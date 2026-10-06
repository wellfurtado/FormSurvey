# Histórico de versões

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), e as
versões seguem o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.9.1] — 2026-10-06

### Adicionado
- O PDF do responsável traz, logo no início, o **link e o código de acesso do menor**,
  com o aviso de que o acesso é de uso único. Assim o acesso não se perde se a página
  for fechada antes de ser repassado.
- Documentação das proteções e dos limites do código de acesso do menor (README,
  seção 7).

### Corrigido
- **Uso simultâneo do mesmo código:** se duas pessoas abrissem o mesmo link e clicassem
  em SIM quase ao mesmo tempo, as duas poderiam participar. O código agora é consumido
  em uma única operação no banco (`UPDATE ... WHERE used = 0`): só a primeira entra, e
  o código expira para sempre no momento da decisão.

## [0.9.0] — 2026-10-05

Versão preparada para a coleta: implementa o delineamento experimental da dissertação
e alinha o sistema ao texto dos termos aprovados pelo CEP.

> ⚠️ **A estrutura do banco mudou.** Um banco da versão 0.1 precisa ser recriado
> (INSTALL.md, passo 10). Como a coleta ainda não começou, nenhum dado é perdido.

### Adicionado
- **Sorteio balanceado** de cada participante em uma das quatro condições do fatorial
  2x2 (C1 a C4), gravado em `participants.condition`.
- **Um endereço de chatbot por condição** (`CHATBOT_URL_C1` a `CHATBOT_URL_C4`); o
  participante é redirecionado com `?token=` para que o chatbot possa associar as
  conversas ao participante anônimo.
- **Registro de ida e volta do chatbot**: horário da primeira abertura do chatbot e do
  questionário. O questionário só abre depois que o chatbot foi aberto.
- **CSV completo para análise**: número sequencial do participante, condição, fatores
  `hum` e `per` (0/1), horários, durações em segundos e quantidade de itens em branco.
- **Codebook** gerado pelo sistema (`flask --app app codebook`) em `dados/codebook.csv`.
- **Comprovante em PDF para download** (termo + respostas) ao final da pesquisa, e
  comprovante do TCLE para o responsável logo após autorizar.
- **Declaração "tenho 18 anos ou mais"** no caminho do adulto.
- **Painel por condição**: sorteados, aberturas do chatbot, conclusões e médias de cada
  construto por condição (acompanhamento da verificação da manipulação).
- **Validação das respostas** contra o instrumento (valores fora da escala são
  descartados).
- `backup.sh` para backup diário consistente do banco.
- Documentação completa no README (diagramas de todas as etapas, banco de dados,
  privacidade, segurança, ficha do PTT), `CITATION.cff` e este CHANGELOG.
- Código comentado em todos os arquivos.

### Alterado
- **Separação total entre respostas e identidade**: removida a coluna
  `participants.ref_id`, que permitia ligar as respostas ao nome por um JOIN. Os
  registros de consentimento passaram a guardar só a data (sem hora).
- O assentimento do menor passou a ser registrado na própria tabela `access_codes`
  (colunas `minor_agreed` e `used_on`); a tabela `minors` deixou de existir.
- O responsável que quiser responder ao questionário agora participa **pelo RCLE**,
  como adulto, em vez de responder sob o TCLE.
- A exportação CSV passou a exigir o login do painel (`/admin/exportar/respostas.csv`),
  em vez de um token na URL.
- O sistema se recusa a iniciar sem `SECRET_KEY` (antes usava um valor padrão
  conhecido).
- O modo de desenvolvimento (`python app.py`) escuta só em `127.0.0.1`.
- Versões das dependências fixadas em `requirements.txt`.
- Nota eletrônica do RCLE: "enviamos uma cópia para o seu e-mail" passou a "você poderá
  baixar uma cópia em PDF".

### Removido
- **Coleta de e-mail** de adultos, responsáveis e menores, e todo o envio de e-mail
  (SMTP, `mailer.py`, `email_templates.py`, `settings.py`, tela de configuração SMTP).
  Os termos aprovados prometem não coletar e-mail.
- **Nome do menor** (o TCLE promete não coletá-lo).
- `EXPORT_TOKEN`.

### Corrigido
- *Open redirect* no login do painel (`/admin/login?next=` aceitava qualquer site).

## [0.1.0] — 2026-07-12

Primeira versão, instalada no servidor do IFAP Campus Santana: fluxos RCLE, TCLE e
TALE com código de uso único, link de retomada, questionário (Anexo I), envio do
comprovante por e-mail, painel administrativo e exportação CSV.
