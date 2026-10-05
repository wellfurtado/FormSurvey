#!/usr/bin/env bash
# =============================================================================
# Instalação do FormSurvey em um servidor Linux (Debian/Ubuntu).
#
# O que eu faço aqui, em ordem:
#   1. crio um ambiente virtual Python (venv) isolado do sistema;
#   2. instalo as dependências com as versões fixadas em requirements.txt;
#   3. na primeira vez, crio o .env e gero sozinho os segredos (SECRET_KEY e
#      ADMIN_PASSWORD) com o gerador criptográfico do Python;
#   4. crio as tabelas do banco (não apaga nada se o banco já existir).
#
# Pode rodar de novo sem medo: o .env existente e o banco são preservados.
# Passo a passo completo, incluindo systemd e HTTPS, em INSTALL.md.
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null; then
    echo "python3 não encontrado. Instale com: apt install python3 python3-venv" >&2
    exit 1
fi

python3 -m venv venv
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

if [ ! -f .env ]; then
    cp .env.example .env
    SECRET_KEY=$(venv/bin/python -c "import secrets; print(secrets.token_urlsafe(32))")
    ADMIN_PASSWORD=$(venv/bin/python -c "import secrets; print(secrets.token_urlsafe(12))")
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${ADMIN_PASSWORD}|" .env
    echo "Criei o .env com SECRET_KEY e ADMIN_PASSWORD gerados automaticamente."
    echo "Senha do painel administrativo (/admin): ${ADMIN_PASSWORD}"
    echo "Guarde essa senha agora. Para trocá-la depois, edite o .env."
    echo "Ainda faltam no .env: CAAE e os endereços do chatbot (CHATBOT_URL_C1 a C4)."
fi

venv/bin/flask --app app init-db

echo
echo "Instalação concluída."
echo "Teste rápido (servidor de desenvolvimento):"
echo "  venv/bin/flask --app app run --host 0.0.0.0 --port 8000"
echo
echo "Para rodar como serviço permanente, veja formsurvey.service e INSTALL.md."
