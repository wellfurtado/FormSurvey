# -*- coding: utf-8 -*-
"""Texto dos termos de consentimento e assentimento.

Eu transcrevi aqui, LITERALMENTE, o texto dos três termos aprovados pelo CEP
(01_RCLE_Virtual_Adultos.pdf, 02_TCLE_Responsaveis_Menores.pdf e
03_TALE_Estudante_Menor.pdf):
  - RCLE: Registro de Consentimento Livre e Esclarecido (adultos);
  - TCLE: Termo de Consentimento Livre e Esclarecido (responsáveis por menores);
  - TALE: Termo de Assentimento Livre e Esclarecido (estudantes de 14 a 17 anos).

Organizei cada termo em seções (ícone + título + parágrafos) só para mostrá-lo
bem formatado na tela; o TEXTO não foi reescrito nem resumido. Os títulos das
seções são os mesmos dos PDFs originais; o parágrafo de abertura, que não tem
título no original, recebeu o rótulo neutro "Sobre a pesquisa".

O mesmo conteúdo vira a página web (templates/*_consent.html) e o comprovante
em PDF (pdfgen.py, por meio de flatten()). Uma única fonte de verdade.

ponytail: não reproduzo a diagramação do papel (timbre, brasão, linhas de
assinatura). Os blocos de "Declaração do pesquisador" (assinatura em papel)
não aparecem para o participante, porque não se aplicam ao fluxo eletrônico.

ATENÇÃO (ver README, seção "Pendências com o CEP"): o texto aprovado cita o
"LimeSurvey" como plataforma do questionário; o sistema usado é o FormSurvey.
Não alterei essa menção aqui porque mudar o texto aprovado exige comunicação
ao CEP. A única frase fora do texto aprovado é a nota eletrônica do RCLE
(RCLE_ELECTRONIC_NOTE), que descreve como o sistema entrega a cópia.
"""
import config

RESEARCH_TITLE = (
    "Chatbot Institucional com IA na Educação Pública: Um modelo integrado entre "
    "Extended Self, Identidade Digital, TRUST-TAM e Engajamento com Serviços Digitais"
)

IFAP_ADDRESS = "IFAP Campus Santana – Rod. Duca Serra, 1133 - Fonte Nova, Santana - AP, CEP 68925-000"
CEP_ADDRESS = "BR 465, Km 7, Seropédica/RJ – Sala CEP/PROPPG/UFRRJ, Biblioteca Central"
CEP_HOURS = "Tel: (21) 2681-4749 | Segunda a sexta, das 09h às 16h | Presencial: terças e quintas, das 09h às 16h"
CARTILHA_URL = (
    "http://conselho.saude.gov.br/images/comissoes/conep/img/boletins/"
    "Cartilha_Direitos_Participantes_de_Pesquisa_2020.pdf"
)
# O CAAE vem do .env (CAAE=...). Enquanto não estiver configurado, o termo
# mostra um aviso no lugar do número, o que facilita perceber a falta.
CAAE = config.CAAE or "a ser preenchido após aprovação do CEP/UFRRJ"


def section(icon, heading, paragraphs):
    """Monto uma seção do termo: ícone, título e lista de parágrafos."""
    return {"icon": icon, "heading": heading, "paragraphs": paragraphs}


DOUBTS_SECTION = section(
    "📞", "Dúvidas sobre a pesquisa",
    [
        "Pesquisador responsável: Wellington Furtado Damasceno",
        "E-mail: wellington.damasceno@ifap.edu.br | Tel/WhatsApp: (96) 991487335",
        f"Endereço institucional: {IFAP_ADDRESS}",
    ],
)

RIGHTS_SECTION = section(
    "⚖️", "Dúvidas sobre seus direitos como participante de pesquisa",
    [
        f"Comitê de Ética em Pesquisa – CEP/UFRRJ: {CEP_ADDRESS}",
        CEP_HOURS,
        "E-mail: eticacep@ufrrj.br",
        "Para mais informações sobre seus direitos, acesse a Cartilha dos Direitos dos "
        f"Participantes de Pesquisa (CONEP): {CARTILHA_URL}",
    ],
)

# --- RCLE (adulto) ---------------------------------------------------------

RCLE_TITLE = "Registro de Consentimento Livre e Esclarecido"
RCLE_SUBTITLE = "Para pesquisas em ambiente virtual — Resolução CNS nº 510/2016"
RCLE_DECLARATION = (
    "Declaro que li e compreendi as informações acima. Fui esclarecido(a) sobre objetivos, "
    "procedimentos, riscos e benefícios. Sei que posso desistir a qualquer momento sem "
    "prejuízo. Autorizo a utilização dos dados, garantido o sigilo da minha identidade."
)
RCLE_ELECTRONIC_NOTE = (
    'Ao selecionar "Concordo em participar", você registra eletronicamente seu '
    "consentimento, em conformidade com a Resolução CNS nº 510/2016. Recomendamos salvar "
    "ou imprimir este documento para referência futura — por isso, ao final da pesquisa, "
    "você poderá baixar uma cópia em PDF deste termo junto com as suas respostas."
)
RCLE_SECTIONS = [
    section("🎓", "Sobre a pesquisa", [
        f'Você está sendo convidado(a) a participar da pesquisa intitulada "{RESEARCH_TITLE}". '
        "O objetivo é analisar os efeitos do uso de um chatbot baseado em Inteligência "
        "Artificial sobre a percepção de identidade digital institucional, a confiança em "
        "IA, a aceitação tecnológica e o engajamento em serviços digitais entre usuários do "
        "IFAP Campus Santana, e propor diretrizes de design conversacional aplicáveis a "
        "chatbots em instituições públicas de ensino. O pesquisador responsável é Wellington "
        "Furtado Damasceno, mestrando do Programa de Pós-Graduação em Gestão e Estratégia "
        "(PPGE) do Instituto de Ciências Sociais Aplicadas (ICSA) da Universidade Federal "
        "Rural do Rio de Janeiro (UFRRJ), sob orientação da Profa. Dra. Patrícia Leite "
        "(UFRRJ) e coorientação do Prof. Dr. Ricardo Limongi (UFG), e servidor Técnico em "
        "Tecnologia da Informação do IFAP Campus Santana.",
        "Seu nome será mantido em absoluto sigilo, nenhuma informação que permita "
        "identificá-lo(a) será coletada ou divulgada.",
    ]),
    section("🕒", "Como as informações serão obtidas?", [
        "A pesquisa é realizada totalmente online, de forma individual, em uma única sessão "
        "com duas etapas:",
        "1ª etapa – Interação com o chatbot (5 a 10 min): você será direcionado(a) a um dos "
        "protótipos do chatbot institucional do IFAP Campus Santana e realizará uma breve "
        "simulação de atendimento, consulta de informações acadêmicas ou administrativas. O "
        "chatbot é um programa de Inteligência Artificial criado para esta pesquisa, não um "
        "atendente humano.",
        "2ª etapa – Questionário estruturado (10 a 15 min): imediatamente após, você "
        "responderá ao questionário eletrônico pelo LimeSurvey. Você tem o direito de não "
        "responder a qualquer questão sem necessidade de justificativa.",
        "Tempo total estimado: 15 a 25 minutos. Não haverá gravação de áudio, vídeo ou "
        "registro fotográfico.",
    ]),
    section("⚠️", "Quais são os riscos?", [
        "Os riscos são considerados mínimos: leve cansaço ou desconforto ao interagir com o "
        "sistema; riscos inerentes ao ambiente virtual como interrupção nos serviços do "
        "servidor, falhas técnicas ou instabilidade de conexão. Nenhuma informação pessoal "
        "identificável é coletada. O risco de compartilhamento indevido de dados é mitigado "
        "pelo uso do LimeSurvey com protocolos de segurança adequados e armazenamento "
        "restrito ao pesquisador responsável e às orientadoras.",
    ]),
    section("🌱", "Quais são os benefícios?", [
        "Sua participação contribuirá para o desenvolvimento de um chatbot institucional "
        "mais acessível para estudantes do IFAP e de outras instituições públicas de ensino "
        "da Amazônia, subsidiando políticas de digitalização de serviços públicos "
        "educacionais.",
    ]),
    section("🙋", "Participação voluntária e retirada do consentimento", [
        "Sua participação é voluntária. Você pode recusar-se a participar, retirar seu "
        "consentimento ou interromper a participação a qualquer momento, sem qualquer "
        "penalidade acadêmica, funcional ou de outra natureza. Caso desista, solicite a "
        "exclusão dos dados pelo e-mail wellington.damasceno@ifap.edu.br. O pesquisador "
        "excluirá os dados imediatamente.",
    ]),
    section("🔒", "Sigilo e proteção de dados", [
        "Não serão coletados nome, CPF, e-mail ou matrícula. Os dados ficam sob guarda do "
        "pesquisador e das orientadoras, acessados exclusivamente para fins desta pesquisa. "
        "Os resultados serão divulgados de forma agregada. Você poderá ter acesso aos "
        "resultados ao final da pesquisa mediante solicitação.",
    ]),
    section("💰", "Remuneração", [
        "Você não será remunerado(a). Por se tratar de pesquisa online, não há previsão de "
        "gastos com transporte ou alimentação. Caso a pesquisa resulte em dano pessoal, o "
        "ressarcimento previsto em lei poderá ser requerido.",
    ]),
    DOUBTS_SECTION,
    RIGHTS_SECTION,
    section("✅", "Este estudo foi aprovado pelo CEP/UFRRJ", [
        f"Registro CAAE: {CAAE}. O CEP avalia e acompanha os aspectos éticos de pesquisas "
        "com seres humanos, garantindo bem-estar, dignidade, direitos e segurança dos "
        "participantes.",
    ]),
]

# --- TCLE (responsável) -----------------------------------------------------

TCLE_TITLE = "Termo de Consentimento Livre e Esclarecido"
TCLE_SUBTITLE = (
    "Para responsáveis legais de participantes menores de idade — Pesquisa na área de "
    "Ciências Humanas e Sociais | Resoluções CNS nº 466/2012 e nº 510/2016"
)
TCLE_DECLARATION = (
    "Eu, abaixo assinado(a), entendi como é a pesquisa, tirei minhas dúvidas com o "
    "pesquisador e autorizo a participação do(a) menor sob minha responsabilidade, sabendo "
    "que posso retirar essa autorização a qualquer momento. Autorizo a divulgação dos "
    "dados, desde que mantida em sigilo a identidade do(a) menor."
)
TCLE_SECTIONS = [
    section("🎓", "Sobre a pesquisa", [
        "Você está sendo solicitado(a) a autorizar a participação do(a) menor sob sua "
        f'responsabilidade na pesquisa intitulada "{RESEARCH_TITLE}". O objetivo é analisar '
        "os efeitos do uso de um chatbot baseado em Inteligência Artificial sobre a "
        "percepção de identidade digital institucional, a confiança em IA, a aceitação "
        "tecnológica e o engajamento em serviços digitais entre usuários do IFAP Campus "
        "Santana, e propor diretrizes de design conversacional aplicáveis a chatbots em "
        "instituições públicas de ensino. O pesquisador responsável é Wellington Furtado "
        "Damasceno, mestrando do Programa de Pós-Graduação em Gestão e Estratégia (PPGE) do "
        "Instituto de Ciências Sociais Aplicadas (ICSA) da Universidade Federal Rural do Rio "
        "de Janeiro (UFRRJ), sob orientação da Profa. Dra. Patrícia Leite (UFRRJ) e "
        "coorientação do Prof. Dr. Ricardo Limongi (UFG), e é servidor Técnico em "
        "Tecnologia da Informação do IFAP Campus Santana.",
        "O nome do(a) menor não será divulgado, será mantido o mais rigoroso sigilo para "
        "não identificá-lo(a).",
    ]),
    section("🕒", "Como as informações serão obtidas?", [
        "A pesquisa é realizada totalmente online, de forma individual. A participação "
        "do(a) menor está condicionada a DUAS etapas de concordância, em sequência "
        "obrigatória:",
        "Etapa 1 – Sua autorização (este documento): você lê, esclarece suas dúvidas e "
        "autoriza eletronicamente. Somente após sua autorização o(a) menor receberá o "
        "próximo documento.",
        "Etapa 2 – Assentimento do(a) menor (TALE): o(a) menor receberá um Termo de "
        "Assentimento em linguagem acessível e decidirá, de forma independente, se quer ou "
        "não participar. Mesmo com sua autorização, a participação não ocorrerá se o(a) "
        "menor não concordar.",
        "Se ambos concordarem, a pesquisa ocorre em duas etapas:",
        "1ª etapa – Interação com o chatbot (5 a 10 min): o(a) menor acessará um dos "
        "protótipos do chatbot institucional do IFAP Campus Santana e realizará uma breve "
        "simulação de atendimento — consulta de informações acadêmicas ou administrativas. "
        "O chatbot é um programa de Inteligência Artificial experimental, não um atendente "
        "humano real.",
        "2ª etapa – Questionário estruturado (10 a 15 min): imediatamente após, o(a) menor "
        "responderá ao questionário eletrônico pelo LimeSurvey. O(a) menor tem o direito de "
        "não responder a qualquer questão sem necessidade de justificativa.",
        "Tempo total estimado: 15 a 25 minutos. Não haverá gravação de áudio, vídeo ou "
        "registro fotográfico.",
    ]),
    section("⚠️", "Quais são os riscos?", [
        "Os riscos são considerados mínimos: leve cansaço ou desconforto ao interagir com o "
        "sistema; riscos inerentes ao ambiente virtual como interrupção nos serviços do "
        "servidor, falhas técnicas ou instabilidade de conexão. Nenhuma informação pessoal "
        "identificável do(a) menor é coletada. O risco de compartilhamento indevido de "
        "dados é mitigado pelo uso do LimeSurvey com protocolos de segurança adequados.",
    ]),
    section("🌱", "Quais são os benefícios?", [
        "A participação contribuirá para o desenvolvimento de um chatbot mais acessível "
        "para estudantes do IFAP e de outras instituições públicas de ensino da Amazônia, "
        "beneficiando indiretamente toda a comunidade acadêmica.",
    ]),
    section("🙋", "Autorização voluntária e retirada do consentimento", [
        "Você é livre para recusar a autorização, retirar seu consentimento ou interromper "
        "a participação do(a) menor a qualquer momento. A recusa não acarretará penalidade "
        "alguma, acadêmica ou de outra natureza, para o(a) menor ou para você. Caso "
        "desista, solicite a exclusão dos dados pelo e-mail wellington.damasceno@ifap.edu.br. "
        "O pesquisador excluirá os dados imediatamente.",
    ]),
    section("🔒", "Sigilo e proteção de dados", [
        "Não serão coletados nome, CPF, e-mail ou matrícula do(a) menor. Os dados ficam sob "
        "guarda do pesquisador e das orientadoras. Os resultados serão divulgados de forma "
        "agregada. Você e o(a) menor poderão ter acesso aos resultados ao final da pesquisa "
        "mediante solicitação.",
    ]),
    section("💰", "Remuneração", [
        "Você e o(a) menor não serão remunerados(as). Por se tratar de pesquisa online, não "
        "há gastos com transporte ou alimentação. Caso a pesquisa resulte em dano pessoal, o "
        "ressarcimento previsto em lei poderá ser requerido.",
    ]),
    DOUBTS_SECTION,
    RIGHTS_SECTION,
    section("✅", "Este estudo foi aprovado pelo CEP/UFRRJ", [
        f"Registro CAAE: {CAAE}. O CEP avalia e acompanha os aspectos éticos de pesquisas "
        "com seres humanos.",
    ]),
]

# --- TALE (menor) ------------------------------------------------------------

TALE_TITLE = "Termo de Assentimento Livre e Esclarecido"
TALE_SUBTITLE = "Convite especial para você! — Para estudantes menores de 18 anos | Resolução CNS nº 510/2016"
TALE_DECLARATION = (
    "Entendi as informações desta pesquisa. Sei que posso desistir a qualquer momento sem "
    "nenhum problema. Concordo em participar e autorizo que os dados sejam usados na "
    "pesquisa, mantendo minha identidade em sigilo. O pesquisador tirou todas as minhas "
    "dúvidas."
)
TALE_SECTIONS = [
    section("👋", "Olá! Temos um convite para você.", [
        "Estamos fazendo uma pesquisa sobre um chatbot, um robozinho de computador, criado "
        "para ajudar os estudantes do IFAP a encontrar informações mais facilmente. A "
        f'pesquisa se chama "{RESEARCH_TITLE}".',
        "Seus pais ou responsáveis já autorizaram sua participação. Mas a decisão final é "
        "SUA! Você pode dizer sim ou não, sem nenhum problema.",
    ]),
    section("💡", "Por que esta pesquisa é importante?", [
        "Queremos entender o que os estudantes do IFAP pensam sobre o chatbot para deixá-lo "
        "mais útil e mais fácil de usar. Você vai ajudar a melhorar um serviço digital para "
        "todos os estudantes da escola!",
    ]),
    section("🙋", "Quem pode participar?", [
        "Estudantes do IFAP Campus Santana, incluindo você!",
    ]),
    section("🤖", "Como vai funcionar?", [
        "Passo 1 — Conversar com o chatbot (5 a 10 minutos): Você vai acessar um link e "
        "conversar com o chatbot do IFAP. É como mandar mensagem para um robô que responde "
        'perguntas, por exemplo: "Qual é o calendário acadêmico?" O chatbot é um programa de '
        "computador feito para esta pesquisa, não é um atendente humano real.",
        "Passo 2 — Responder um formulário rápido (10 a 15 minutos): Depois, você responde "
        "algumas perguntas sobre o que achou da experiência. Não tem resposta certa ou "
        "errada, queremos saber o que você realmente pensa. Você não precisa responder "
        "nenhuma pergunta que não quiser.",
        "Tempo total: entre 15 e 25 minutos, pelo celular ou computador, quando você "
        "quiser.",
    ]),
    section("⚠️", "O que pode acontecer de ruim? (Riscos)", [
        "Os riscos são bem pequenos:",
        "• Você pode ficar um pouquinho cansado(a) ou ter alguma dúvida enquanto usa o "
        "chatbot.",
        "• A internet pode cair ou dar algum problema técnico durante a pesquisa.",
        "Se isso acontecer, é só fechar o navegador. Nenhuma informação pessoal sua vai "
        "estar em risco.",
    ]),
    section("🌟", "O que tem de bom para você? (Benefícios)", [
        "Você vai ajudar a melhorar os serviços digitais do IFAP para você e para todos os "
        "estudantes. Além disso, vai ter uma experiência real com tecnologia de "
        "Inteligência Artificial, a mesma usada em assistentes como ChatGPT!",
    ]),
    section("🔒", "Suas informações ficam em segredo", [
        "Seu nome não vai aparecer em lugar nenhum. A pesquisa não coleta CPF, e-mail ou "
        "matrícula. Só o pesquisador e as orientadoras têm acesso às respostas.",
    ]),
    section("🚪", "Você pode sair quando quiser", [
        "A participação é voluntária e gratuita. Se mudar de ideia, é só fechar o "
        "navegador. Nada vai mudar na sua vida escolar.",
    ]),
    section("📞", "Ficou com dúvida? Fale com a gente!", [
        "Pesquisador: Wellington Furtado Damasceno",
        "E-mail: wellington.damasceno@ifap.edu.br | WhatsApp/Tel: (96) 991487335",
        "Se tiver dúvidas sobre seus direitos, fale com o Comitê de Ética em Pesquisa da "
        "UFRRJ: CEP/UFRRJ | Tel: (21) 2681-4749 | E-mail: eticacep@ufrrj.br",
        f"{CEP_ADDRESS}",
        "Atendimento: segunda a sexta, das 09h às 16h | Presencial: terças e quintas, das "
        "09h às 16h",
    ]),
]


def flatten(title, subtitle, sections):
    """Junto título, subtítulo e seções em texto corrido, para o PDF (pdfgen.py)."""
    lines = [title, subtitle, ""]
    for s in sections:
        lines.append(s["heading"].upper())
        lines.extend(s["paragraphs"])
        lines.append("")
    return "\n".join(lines)
