# -*- coding: utf-8 -*-
"""Instrumento de coleta de dados (Anexo I da dissertação).

Eu escrevi o questionário como DADOS, e não direto no HTML. Assim uma única
definição alimenta tudo: a página do questionário, a validação das respostas,
o PDF do comprovante, o CSV exportado, o codebook e as médias do painel. Para
mudar um item, mudo só aqui.

Cada item tem um CÓDIGO curto (HUM1, PER2, IDI3...). O prefixo em letras é o
construto e o número é a ordem do item dentro dele. Esses códigos viram os
nomes das colunas no CSV, prontos para o SPSS e o R.

Os textos dos itens são os do Quadro 6 da dissertação (escalas adaptadas da
literatura); não os altero aqui sem alterar também a dissertação.
"""

# Escala Likert de 5 pontos, usada em todos os itens dos Blocos I a III.
LIKERT_SCALE = [
    (1, "Discordo Totalmente"),
    (2, "Discordo Parcialmente"),
    (3, "Neutro"),
    (4, "Concordo Parcialmente"),
    (5, "Concordo Totalmente"),
]

# Blocos I a III: (título do bloco, [(código, texto do item), ...]).
#   Bloco I   - verificação da manipulação (manipulation check): confere se o
#               participante percebeu o nível de humanização (HUM) e de
#               personalização (PER) da condição a que foi exposto.
#   Bloco II  - os construtos do modelo teórico (IDI, CON, PU, PEOU, IU, CSD).
#   Bloco III - variáveis de controle (VC).
LIKERT_BLOCKS = [
    (
        "Bloco I - Verificação da Manipulação",
        [
            ("HUM1", "O chatbot se comunicou de forma natural, parecendo uma conversa com um ser humano."),
            ("HUM2", "A linguagem utilizada pelo chatbot foi cordial e amigável."),
            ("HUM3", "Senti que o chatbot demonstrou proximidade durante o atendimento."),
            ("HUM4", "A interação com o chatbot transmitiu uma sensação de contato social, semelhante a uma conversa com uma pessoa real."),
            ("PER1", "A interface do chatbot deixou claro que se trata de um serviço oficial do IFAP Campus Santana."),
            ("PER2", "O chatbot utilizou termos e expressões próprios do ambiente acadêmico da instituição."),
            ("PER3", "A identidade visual e textual do chatbot reflete adequadamente a imagem do IFAP."),
            ("PER4", "O chatbot transmite características que são tipicamente associadas ao IFAP, e não a qualquer outra instituição de ensino."),
        ],
    ),
    (
        "Bloco II - Construtos do Modelo Teórico",
        [
            ("IDI1", "Sinto que o chatbot representa adequadamente os valores e a identidade do IFAP no ambiente digital."),
            ("IDI2", "Interagir com este chatbot é como interagir diretamente com a instituição."),
            ("IDI3", "Os elementos visuais e linguagem do chatbot são reconhecíveis como sendo do IFAP."),
            ("IDI4", "Considero que este chatbot é uma extensão legítima do IFAP no ambiente digital."),
            ("CON1", "Confio que as informações fornecidas pelo chatbot são precisas e corretas."),
            ("CON2", "Acredito que o chatbot atua de forma segura e protege meus dados durante a interação."),
            ("CON3", "Sinto que posso confiar nas orientações dadas por este sistema automatizado."),
            ("CON4", "O chatbot demonstra consistência e confiabilidade no atendimento prestado."),
            ("PU1", "O uso do chatbot melhoraria meu acesso aos serviços do IFAP."),
            ("PU2", "Utilizar o chatbot tornaria mais rápida a busca por informações institucionais."),
            ("PU3", "O chatbot é útil para resolver minhas dúvidas acadêmicas ou administrativas."),
            ("PU4", "No geral, considero que o chatbot traz benefícios práticos para o meu dia a dia na instituição."),
            ("PEOU1", "Aprender a interagir com o chatbot é fácil para mim."),
            ("PEOU2", "Acho que a interface do chatbot é clara e compreensível."),
            ("PEOU3", "É fácil fazer com que o chatbot faça o que eu preciso."),
            ("PEOU4", "No geral, considero o chatbot fácil de usar."),
            ("IU1", "Pretendo utilizar o chatbot sempre que precisar de informações do IFAP."),
            ("IU2", "Planejo usar o chatbot no futuro para acessar serviços institucionais."),
            ("IU3", "É provável que eu utilize este sistema automatizado como meu canal de atendimento preferencial."),
            ("IU4", "Pretendo continuar utilizando o chatbot do IFAP nos próximos meses, sempre que precisar acessar informações institucionais."),
            ("CSD1", "O uso do chatbot me incentiva a utilizar mais os serviços digitais oferecidos pelo IFAP."),
            ("CSD2", "Sinto-me mais engajado com a instituição ao utilizar este canal de atendimento."),
            ("CSD3", "A facilidade de acesso via chatbot aumenta minha frequência de uso dos sistemas institucionais."),
            ("CSD4", "Interagir com o chatbot do IFAP aumenta minha disposição para explorar outros canais digitais da instituição."),
        ],
    ),
    (
        "Bloco III - Variáveis de Controle",
        [
            ("VC1", "Tenho bastante experiência no uso de chatbots para atendimento ao cliente."),
            ("VC2", "Costumo utilizar serviços digitais e aplicativos no meu dia a dia."),
            ("VC3", "Sinto-me confortável interagindo com sistemas baseados em Inteligência Artificial."),
        ],
    ),
]

# Bloco IV - perfil: (título, [(código, pergunta, [opções]), ...]). São
# perguntas de múltipla escolha; "Prefiro não responder" é a opção vazia.
PROFILE_BLOCK = (
    "Bloco IV - Perfil do Participante",
    [
        ("VINCULO", "Qual é o seu vínculo principal com o IFAP Campus Santana?",
         ["Estudante", "Técnico Administrativo", "Docente", "Pai / Responsável / Comunidade Externa"]),
        ("FAIXA_ETARIA", "Qual é a sua faixa etária?",
         ["Menos de 18 anos", "18 a 24 anos", "25 a 34 anos", "35 a 44 anos", "45 anos ou mais"]),
        ("GENERO", "Qual é o seu gênero?",
         ["Feminino", "Masculino", "Prefiro não informar", "Outro"]),
        ("ESCOLARIDADE", "Qual é o seu nível de escolaridade?",
         ["Ensino Fundamental (completo ou incompleto)", "Ensino Médio (completo ou incompleto)",
          "Ensino Superior (completo ou incompleto)", "Pós-graduação"]),
        ("FREQUENCIA", "Com que frequência você acessa os canais digitais do IFAP? (site, SUAP, WhatsApp)",
         ["Diariamente", "Algumas vezes por semana", "Algumas vezes por mês", "Raramente", "Nunca acessei"]),
    ],
)


def all_question_codes():
    """Todos os códigos de item, na ordem em que aparecem no questionário."""
    codes = []
    for _, items in LIKERT_BLOCKS:
        codes += [code for code, _ in items]
    codes += [code for code, _, _ in PROFILE_BLOCK[1]]
    return codes


# Nome por extenso de cada construto, usado no painel e no codebook.
CONSTRUCT_LABELS = {
    "HUM": "Humanização da Interface",
    "PER": "Personalização Institucional",
    "IDI": "Identidade Digital Institucional Percebida",
    "CON": "Confiança em Inteligência Artificial",
    "PU": "Utilidade Percebida",
    "PEOU": "Facilidade de Uso Percebida",
    "IU": "Intenção de Uso",
    "CSD": "Engajamento de Serviços Digitais",
    "VC": "Variáveis de Controle",
}


def is_likert_code(code):
    """O item é da escala Likert (Blocos I a III)?"""
    return code in _LIKERT_CODES


def all_likert_codes():
    """Conjunto com os códigos de todos os itens Likert."""
    return set(_LIKERT_CODES)


# Tabelas de consulta montadas uma vez, quando o módulo é carregado.
_LIKERT_CODES = {code for _, items in LIKERT_BLOCKS for code, _ in items}
_QUESTION_TEXT = {code: text for _, items in LIKERT_BLOCKS for code, text in items}
_QUESTION_TEXT.update({code: text for code, text, _ in PROFILE_BLOCK[1]})
_LIKERT_LABELS = {str(value): label for value, label in LIKERT_SCALE}
_PROFILE_OPTIONS = {code: options for code, _, options in PROFILE_BLOCK[1]}


def question_text(code):
    """Texto do item a partir do código."""
    return _QUESTION_TEXT.get(code, code)


def answer_display(code, value):
    """Formato a resposta para leitura humana, ex.: '4 - Concordo Parcialmente'."""
    if is_likert_code(code) and value in _LIKERT_LABELS:
        return f"{value} - {_LIKERT_LABELS[value]}"
    return value


def profile_options(code):
    """Opções de resposta de um item do Bloco IV."""
    return _PROFILE_OPTIONS.get(code, [])


def is_valid_answer(code, value):
    """A resposta é uma das opções que o instrumento oferece?

    Eu confiro isso no servidor porque o navegador do participante não é
    confiável: qualquer pessoa pode editar o formulário e enviar um valor
    inventado (por exemplo, "7" numa escala de 1 a 5). Valores inválidos são
    descartados, como se o item tivesse ficado em branco.
    """
    if is_likert_code(code):
        return value in _LIKERT_LABELS
    return value in _PROFILE_OPTIONS.get(code, [])
