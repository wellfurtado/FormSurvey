-- =============================================================================
-- FormSurvey — estrutura do banco de dados (SQLite)
-- =============================================================================
-- Eu organizei o banco em DOIS grupos de tabelas que, de propósito, NÃO se
-- ligam entre si:
--
--   1) REGISTROS DE CONSENTIMENTO (adults, guardians, access_codes)
--      Guardam a decisão de cada pessoa diante do termo (concordou ou não) e,
--      no caso do responsável, o nome e o vínculo com o(a) menor — que é a
--      "assinatura" do TCLE. Aqui eu só guardo a DATA (sem hora) da decisão.
--
--   2) DADOS DA PESQUISA (participants, responses)
--      Guardam a condição experimental sorteada, os horários de cada etapa e
--      as respostas do questionário. Nenhuma coluna aqui aponta para o grupo 1.
--
-- Por que separar assim? Porque os termos aprovados pelo CEP prometem que as
-- respostas não podem ser associadas a quem respondeu. Se existisse uma chave
-- estrangeira de participants para guardians (como havia na versão anterior,
-- com a coluna ref_id), bastaria um JOIN para ligar as respostas ao nome do
-- responsável. Sem essa coluna, a ligação não existe no banco.
--
-- Por que só a DATA nos registros de consentimento? Porque se eu guardasse a
-- hora exata da decisão em um lado e a hora exata da criação do participante
-- no outro, daria para casar os dois pelo horário. Guardando só o dia, um
-- registro de consentimento fica "misturado" com todos os outros do mesmo dia.
--
-- Todas as tabelas usam "CREATE TABLE IF NOT EXISTS": rodar o init-db de novo
-- não apaga nada. Mudanças de estrutura exigem recriar o banco (ver README,
-- seção "Banco de dados").
-- =============================================================================


-- -----------------------------------------------------------------------------
-- adults: uma linha por adulto que leu o RCLE e tomou uma decisão.
-- Não tem nenhum dado pessoal: só se concordou (1) ou não (0) e o dia.
-- Serve para eu contar adesão e recusa no painel.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS adults (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    agreed     INTEGER NOT NULL CHECK (agreed IN (0, 1)),
    created_on TEXT    NOT NULL              -- AAAA-MM-DD (só a data)
);


-- -----------------------------------------------------------------------------
-- guardians: uma linha por responsável que leu o TCLE e tomou uma decisão.
-- Quando o responsável RECUSA, eu gravo a linha sem nome nem vínculo (NULL):
-- a recusa acontece antes de qualquer dado ser pedido.
-- Quando AUTORIZA, guardo o nome e o vínculo, que equivalem à assinatura do
-- termo. O nome do(a) menor NÃO é pedido nem guardado (o TCLE promete isso).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS guardians (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    guardian_name TEXT,                      -- NULL quando recusou
    relationship  TEXT,                      -- NULL quando recusou
    agreed        INTEGER NOT NULL CHECK (agreed IN (0, 1)),
    created_on    TEXT    NOT NULL           -- AAAA-MM-DD
);


-- -----------------------------------------------------------------------------
-- access_codes: o código de uso único que o responsável repassa ao(à) menor.
-- Cada autorização gera um código (UUID v4 em hexadecimal, 32 caracteres).
-- Esta tabela também é o registro do ASSENTIMENTO do(a) menor: quando ele(a)
-- decide no TALE, eu marco used = 1 e gravo minor_agreed (1 = sim, 0 = não).
-- Assim o assentimento fica preso à autorização que o originou, como exige o
-- fluxo TCLE -> TALE, sem precisar de uma tabela só para menores.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS access_codes (
    code         TEXT    PRIMARY KEY,         -- uuid4().hex
    guardian_id  INTEGER NOT NULL REFERENCES guardians(id),
    used         INTEGER NOT NULL DEFAULT 0 CHECK (used IN (0, 1)),
    minor_agreed INTEGER CHECK (minor_agreed IN (0, 1)),  -- NULL até o(a) menor decidir
    created_on   TEXT    NOT NULL,            -- AAAA-MM-DD (autorização)
    used_on      TEXT                         -- AAAA-MM-DD (assentimento)
);


-- -----------------------------------------------------------------------------
-- participants: uma linha por pessoa que entrou na pesquisa (adulto ou menor
-- que concordou). É o "crachá" anônimo do participante.
--
--   id        número sequencial; é o que aparece no CSV exportado.
--   token     UUID v4 aleatório; vai na URL das etapas e funciona como link
--             de retomada. É secreto: nunca aparece no CSV.
--   kind      'adult' ou 'minor' — o perfil de consentimento.
--   condition condição experimental sorteada (C1 a C4, ver config.py).
--   *_at      horários (UTC, ISO 8601) de cada etapa; servem para calcular
--             duração e para filtrar respostas rápidas demais na análise.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS participants (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    token                    TEXT    NOT NULL UNIQUE,
    kind                     TEXT    NOT NULL CHECK (kind IN ('adult', 'minor')),
    condition                TEXT    NOT NULL,
    created_at               TEXT    NOT NULL,  -- concordou com o termo
    chatbot_opened_at        TEXT,              -- clicou em "Abrir o chatbot" (1ª vez)
    questionnaire_started_at TEXT,              -- abriu o questionário (1ª vez)
    completed_at             TEXT               -- enviou o questionário
);


-- -----------------------------------------------------------------------------
-- responses: uma linha por item respondido. Item deixado em branco não gera
-- linha (por isso "itens_em_branco" no CSV é calculado, não armazenado).
-- question_code é o código do item (HUM1, PER2, VINCULO...) definido em
-- questions.py; value é o valor marcado (1 a 5 nos itens Likert, ou o texto
-- da opção nos itens de perfil).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS responses (
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    question_code  TEXT    NOT NULL,
    value          TEXT    NOT NULL,
    PRIMARY KEY (participant_id, question_code)
);
