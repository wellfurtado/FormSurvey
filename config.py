# -*- coding: utf-8 -*-
"""Configuração do FormSurvey.

Eu leio tudo de variáveis de ambiente, que por sua vez vêm do arquivo .env na
raiz do projeto (carregado logo abaixo). Assim nenhum segredo (senha do
painel, chave de sessão) fica dentro do código ou do repositório: o .env está
no .gitignore e cada servidor tem o seu. O modelo comentado é o .env.example.
"""
import os


def _load_dotenv():
    """Carrego o .env manualmente, linha a linha, no formato CHAVE=valor.

    Preferi não usar a biblioteca python-dotenv porque isto aqui são dez
    linhas e evita uma dependência a mais. Uso setdefault para que uma
    variável já definida no ambiente (por exemplo, nos testes automatizados)
    tenha prioridade sobre o que está no arquivo.
    """
    path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# Chave que assina o cookie de sessão do Flask. Se ela vazar ou for fraca,
# alguém consegue forjar uma sessão de administrador. Por isso eu me recuso a
# iniciar sem ela, em vez de cair silenciosamente para um valor padrão
# conhecido (como acontecia antes com "dev-change-me"). O install.sh gera uma
# chave aleatória automaticamente.
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY não definida. Gere uma com:\n"
        '  python -c "import secrets; print(secrets.token_urlsafe(32))"\n'
        "e coloque no arquivo .env (veja .env.example)."
    )

# Onde fica o arquivo do banco SQLite. A pasta instance/ está no .gitignore:
# os dados coletados nunca vão para o repositório.
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH", os.path.join(os.path.dirname(__file__), "instance", "formsurvey.db")
)

# Senha do painel administrativo (/admin). Vazia = login sempre bloqueado.
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

# Número CAAE do parecer do Comitê de Ética. Ele aparece no texto dos termos.
CAAE = os.environ.get("CAAE", "")

# Eu só ligo isto (FORCE_HTTPS=1) quando o site estiver de fato atrás de HTTPS
# (Nginx com certificado). Controla o cookie "Secure" e faz os links gerados
# pelo sistema saírem como https://. Fica desligado por padrão para não
# quebrar o uso em rede local, sem certificado.
FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "0") == "1"


# =============================================================================
# Condições experimentais (delineamento fatorial 2x2 da dissertação)
# =============================================================================
# Cada participante é sorteado para UMA destas condições (ver assign_condition
# em app.py). Cada condição combina um nível de humanização ("hum") e um nível
# de personalização institucional ("per"): 0 = baixa, 1 = alta.
#
#   Condição | Humanização | Personalização
#   ---------+-------------+---------------
#      C1    |   baixa (0) |   baixa (0)
#      C2    |   alta  (1) |   baixa (0)
#      C3    |   baixa (0) |   alta  (1)
#      C4    |   alta  (1) |   alta  (1)
#
# Cada condição aponta para o endereço do chatbot correspondente, lido do .env
# (CHATBOT_URL_C1 ... CHATBOT_URL_C4). Se uma delas não estiver definida, uso
# CHATBOT_URL como reserva — útil em teste, quando ainda existe um chatbot só.
#
# Para reutilizar o FormSurvey em outro experimento, basta mudar este
# dicionário: o sorteio, o banco, o CSV e o painel se adaptam sozinhos ao
# número de condições e aos nomes dos fatores.
_DEFAULT_CHATBOT_URL = os.environ.get("CHATBOT_URL", "https://exemplo-ifap.edu.br/chatbot-prototipo")

CONDITIONS = {
    "C1": {"hum": 0, "per": 0},
    "C2": {"hum": 1, "per": 0},
    "C3": {"hum": 0, "per": 1},
    "C4": {"hum": 1, "per": 1},
}
for _name, _cond in CONDITIONS.items():
    _cond["url"] = os.environ.get(f"CHATBOT_URL_{_name}", _DEFAULT_CHATBOT_URL)

# Nomes dos fatores, na ordem em que viram colunas no CSV ("hum", "per").
FACTORS = [key for key in next(iter(CONDITIONS.values())) if key != "url"]
