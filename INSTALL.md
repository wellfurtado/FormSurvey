# Guia de instalação — FormSurvey

Passo a passo para colocar o FormSurvey no ar em um servidor Linux (testado em
Debian 13). Para testar no seu computador, veja a seção 9.1 do [README](README.md).

Todos os comandos abaixo são executados **como root** no servidor (ou com `sudo`).

---

## 1. Pré-requisitos

```bash
apt update
apt install -y python3 python3-venv git fonts-dejavu-core
```

| Pacote | Para quê |
|---|---|
| `python3`, `python3-venv` | Rodar o sistema em um ambiente isolado (Python 3.9 ou mais novo) |
| `git` | Baixar e atualizar o código a partir do GitHub |
| `fonts-dejavu-core` | Fonte com acentos para os comprovantes em PDF. Sem ela, os PDFs saem sem acentuação |

O servidor precisa de pouco: 1 vCPU, 1 GB de RAM livre e alguns MB de disco bastam
para uma pesquisa com centenas de participantes.

## 2. Baixar o código

```bash
git clone https://github.com/wellfurtado/chatif.git /opt/formsurvey
cd /opt/formsurvey
```

## 3. Instalar

```bash
./install.sh
```

O script:
- cria o ambiente virtual (`venv/`) e instala as dependências, com as versões fixadas
  em `requirements.txt`;
- cria o `.env` a partir do `.env.example` e gera **sozinho** a `SECRET_KEY` e a
  `ADMIN_PASSWORD`. A senha do painel aparece **uma única vez** no terminal; anote-a;
- cria o banco de dados (`instance/formsurvey.db`).

Depois, entregue a pasta ao usuário sem privilégios que vai rodar o serviço:

```bash
chown -R www-data:www-data /opt/formsurvey
chmod 600 /opt/formsurvey/.env
```

## 4. Completar a configuração

Edite o `.env` (`nano /opt/formsurvey/.env`) e preencha:

```ini
CAAE=99324326.3.0000.0311
CHATBOT_URL_C1=https://...   # chatbot da condição C1 (baixa hum., baixa pers.)
CHATBOT_URL_C2=https://...   # C2 (alta hum., baixa pers.)
CHATBOT_URL_C3=https://...   # C3 (baixa hum., alta pers.)
CHATBOT_URL_C4=https://...   # C4 (alta hum., alta pers.)
```

Enquanto os chatbots não existirem, deixe os `CHATBOT_URL_C*` vazios: todas as
condições usam o `CHATBOT_URL`.

## 5. Testar antes de deixar no ar

```bash
sudo -u www-data venv/bin/flask --app app run --host 0.0.0.0 --port 8000
```

Acesse `http://IP_DO_SERVIDOR:8000`, percorra os três caminhos (adulto, responsável →
menor) e pare com `Ctrl+C`. Esse servidor é só para teste; em produção quem roda o
sistema é o Gunicorn (passo 6).

## 6. Deixar rodando permanentemente (systemd + Gunicorn)

```bash
cp formsurvey.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now formsurvey
systemctl status formsurvey
```

O serviço sobe o sistema na **porta 80** (`http://IP_DO_SERVIDOR/`), roda como
`www-data` e reinicia sozinho em caso de falha ou de reinício do servidor.

- Ver os logs: `journalctl -u formsurvey -f`
- Reiniciar depois de mudar o `.env`: `systemctl restart formsurvey`

## 7. HTTPS com domínio público (Nginx + Certbot)

Com dados de menores, o acesso pela internet **precisa** ser por HTTPS. Faça esta
etapa quando houver um domínio público apontando para o servidor (peça à TI da
instituição o DNS e a liberação das portas 80 e 443).

```bash
apt install -y nginx certbot python3-certbot-nginx
```

1. **Tire o Gunicorn da porta 80**, para o Nginx usá-la. Em
   `/etc/systemd/system/formsurvey.service`, troque `-b 0.0.0.0:80` por
   `-b 127.0.0.1:8000`. Depois: `systemctl daemon-reload && systemctl restart formsurvey`.

2. **Crie** `/etc/nginx/sites-available/formsurvey`:

   ```nginx
   server {
       listen 80;
       server_name pesquisa.seudominio.edu.br;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Ative e peça o certificado:**

   ```bash
   ln -s /etc/nginx/sites-available/formsurvey /etc/nginx/sites-enabled/
   rm -f /etc/nginx/sites-enabled/default
   nginx -t && systemctl reload nginx
   certbot --nginx -d pesquisa.seudominio.edu.br
   ```

   O Certbot configura o HTTPS e renova o certificado sozinho.

4. **Ligue o modo HTTPS do sistema:**

   ```bash
   sed -i "s|^FORCE_HTTPS=.*|FORCE_HTTPS=1|" /opt/formsurvey/.env
   systemctl restart formsurvey
   ```

   Isso faz o cookie de sessão trafegar só por HTTPS e os links gerados (acesso do
   menor, retomada) saírem com `https://`. Só ligue depois de confirmar que o HTTPS
   funciona.

## 8. Backup diário

```bash
chmod +x /opt/formsurvey/backup.sh
echo "30 2 * * * root /opt/formsurvey/backup.sh" > /etc/cron.d/formsurvey-backup
/opt/formsurvey/backup.sh          # testa agora
ls -l /var/backups/formsurvey/
```

Todo dia às 2h30 é gravada uma cópia consistente do banco em
`/var/backups/formsurvey/formsurvey-AAAA-MM-DD.db` (só o root lê). Cópias com mais de
30 dias são apagadas. Para restaurar uma cópia:

```bash
systemctl stop formsurvey
cp /var/backups/formsurvey/formsurvey-AAAA-MM-DD.db /opt/formsurvey/instance/formsurvey.db
chown www-data:www-data /opt/formsurvey/instance/formsurvey.db
systemctl start formsurvey
```

## 9. Painel e exportação

- **Painel:** `http://SERVIDOR/admin`, com a senha do passo 3.
- **CSV para SPSS/R:** no painel, menu **Exportar CSV**. O dicionário das colunas está
  em [`dados/codebook.csv`](dados/codebook.csv).

## 10. Atualizar o sistema

Depois de publicar mudanças no GitHub:

```bash
cd /opt/formsurvey
sudo -u www-data git pull
sudo -u www-data venv/bin/pip install -r requirements.txt -q
systemctl restart formsurvey
```

O `.env` e o banco (`instance/`) ficam fora do Git e **não são tocados** pela
atualização.

**Se a versão nova mudar a estrutura do banco** (o CHANGELOG avisa), o banco precisa
ser recriado. Isso **só pode ser feito antes do início da coleta**, porque apaga os
dados:

```bash
systemctl stop formsurvey
mv instance/formsurvey.db instance/formsurvey.db.antigo-$(date +%F)
sudo -u www-data venv/bin/flask --app app init-db
systemctl start formsurvey
```

## 11. Encerramento da coleta

Ao fim da coleta, o Ofício Circular nº 2/2021/CONEP recomenda baixar os dados para um
dispositivo local e apagá-los do ambiente virtual:

1. exporte o CSV pelo painel;
2. copie o banco para o seu computador:
   `scp root@SERVIDOR:/opt/formsurvey/instance/formsurvey.db .`;
3. no servidor, pare o serviço e apague o banco e os backups:

   ```bash
   systemctl disable --now formsurvey
   rm /etc/cron.d/formsurvey-backup
   rm -f /opt/formsurvey/instance/formsurvey.db /var/backups/formsurvey/*.db
   ```

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| O serviço não sobe e o log diz `SECRET_KEY não definida` | `.env` ausente ou sem a chave | Rode `./install.sh` ou preencha `SECRET_KEY` no `.env` |
| `Address already in use` | Outro programa usa a porta | `ss -tlnp` para descobrir qual; troque a porta no serviço |
| PDF sem acentos | Fonte ausente | `apt install fonts-dejavu-core` e `systemctl restart formsurvey` |
| `no such column` no log após atualizar | A estrutura do banco mudou | Veja "Se a versão nova mudar a estrutura do banco" (passo 10) |
| Links do menor saem com `http://` mesmo com HTTPS | `FORCE_HTTPS` desligado | Passo 7.4 |
| Termos mostram "a ser preenchido após aprovação" | `CAAE` vazio no `.env` | Passo 4 |
