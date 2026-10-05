# -*- coding: utf-8 -*-
"""FormSurvey — aplicação web (Flask).

Este é o arquivo principal. Nele eu defino todas as páginas (rotas) do
sistema, na ordem em que o participante passa por elas:

    1. Página inicial ............................. "/"
    2. Termo + decisão
         - adulto (RCLE) .......................... "/adulto"
         - responsável (TCLE) ..................... "/responsavel"
         - menor (TALE), com código de acesso ..... "/menor" e "/menor/acesso/<código>"
    3. Sorteio da condição experimental (C1-C4) ... feito ao concordar
    4. Chatbot (ida e volta registradas) .......... "/pesquisa/<token>/chatbot"
    5. Questionário ............................... "/pesquisa/<token>/questionario"
    6. Conclusão + comprovante em PDF ............. "/pesquisa/<token>/concluido"

E, para o pesquisador:

    7. Painel administrativo ...................... "/admin"
    8. Exportação das respostas (CSV) ............. "/admin/exportar/respostas.csv"

O README.md tem os diagramas de cada fluxo e explica o porquê de cada decisão.
"""
import csv
import io
import os
import random
import secrets
import sys
import uuid
from datetime import date, datetime, timezone
from functools import wraps
from urllib.parse import urlencode

from flask import Flask, Response, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

import config
import db
import pdfgen
import questions
import stats
import terms

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.teardown_appcontext(db.close_db)

# Configuro o cookie de sessão (usado no login do painel e para lembrar, entre
# uma página e outra, que a pessoa já concordou com o termo):
#   - SameSite=Lax: o navegador não envia o cookie em formulários vindos de
#     outros sites, o que protege contra CSRF sem precisar de token por
#     formulário;
#   - HttpOnly: o JavaScript da página não consegue ler o cookie;
#   - Secure: o cookie só trafega em HTTPS. Só ligo com FORCE_HTTPS=1, senão
#     o sistema deixaria de funcionar na rede local, sem certificado.
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=config.FORCE_HTTPS,
)

if config.FORCE_HTTPS:
    # Quando o Nginx faz o HTTPS e repassa a requisição para cá em HTTP, eu
    # preciso confiar nos cabeçalhos X-Forwarded-* que ele envia. Sem isso, os
    # links completos que gero (link do menor, link de retomada) sairiam com
    # http:// em vez de https://.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


# --- comandos de linha de comando ------------------------------------------

@app.cli.command("init-db")
def init_db_command():
    """flask --app app init-db  ->  cria as tabelas do banco."""
    db.init_db()
    print("Banco de dados inicializado em " + config.DATABASE_PATH)


@app.cli.command("codebook")
def codebook_command():
    """flask --app app codebook > dados/codebook.csv  ->  gera o dicionário de variáveis.

    Gero o codebook a partir do próprio código (questions.py e config.py) para
    que ele nunca fique diferente do que o sistema realmente exporta.
    """
    # Forço UTF-8: no Windows a saída padrão usa outra codificação e os
    # acentos sairiam errados no arquivo.
    sys.stdout.reconfigure(encoding="utf-8")
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(["variavel", "descricao", "tipo", "valores"])
    for name, description, kind, values in export_columns_dictionary():
        writer.writerow([name, description, kind, values])


# --- etapas mostradas no topo das páginas (stepper) ---------------------------

# Adulto e menor seguem o mesmo caminho depois do termo. O responsável tem um
# caminho próprio: ele não responde à pesquisa por este termo, só autoriza.
STEPS = ["Termo", "Chatbot", "Questionário", "Concluído"]
GUARDIAN_STEPS = ["Termo", "Seus dados", "Link do(a) menor"]


# --- funções auxiliares ------------------------------------------------------

def now_iso():
    """Horário atual em UTC, formato ISO 8601. Uso UTC para que os cálculos
    de duração não sejam afetados por fuso horário ou horário de verão."""
    return datetime.now(timezone.utc).isoformat()


def today():
    """Só a data de hoje (AAAA-MM-DD). É o que guardo nos registros de
    consentimento, para que eles não possam ser casados com os participantes
    pelo horário exato (ver comentário no topo do schema.sql)."""
    return date.today().isoformat()


def fmt_ts(iso_value):
    """Converto um horário ISO (UTC) para o formato brasileiro, no fuso do
    servidor, para mostrar no PDF."""
    return datetime.fromisoformat(iso_value).astimezone().strftime("%d/%m/%Y %H:%M")


def fmt_date(iso_date):
    """AAAA-MM-DD -> DD/MM/AAAA."""
    return date.fromisoformat(iso_date).strftime("%d/%m/%Y")


def assign_condition():
    """Sorteio a condição experimental do novo participante, de forma balanceada.

    Como funciona: conto quantos participantes já foram designados para cada
    condição e escolho, entre as condições com MENOS participantes, uma ao
    acaso. Isso mantém os quatro grupos com tamanhos quase iguais ao longo de
    toda a coleta (a diferença entre o maior e o menor grupo nunca passa de 1
    em condições normais), o que é importante para a ANOVA 2x2, cuja meta na
    dissertação é de 40 a 50 participantes por célula.

    Por que não um sorteio simples (random.choice entre as quatro)? Porque com
    amostras pequenas o sorteio simples pode gerar grupos bem desiguais (por
    exemplo, 60/45/52/43 com 200 pessoas). O balanceamento evita isso, e o
    desempate aleatório evita que a ordem de chegada determine o grupo.

    Conto TODOS os designados, inclusive quem não terminou. Assim, quem está
    respondendo agora já conta para o grupo dele, e duas pessoas que chegam
    ao mesmo tempo tendem a ir para grupos diferentes.

    Uso random.SystemRandom, que tira a aleatoriedade do sistema operacional,
    em vez do gerador padrão do Python, que é previsível se a semente for
    conhecida.
    """
    counts = {name: 0 for name in config.CONDITIONS}
    for row in db.query_all("SELECT condition, COUNT(*) AS n FROM participants GROUP BY condition"):
        if row["condition"] in counts:
            counts[row["condition"]] = row["n"]
    smallest = min(counts.values())
    candidates = [name for name, n in counts.items() if n == smallest]
    return random.SystemRandom().choice(candidates)


def new_participant(kind):
    """Crio o participante anônimo e já sorteio a condição dele.

    O token é um UUID v4: 122 bits aleatórios, impossível de adivinhar. Ele vai
    na URL de cada etapa e funciona como "link de retomada": se a internet
    cair, a pessoa abre o mesmo link e continua de onde parou, mesmo em outro
    aparelho. Repare que eu NÃO guardo aqui nenhuma referência ao registro de
    consentimento: essa é a separação que garante o anonimato das respostas.
    """
    token = str(uuid.uuid4())
    db.execute(
        "INSERT INTO participants (token, kind, condition, created_at) VALUES (?, ?, ?, ?)",
        (token, kind, assign_condition(), now_iso()),
    )
    return token


def generate_unique_code():
    """Gero o código de acesso do(a) menor (UUID v4 em hexadecimal, 32
    caracteres). A chance de repetir é desprezível, mas confiro mesmo assim."""
    while True:
        code = uuid.uuid4().hex
        if not db.query_one("SELECT 1 FROM access_codes WHERE code = ?", (code,)):
            return code


def get_participant_or_404(token):
    """Busco o participante pelo token da URL; token inexistente = página 404."""
    participant = db.query_one("SELECT * FROM participants WHERE token = ?", (token,))
    if not participant:
        abort(404)
    return participant


def safe_next(target):
    """Só aceito redirecionar, depois do login, para um caminho DENTRO deste site.

    Sem esta checagem, um link como /admin/login?next=https://site-falso.com
    levaria o pesquisador, logo após digitar a senha, para um site de terceiros
    (o chamado "open redirect"). Caminhos que começam com "//" ou "/\\" também
    são recusados porque os navegadores os interpretam como outro domínio.
    """
    if target and target.startswith("/") and not target.startswith(("//", "/\\")):
        return target
    return url_for("admin_dashboard")


def admin_required(view):
    """Decorador: a página só abre se o pesquisador tiver feito login."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


# =============================================================================
# ETAPA 1 — Página inicial
# =============================================================================

@app.route("/")
def index():
    """Página de entrada: a pessoa escolhe o caminho que corresponde a ela."""
    return render_template("index.html")


@app.route("/nao-participacao")
def declined():
    """Página mostrada a quem recusou. Nenhum dado pessoal foi pedido."""
    return render_template("declined.html")


# =============================================================================
# ETAPA 2a — Adulto (RCLE): lê o termo, declara ter 18 anos ou mais e decide
# =============================================================================

@app.route("/adulto", methods=["GET", "POST"])
def adult_consent():
    """Mostro o RCLE inteiro e os botões de decisão.

    Se a pessoa RECUSA, gravo só "agreed = 0" e a data, e a levo para a página
    de agradecimento. Se CONCORDA, exijo também a declaração de maioridade
    (um menor não pode entrar pelo caminho de adulto, porque precisa da
    autorização do responsável); então gravo o consentimento, crio o
    participante anônimo (com a condição sorteada) e sigo para o chatbot.

    Não peço nenhum dado pessoal: o RCLE aprovado promete que "não serão
    coletados nome, CPF, e-mail ou matrícula".
    """
    if request.method == "POST":
        if request.form.get("decision") != "agree":
            db.execute("INSERT INTO adults (agreed, created_on) VALUES (0, ?)", (today(),))
            return redirect(url_for("declined"))

        if request.form.get("adult_declared") != "yes":
            flash("Para participar por este caminho, confirme que você tem 18 anos ou mais. "
                  "Se você é menor de idade, peça ao seu responsável para autorizar a sua participação.")
            return redirect(url_for("adult_consent"))

        db.execute("INSERT INTO adults (agreed, created_on) VALUES (1, ?)", (today(),))
        token = new_participant("adult")
        return redirect(url_for("chatbot_step", token=token))

    return render_template(
        "adult_consent.html", title=terms.RCLE_TITLE, subtitle=terms.RCLE_SUBTITLE,
        sections=terms.RCLE_SECTIONS, declaration=terms.RCLE_DECLARATION,
        note=terms.RCLE_ELECTRONIC_NOTE, step=1, steps=STEPS,
    )


# =============================================================================
# ETAPA 2b — Responsável (TCLE): página 1 = termo + decisão; página 2 = dados
# =============================================================================

@app.route("/responsavel", methods=["GET", "POST"])
def guardian_consent():
    """Mostro o TCLE e os botões de decisão.

    Separei termo e dados em duas páginas para que a decisão venha ANTES de
    qualquer dado ser pedido: quem recusa não informa nada. Quem autoriza
    segue para a página 2; guardo na sessão (cookie) só a informação de que
    concordou, para que ninguém pule direto para a página 2.
    """
    if request.method == "POST":
        if request.form.get("decision") == "agree":
            session["guardian_agreed"] = True
            return redirect(url_for("guardian_details"))
        db.execute(
            "INSERT INTO guardians (guardian_name, relationship, agreed, created_on) "
            "VALUES (NULL, NULL, 0, ?)",
            (today(),),
        )
        return redirect(url_for("declined"))
    return render_template(
        "guardian_consent.html", title=terms.TCLE_TITLE, subtitle=terms.TCLE_SUBTITLE,
        sections=terms.TCLE_SECTIONS, declaration=terms.TCLE_DECLARATION,
        step=1, steps=GUARDIAN_STEPS,
    )


@app.route("/responsavel/detalhes", methods=["GET", "POST"])
def guardian_details():
    """Peço o nome do responsável e o vínculo com o(a) menor (a "assinatura"
    do TCLE), gravo a autorização e gero o código de uso único do(a) menor.

    O nome do(a) menor NÃO é pedido: o TCLE promete que "não serão coletados
    nome, CPF, e-mail ou matrícula do(a) menor". O código de acesso é o que
    identifica, no comprovante do responsável, qual autorização é essa.
    """
    if not session.get("guardian_agreed"):
        return redirect(url_for("guardian_consent"))

    if request.method == "POST":
        guardian_name = request.form.get("guardian_name", "").strip()
        relationship = request.form.get("relationship", "").strip()

        if not guardian_name or not relationship:
            flash("Preencha seu nome e o grau de parentesco / vínculo com o(a) menor.")
            return render_template("guardian_details.html", form=request.form, step=2, steps=GUARDIAN_STEPS)

        cur = db.execute(
            "INSERT INTO guardians (guardian_name, relationship, agreed, created_on) VALUES (?, ?, 1, ?)",
            (guardian_name, relationship, today()),
        )
        code = generate_unique_code()
        db.execute(
            "INSERT INTO access_codes (code, guardian_id, created_on) VALUES (?, ?, ?)",
            (code, cur.lastrowid, today()),
        )

        session.pop("guardian_agreed", None)
        # Guardo o código na sessão para mostrar a próxima página e permitir o
        # download do comprovante, sem colocar o código em nenhuma URL pública.
        session["guardian_code"] = code
        return redirect(url_for("guardian_code_page"))

    return render_template("guardian_details.html", form={}, step=2, steps=GUARDIAN_STEPS)


@app.route("/responsavel/codigo")
def guardian_code_page():
    """Mostro o link (e o código) que o responsável deve repassar ao(à) menor,
    o botão para baixar o comprovante do TCLE e o convite para o próprio
    responsável participar também — pelo caminho de adulto, com o RCLE, que é
    o termo adequado para quem responde por si mesmo."""
    code = session.get("guardian_code")
    if not code:
        abort(404)
    return render_template(
        "guardian_code.html",
        code=code,
        access_link=url_for("minor_access_link", code=code, _external=True),
        step=3, steps=GUARDIAN_STEPS,
    )


@app.route("/responsavel/comprovante.pdf")
def guardian_pdf():
    """Gero na hora o PDF do TCLE com os dados da autorização.

    O PDF não fica salvo em lugar nenhum: é montado a partir do banco e
    entregue ao navegador. Só quem tem a sessão da autorização (o próprio
    responsável, logo após autorizar) consegue baixá-lo.
    """
    code = session.get("guardian_code")
    if not code:
        abort(404)
    row = db.query_one(
        "SELECT g.guardian_name, g.relationship, g.created_on FROM access_codes a "
        "JOIN guardians g ON g.id = a.guardian_id WHERE a.code = ?",
        (code,),
    )
    pdf_bytes = pdfgen.guardian_pdf(row["guardian_name"], row["relationship"], code, fmt_date(row["created_on"]))
    return _pdf_response(pdf_bytes, "termo_consentimento_responsavel.pdf")


# =============================================================================
# ETAPA 2c — Menor (TALE): entra com o código, lê o termo e decide
# =============================================================================

def _activate_code(code):
    """Confiro se o código existe e ainda não foi usado; se sim, guardo-o na
    sessão como "código pendente" até o(a) menor decidir."""
    row = db.query_one("SELECT * FROM access_codes WHERE code = ?", (code,))
    if not row or row["used"]:
        return False
    session["pending_code"] = code
    return True


@app.route("/menor", methods=["GET", "POST"])
def minor_code_entry():
    """Página onde o(a) menor digita o código (alternativa ao link direto)."""
    if request.method == "POST":
        code = request.form.get("code", "").strip().lower()
        row = db.query_one("SELECT * FROM access_codes WHERE code = ?", (code,))
        if not row:
            flash("Código não encontrado. Confira com o(a) responsável e tente novamente.")
            return render_template("minor_code_entry.html")
        if row["used"]:
            flash("Este código já foi utilizado. Cada código só pode ser usado uma vez.")
            return render_template("minor_code_entry.html")
        session["pending_code"] = code
        return redirect(url_for("minor_consent"))
    return render_template("minor_code_entry.html")


@app.route("/menor/acesso/<code>")
def minor_access_link(code):
    """Link direto que o responsável repassa: já ativa o código e abre o TALE."""
    if not _activate_code(code.strip().lower()):
        flash("Link inválido ou já utilizado. Peça um novo código ao(à) responsável.")
        return redirect(url_for("minor_code_entry"))
    return redirect(url_for("minor_consent"))


@app.route("/menor/assentimento", methods=["GET", "POST"])
def minor_consent():
    """Mostro o TALE (linguagem acessível) e os botões SIM / NÃO.

    Em qualquer das duas decisões o código é CONSUMIDO (used = 1): ele não
    pode ser reaproveitado, nem para mudar a decisão, nem por outra pessoa.
    Se o(a) menor diz SIM, crio o participante anônimo e sigo para o chatbot.
    """
    code = session.get("pending_code")
    row = db.query_one("SELECT * FROM access_codes WHERE code = ?", (code,)) if code else None
    if not row or row["used"]:
        session.pop("pending_code", None)
        return redirect(url_for("minor_code_entry"))

    if request.method == "POST":
        agreed = request.form.get("decision") == "agree"
        db.execute(
            "UPDATE access_codes SET used = 1, minor_agreed = ?, used_on = ? WHERE code = ?",
            (int(agreed), today(), code),
        )
        session.pop("pending_code", None)
        if not agreed:
            return redirect(url_for("declined"))
        token = new_participant("minor")
        return redirect(url_for("chatbot_step", token=token))

    return render_template(
        "minor_consent.html", title=terms.TALE_TITLE, subtitle=terms.TALE_SUBTITLE,
        sections=terms.TALE_SECTIONS, declaration=terms.TALE_DECLARATION,
        step=1, steps=STEPS,
    )


# =============================================================================
# ETAPA 4 — Chatbot (ida e volta registradas)
# =============================================================================
# A partir daqui o token vai na URL. É ele que permite retomar a pesquisa
# depois de uma queda de conexão, mesmo sem o cookie de sessão.

def _redirect_if_completed(participant):
    """Quem já concluiu não volta ao chatbot nem ao questionário: vai direto
    para a página de conclusão (onde pode baixar o comprovante de novo)."""
    if participant["completed_at"]:
        return redirect(url_for("completed", token=participant["token"]))
    return None


@app.route("/pesquisa/<token>/chatbot")
def chatbot_step(token):
    """Página com o botão "Abrir o chatbot" e o link de retomada."""
    participant = get_participant_or_404(token)
    done = _redirect_if_completed(participant)
    if done:
        return done
    return render_template(
        "chatbot.html", token=token,
        chatbot_opened=bool(participant["chatbot_opened_at"]),
        resume_link=url_for("chatbot_step", token=token, _external=True),
        step=2, steps=STEPS,
    )


@app.route("/pesquisa/<token>/chatbot/abrir")
def open_chatbot(token):
    """Registro que o participante abriu o chatbot e o envio para a versão do
    chatbot da condição sorteada para ele.

    O botão da página aponta para esta rota, e não direto para o chatbot, por
    dois motivos:
      1. o participante nunca vê a lista de endereços das quatro condições;
         ele só recebe o da sua;
      2. eu registro o horário da primeira abertura (chatbot_opened_at), que é
         a prova de que houve exposição ao estímulo e o início da contagem de
         tempo de interação.

    Repasso o token ao chatbot (parâmetro ?token=...) para que, se o chatbot
    gravar as conversas, elas possam ser associadas a este participante
    anônimo — e, portanto, à condição dele — sem nenhum dado pessoal.
    """
    participant = get_participant_or_404(token)
    done = _redirect_if_completed(participant)
    if done:
        return done
    if not participant["chatbot_opened_at"]:
        db.execute("UPDATE participants SET chatbot_opened_at = ? WHERE token = ?", (now_iso(), token))

    url = config.CONDITIONS[participant["condition"]]["url"]
    separator = "&" if "?" in url else "?"
    return redirect(f"{url}{separator}{urlencode({'token': token})}")


# =============================================================================
# ETAPA 5 — Questionário
# =============================================================================

@app.route("/pesquisa/<token>/questionario", methods=["GET", "POST"])
def questionnaire(token):
    """Mostro e recebo o questionário (Anexo I da dissertação).

    Só libero o questionário depois que o chatbot foi aberto: responder sobre
    um chatbot que não se viu tornaria a resposta inválida para o experimento.

    Nenhuma pergunta é obrigatória (exigência ética: "você tem o direito de não
    responder a qualquer questão"). Itens em branco simplesmente não geram
    linha na tabela responses, e o CSV informa quantos ficaram em branco.
    """
    participant = get_participant_or_404(token)
    done = _redirect_if_completed(participant)
    if done:
        return done

    if not participant["chatbot_opened_at"]:
        flash("Antes do questionário, abra o chatbot e converse com ele por alguns minutos.")
        return redirect(url_for("chatbot_step", token=token))

    if request.method == "POST":
        for code in questions.all_question_codes():
            value = request.form.get(code, "").strip()
            # Só aceito valores que existem no instrumento. Isso impede que
            # alguém grave texto arbitrário editando o formulário no navegador.
            if value and questions.is_valid_answer(code, value):
                db.execute(
                    "INSERT OR REPLACE INTO responses (participant_id, question_code, value) VALUES (?, ?, ?)",
                    (participant["id"], code, value),
                )
        db.execute("UPDATE participants SET completed_at = ? WHERE token = ?", (now_iso(), token))
        return redirect(url_for("completed", token=token))

    # Registro só a PRIMEIRA vez que o questionário foi aberto: se a pessoa
    # recarregar a página, o início não muda.
    if not participant["questionnaire_started_at"]:
        db.execute("UPDATE participants SET questionnaire_started_at = ? WHERE token = ?", (now_iso(), token))

    return render_template(
        "questionnaire.html",
        blocks=questions.LIKERT_BLOCKS,
        profile=questions.PROFILE_BLOCK,
        likert_scale=questions.LIKERT_SCALE,
        step=3, steps=STEPS,
    )


# =============================================================================
# ETAPA 6 — Conclusão e comprovante em PDF
# =============================================================================

def _participant_answers(participant):
    """Respostas do participante, na ordem do questionário, como (código, valor)."""
    stored = {
        r["question_code"]: r["value"]
        for r in db.query_all(
            "SELECT question_code, value FROM responses WHERE participant_id = ?", (participant["id"],)
        )
    }
    return [(code, stored[code]) for code in questions.all_question_codes() if code in stored]


def _pdf_response(pdf_bytes, filename):
    """Entrego o PDF como download (Content-Disposition: attachment)."""
    resp = Response(pdf_bytes, mimetype="application/pdf")
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


@app.route("/pesquisa/<token>/concluido")
def completed(token):
    """Página final: agradecimento e botão para baixar o comprovante."""
    participant = get_participant_or_404(token)
    if not participant["completed_at"]:
        return redirect(url_for("chatbot_step", token=token))
    return render_template("thanks.html", token=token, step=4, steps=STEPS)


@app.route("/pesquisa/<token>/comprovante.pdf")
def participant_pdf(token):
    """Gero na hora o PDF com o termo aceito (RCLE ou TALE), a data/hora do
    aceite e as respostas dadas.

    Antes o comprovante ia por e-mail, o que exigia guardar o e-mail e ligá-lo
    às respostas — contrariando o termo aprovado. Agora o participante baixa o
    arquivo no próprio navegador, e nada disso precisa ser guardado.
    """
    participant = get_participant_or_404(token)
    if not participant["completed_at"]:
        abort(404)
    answers = _participant_answers(participant)
    consent_at = fmt_ts(participant["created_at"])
    if participant["kind"] == "adult":
        pdf_bytes = pdfgen.adult_pdf(consent_at, answers)
        filename = "registro_consentimento_e_respostas.pdf"
    else:
        pdf_bytes = pdfgen.minor_pdf(consent_at, answers)
        filename = "termo_assentimento_e_respostas.pdf"
    return _pdf_response(pdf_bytes, filename)


# =============================================================================
# ETAPA 8 — Exportação para estatística (SPSS / R)
# =============================================================================

def _seconds_between(start, end):
    """Duração em segundos entre dois horários ISO; vazio se faltar algum."""
    if not start or not end:
        return ""
    return round((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())


def export_columns_dictionary():
    """Descrição de cada coluna do CSV, na mesma ordem do CSV.

    É a fonte do codebook (comando "flask --app app codebook") e da tabela de
    variáveis do README. Mantenho tudo aqui, ao lado do código que gera o CSV,
    para que a documentação não se desatualize.
    """
    condition_values = "; ".join(
        f"{name} = " + ", ".join(f"{f}={c[f]}" for f in config.FACTORS)
        for name, c in config.CONDITIONS.items()
    )
    columns = [
        ("participante", "Número sequencial do participante (não identifica a pessoa)", "inteiro", ""),
        ("perfil", "Caminho de consentimento", "texto", "adulto = RCLE; menor = TCLE + TALE"),
        ("condicao", "Condição experimental sorteada", "texto", condition_values),
    ]
    factor_labels = {"hum": "Humanização", "per": "Personalização institucional"}
    for factor in config.FACTORS:
        columns.append((factor, f"Fator {factor_labels.get(factor, factor)} da condição", "0/1", "0 = baixa; 1 = alta"))
    columns += [
        ("inicio", "Aceite do termo (UTC, ISO 8601)", "data-hora", ""),
        ("chatbot_aberto", "Primeira abertura do chatbot (UTC)", "data-hora", ""),
        ("questionario_aberto", "Primeira abertura do questionário (UTC)", "data-hora", ""),
        ("concluido", "Envio do questionário (UTC)", "data-hora", ""),
        ("seg_chatbot", "Segundos entre abrir o chatbot e abrir o questionário (tempo aproximado de interação)", "inteiro", ""),
        ("seg_questionario", "Segundos entre abrir e enviar o questionário", "inteiro", ""),
        ("seg_total", "Segundos entre o aceite do termo e o envio do questionário", "inteiro", ""),
        ("itens_em_branco", f"Quantidade de itens não respondidos (de {len(questions.all_question_codes())})", "inteiro", ""),
    ]
    for code in questions.all_question_codes():
        if questions.is_likert_code(code):
            construct = questions.CONSTRUCT_LABELS.get(code.rstrip("0123456789"), "")
            scale = "; ".join(f"{v} = {label}" for v, label in questions.LIKERT_SCALE)
            columns.append((code, f"[{construct}] {questions.question_text(code)}", "Likert 1-5", scale + "; vazio = não respondeu"))
        else:
            options = "; ".join(questions.profile_options(code))
            columns.append((code, questions.question_text(code), "categórica", options + "; vazio = prefiro não responder"))
    return columns


@app.route("/admin/exportar/respostas.csv")
@admin_required
def export_csv():
    """Gero o CSV com uma linha por participante que concluiu o questionário.

    Este arquivo é a base da análise estatística (ANOVA 2x2 no SPSS e PLS-SEM
    no R). Ele não contém nenhum dado identificável: nem nome, nem e-mail, nem
    o token (que é substituído pelo número sequencial do participante).

    Antes a exportação era protegida por um token na própria URL, que ficava
    gravado no histórico do navegador e nos logs do servidor. Agora ela exige
    o login do painel, como qualquer outra página administrativa.
    """
    codes = questions.all_question_codes()
    header = [name for name, *_ in export_columns_dictionary()]
    kind_label = {"adult": "adulto", "minor": "menor"}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(header)
    for p in db.query_all("SELECT * FROM participants WHERE completed_at IS NOT NULL ORDER BY id"):
        answers = dict(_participant_answers(p))
        condition = config.CONDITIONS.get(p["condition"], {})
        writer.writerow([
            p["id"],
            kind_label[p["kind"]],
            p["condition"],
            *[condition.get(f, "") for f in config.FACTORS],
            p["created_at"],
            p["chatbot_opened_at"] or "",
            p["questionnaire_started_at"] or "",
            p["completed_at"],
            _seconds_between(p["chatbot_opened_at"], p["questionnaire_started_at"]),
            _seconds_between(p["questionnaire_started_at"], p["completed_at"]),
            _seconds_between(p["created_at"], p["completed_at"]),
            sum(1 for c in codes if c not in answers),
            *[answers.get(c, "") for c in codes],
        ])

    # O BOM (﻿) no início faz o Excel abrir o arquivo com os acentos
    # certos; SPSS e R o ignoram.
    resp = Response("﻿" + output.getvalue(), mimetype="text/csv; charset=utf-8")
    resp.headers["Content-Disposition"] = "attachment; filename=respostas_pesquisa.csv"
    return resp


# =============================================================================
# ETAPA 7 — Painel administrativo
# =============================================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Login do pesquisador com uma senha única definida no .env.

    Comparo a senha com secrets.compare_digest, que leva o mesmo tempo para
    qualquer senha errada; uma comparação comum (==) termina mais cedo quando
    o primeiro caractere já difere, o que permitiria adivinhar a senha
    medindo o tempo de resposta.
    """
    if request.method == "POST":
        password = request.form.get("password", "")
        if config.ADMIN_PASSWORD and secrets.compare_digest(password, config.ADMIN_PASSWORD):
            session["is_admin"] = True
            return redirect(safe_next(request.args.get("next")))
        flash("Senha incorreta.")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    """Painel com números agregados (nenhum dado individual)."""
    return render_template("admin_dashboard.html", stats=stats.compute())


if __name__ == "__main__":
    # Modo de desenvolvimento: "python app.py". Em produção quem roda o
    # sistema é o Gunicorn (ver formsurvey.service), nunca este bloco.
    with app.app_context():
        db.init_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True, use_reloader=False)
