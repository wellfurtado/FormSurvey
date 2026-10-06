# -*- coding: utf-8 -*-
"""Testes automatizados do FormSurvey, de ponta a ponta.

Eu simulo um navegador (o "test client" do Flask) percorrendo cada caminho do
sistema, como um participante faria, e confiro o que ficou gravado no banco.
Cada teste corresponde a uma regra que o sistema PRECISA cumprir — ética,
metodológica ou de segurança — e o nome do teste diz qual é.

Para rodar (na raiz do projeto):
    python -m unittest tests.test_flow -v

Os testes usam um banco temporário, apagado no final; nunca tocam o banco real.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Configuro o ambiente ANTES de importar o app, porque config.py lê as
# variáveis no momento da importação.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_PATH"] = _tmp_db.name
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ADMIN_PASSWORD"] = "test-admin-password"
# URL com "?" de propósito, para testar que o token é anexado com "&".
os.environ["CHATBOT_URL"] = "https://chatbot.exemplo/conversa?origem=formsurvey"
os.environ["CHATBOT_URL_C1"] = "https://chatbot.exemplo/c1"

import app as app_module  # noqa: E402
import config  # noqa: E402
import db  # noqa: E402

TOKEN_RE = re.compile(r"/pesquisa/([^/]+)/chatbot")
TIME_OF_DAY_RE = re.compile(r"\d{2}:\d{2}")


def token_from_location(location):
    match = TOKEN_RE.search(location)
    assert match, f"token não encontrado em {location!r}"
    return match.group(1)


class FlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app_module.app
        cls.app.config["TESTING"] = True
        with cls.app.app_context():
            db.init_db()

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(_tmp_db.name)
        except OSError:
            pass

    # --- utilitários dos testes ------------------------------------------

    def query_one(self, sql, params=()):
        with self.app.app_context():
            return db.query_one(sql, params)

    def query_all(self, sql, params=()):
        with self.app.app_context():
            return db.query_all(sql, params)

    def new_adult(self, client=None):
        """Percorro o caminho do adulto até a página do chatbot; devolvo o token."""
        client = client or self.app.test_client()
        resp = client.post("/adulto", data={"decision": "agree", "adult_declared": "yes"})
        self.assertEqual(resp.status_code, 302)
        return client, token_from_location(resp.location)

    def admin_client(self):
        client = self.app.test_client()
        client.post("/admin/login", data={"password": "test-admin-password"})
        return client

    # --- páginas gerais ----------------------------------------------------

    def test_index_loads(self):
        resp = self.app.test_client().get("/")
        self.assertEqual(resp.status_code, 200)

    # --- adulto ------------------------------------------------------------

    def test_adult_full_flow(self):
        client, token = self.new_adult()

        # Sem abrir o chatbot, o questionário não abre.
        resp = client.get(f"/pesquisa/{token}/questionario")
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"/pesquisa/{token}/chatbot", resp.location)

        # "Abrir o chatbot" registra o horário e leva ao chatbot da condição.
        resp = client.get(f"/pesquisa/{token}/chatbot/abrir")
        self.assertEqual(resp.status_code, 302)
        p = self.query_one("SELECT * FROM participants WHERE token = ?", (token,))
        self.assertIsNotNone(p["chatbot_opened_at"])
        self.assertTrue(resp.location.startswith(config.CONDITIONS[p["condition"]]["url"]))
        self.assertIn(f"token={token}", resp.location)

        # Agora o questionário abre e o horário de início é registrado.
        resp = client.get(f"/pesquisa/{token}/questionario")
        self.assertEqual(resp.status_code, 200)
        p = self.query_one("SELECT * FROM participants WHERE token = ?", (token,))
        self.assertIsNotNone(p["questionnaire_started_at"])

        # "7" não existe na escala e deve ser descartado; "5" e o perfil valem.
        resp = client.post(
            f"/pesquisa/{token}/questionario",
            data={"HUM1": "5", "HUM2": "7", "VINCULO": "Estudante"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"/pesquisa/{token}/concluido", resp.location)
        saved = {r["question_code"]: r["value"] for r in self.query_all(
            "SELECT question_code, value FROM responses WHERE participant_id = ?", (p["id"],))}
        self.assertEqual(saved, {"HUM1": "5", "VINCULO": "Estudante"})

        # Página final e comprovante em PDF.
        resp = client.get(f"/pesquisa/{token}/concluido")
        self.assertIn("Obrigado".encode("utf-8"), resp.data)
        resp = client.get(f"/pesquisa/{token}/comprovante.pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/pdf")
        self.assertTrue(resp.data.startswith(b"%PDF"))

        # Quem concluiu não responde de novo: volta para a página final.
        resp = client.get(f"/pesquisa/{token}/questionario")
        self.assertIn(f"/pesquisa/{token}/concluido", resp.location)

    def test_adult_must_declare_18_or_more(self):
        before = self.query_one("SELECT COUNT(*) n FROM participants")["n"]
        resp = self.app.test_client().post("/adulto", data={"decision": "agree"}, follow_redirects=True)
        self.assertIn("18 anos ou mais".encode("utf-8"), resp.data)
        self.assertEqual(self.query_one("SELECT COUNT(*) n FROM participants")["n"], before)

    def test_adult_declines_without_personal_data(self):
        before = self.query_one("SELECT COUNT(*) n FROM adults WHERE agreed = 0")["n"]
        resp = self.app.test_client().post("/adulto", data={"decision": "disagree"}, follow_redirects=True)
        self.assertIn("Decisão registrada".encode("utf-8"), resp.data)
        self.assertEqual(self.query_one("SELECT COUNT(*) n FROM adults WHERE agreed = 0")["n"], before + 1)

    def test_pdf_not_available_before_completion(self):
        client, token = self.new_adult()
        self.assertEqual(client.get(f"/pesquisa/{token}/comprovante.pdf").status_code, 404)

    # --- retomada -------------------------------------------------------

    def test_resume_link_works_without_session(self):
        """Se o cookie se perde (internet caiu, trocou de aparelho), o link
        com o token continua levando o participante de onde parou."""
        _, token = self.new_adult()
        fresh = self.app.test_client()
        self.assertEqual(fresh.get(f"/pesquisa/{token}/chatbot").status_code, 200)
        fresh.get(f"/pesquisa/{token}/chatbot/abrir")
        resp = fresh.post(f"/pesquisa/{token}/questionario", data={"HUM2": "3"})
        self.assertIn("/concluido", resp.location)

    def test_invalid_participant_token_is_404(self):
        resp = self.app.test_client().get("/pesquisa/token-que-nao-existe/chatbot")
        self.assertEqual(resp.status_code, 404)

    # --- responsável e menor -------------------------------------------

    def test_guardian_and_minor_flow(self):
        client = self.app.test_client()
        resp = client.post("/responsavel", data={"decision": "agree"})
        self.assertTrue(resp.location.endswith("/responsavel/detalhes"))

        resp = client.post(
            "/responsavel/detalhes",
            data={"guardian_name": "Maria Silva", "relationship": "Mãe"},
            follow_redirects=True,
        )
        self.assertIn("Autorização registrada".encode("utf-8"), resp.data)
        code = re.search(rb'class="code-box">([0-9a-f]{32})<', resp.data).group(1).decode()

        # O responsável baixa o comprovante do TCLE logo após autorizar.
        resp = client.get("/responsavel/comprovante.pdf")
        self.assertTrue(resp.data.startswith(b"%PDF"))

        # O(A) menor entra pelo link, em outro aparelho, e concorda.
        minor = self.app.test_client()
        resp = minor.get(f"/menor/acesso/{code}", follow_redirects=True)
        self.assertIn("Assentimento".encode("utf-8"), resp.data)
        resp = minor.post("/menor/assentimento", data={"decision": "agree"})
        token = token_from_location(resp.location)

        row = self.query_one("SELECT * FROM access_codes WHERE code = ?", (code,))
        self.assertEqual((row["used"], row["minor_agreed"]), (1, 1))
        p = self.query_one("SELECT * FROM participants WHERE token = ?", (token,))
        self.assertEqual(p["kind"], "minor")

        minor.get(f"/pesquisa/{token}/chatbot/abrir")
        resp = minor.post(f"/pesquisa/{token}/questionario", data={"HUM1": "4"})
        self.assertIn("/concluido", resp.location)
        self.assertTrue(minor.get(f"/pesquisa/{token}/comprovante.pdf").data.startswith(b"%PDF"))

        # O código não pode ser usado de novo, nem por link nem digitado.
        other = self.app.test_client()
        resp = other.post("/menor", data={"code": code}, follow_redirects=True)
        self.assertIn("já foi utilizado".encode("utf-8"), resp.data)
        resp = other.get(f"/menor/acesso/{code}", follow_redirects=True)
        self.assertIn("inválido ou já utilizado".encode("utf-8"), resp.data)

    def test_minor_declines_code_is_consumed(self):
        client = self.app.test_client()
        client.post("/responsavel", data={"decision": "agree"})
        resp = client.post("/responsavel/detalhes", data={"guardian_name": "Ana", "relationship": "Avó"},
                           follow_redirects=True)
        code = re.search(rb'class="code-box">([0-9a-f]{32})<', resp.data).group(1).decode()
        before = self.query_one("SELECT COUNT(*) n FROM participants")["n"]

        minor = self.app.test_client()
        minor.get(f"/menor/acesso/{code}")
        resp = minor.post("/menor/assentimento", data={"decision": "disagree"}, follow_redirects=True)
        self.assertIn("Decisão registrada".encode("utf-8"), resp.data)

        row = self.query_one("SELECT * FROM access_codes WHERE code = ?", (code,))
        self.assertEqual((row["used"], row["minor_agreed"]), (1, 0))
        self.assertEqual(self.query_one("SELECT COUNT(*) n FROM participants")["n"], before)

    def _authorize(self):
        """Faço uma autorização de responsável e devolvo o código gerado."""
        client = self.app.test_client()
        client.post("/responsavel", data={"decision": "agree"})
        resp = client.post("/responsavel/detalhes", data={"guardian_name": "Rita", "relationship": "Tia"},
                           follow_redirects=True)
        return re.search(rb'class="code-box">([0-9a-f]{32})<', resp.data).group(1).decode()

    def test_simultaneous_use_of_code_admits_only_one(self):
        """Duas pessoas abrem o mesmo link e clicam em SIM quase ao mesmo tempo:
        só uma pode entrar. Para reproduzir a corrida, faço a segunda
        requisição "ler" o código ainda como não usado (como aconteceria se ela
        tivesse lido o banco antes de a primeira gravar)."""
        code = self._authorize()
        first, second = self.app.test_client(), self.app.test_client()
        first.get(f"/menor/acesso/{code}")
        second.get(f"/menor/acesso/{code}")
        before = self.query_one("SELECT COUNT(*) n FROM participants")["n"]

        resp = first.post("/menor/assentimento", data={"decision": "agree"})
        self.assertIn("/pesquisa/", resp.location)

        stale_row = {"code": code, "used": 0}
        with mock.patch.object(app_module.db, "query_one", return_value=stale_row):
            resp = second.post("/menor/assentimento", data={"decision": "agree"})
        self.assertTrue(resp.location.endswith("/menor"))

        self.assertEqual(self.query_one("SELECT COUNT(*) n FROM participants")["n"], before + 1)
        row = self.query_one("SELECT used, minor_agreed FROM access_codes WHERE code = ?", (code,))
        self.assertEqual((row["used"], row["minor_agreed"]), (1, 1))

    def test_guardian_pdf_contains_access_link_and_code(self):
        """O PDF do responsável traz o link e o código, para que o acesso não
        se perca se a página for fechada."""
        import pdfgen
        captured = {}

        def fake_render(text):
            captured["text"] = text
            return b"%PDF-falso"

        client = self.app.test_client()
        client.post("/responsavel", data={"decision": "agree"})
        resp = client.post("/responsavel/detalhes", data={"guardian_name": "Rita", "relationship": "Tia"},
                           follow_redirects=True)
        code = re.search(rb'class="code-box">([0-9a-f]{32})<', resp.data).group(1).decode()
        with mock.patch.object(pdfgen, "_render", side_effect=fake_render):
            client.get("/responsavel/comprovante.pdf")
        self.assertIn(f"Código de acesso: {code}", captured["text"])
        self.assertIn(f"/menor/acesso/{code}", captured["text"])
        self.assertIn("uso único", captured["text"])

    def test_guardian_declines_gives_no_code(self):
        before = self.query_one("SELECT COUNT(*) n FROM access_codes")["n"]
        resp = self.app.test_client().post("/responsavel", data={"decision": "disagree"}, follow_redirects=True)
        self.assertIn("Decisão registrada".encode("utf-8"), resp.data)
        self.assertEqual(self.query_one("SELECT COUNT(*) n FROM access_codes")["n"], before)

    def test_guardian_details_require_consent_first(self):
        resp = self.app.test_client().get("/responsavel/detalhes")
        self.assertTrue(resp.location.endswith("/responsavel"))

    # --- sorteio das condições -----------------------------------------

    def test_assignment_is_balanced(self):
        """Depois de muitos participantes, os grupos diferem em no máximo 1."""
        for _ in range(23):
            self.new_adult()
        counts = Counter(r["condition"] for r in self.query_all("SELECT condition FROM participants"))
        self.assertEqual(set(counts), set(config.CONDITIONS))
        self.assertLessEqual(max(counts.values()) - min(counts.values()), 1)

    # --- anonimato -----------------------------------------------------

    def test_research_data_is_not_linked_to_consent_records(self):
        """As tabelas da pesquisa não têm nenhuma coluna que aponte para os
        registros de consentimento, e estes não guardam a hora do dia."""
        with self.app.app_context():
            conn = db.get_db()
            for table in ("participants", "responses"):
                fks = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
                self.assertTrue(all(fk["table"] == "participants" for fk in fks), table)
                cols = {c["name"] for c in conn.execute(f"PRAGMA table_info({table})")}
                self.assertFalse(cols & {"ref_id", "email", "guardian_id", "access_code"}, table)
            for table, column in (("adults", "created_on"), ("guardians", "created_on"),
                                  ("access_codes", "created_on"), ("access_codes", "used_on")):
                for row in conn.execute(f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL"):
                    self.assertIsNone(TIME_OF_DAY_RE.search(row[0]), f"{table}.{column}")

    # --- exportação ----------------------------------------------------

    def test_export_requires_admin_login(self):
        resp = self.app.test_client().get("/admin/exportar/respostas.csv")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login", resp.location)

    def test_export_csv_content(self):
        client, token = self.new_adult()
        client.get(f"/pesquisa/{token}/chatbot/abrir")
        client.post(f"/pesquisa/{token}/questionario", data={"PU1": "4"})
        p = self.query_one("SELECT * FROM participants WHERE token = ?", (token,))

        resp = self.admin_client().get("/admin/exportar/respostas.csv")
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode("utf-8-sig")
        lines = text.strip().splitlines()
        header = lines[0].split(",")
        with self.app.app_context():
            expected = [name for name, *_ in app_module.export_columns_dictionary()]
        self.assertEqual(header, expected)

        row = dict(zip(header, next(l for l in lines[1:] if l.split(",")[0] == str(p["id"])).split(",")))
        cond = config.CONDITIONS[p["condition"]]
        self.assertEqual(row["condicao"], p["condition"])
        self.assertEqual((row["hum"], row["per"]), (str(cond["hum"]), str(cond["per"])))
        self.assertEqual(row["PU1"], "4")
        self.assertEqual(row["itens_em_branco"], str(len(header) - header.index("HUM1") - 1))

        # O token (link de retomada) e nomes nunca aparecem no CSV.
        self.assertNotIn(token, text)
        self.assertNotIn("Maria Silva", text)

    def test_codebook_matches_csv_columns(self):
        out = subprocess.run(
            [sys.executable, "-m", "flask", "--app", "app", "codebook"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=os.environ.copy(),
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        names = [line.split(",")[0] for line in out.stdout.strip().splitlines()[1:]]
        with self.app.app_context():
            expected = [name for name, *_ in app_module.export_columns_dictionary()]
        self.assertEqual(names, expected)

    # --- painel --------------------------------------------------------

    def test_admin_requires_login(self):
        client = self.app.test_client()
        resp = client.get("/admin")
        self.assertIn("/admin/login", resp.location)

        resp = client.post("/admin/login", data={"password": "errada"}, follow_redirects=True)
        self.assertIn("Senha incorreta".encode("utf-8"), resp.data)

        client.post("/admin/login", data={"password": "test-admin-password"})
        resp = client.get("/admin")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Painel de respostas".encode("utf-8"), resp.data)
        self.assertIn("Condições experimentais".encode("utf-8"), resp.data)

    def test_login_does_not_redirect_to_other_sites(self):
        for evil in ("https://site-falso.com", "//site-falso.com", "/\\site-falso.com"):
            resp = self.app.test_client().post(
                f"/admin/login?next={evil}", data={"password": "test-admin-password"})
            self.assertEqual(resp.location, "/admin", evil)
        resp = self.app.test_client().post(
            "/admin/login?next=/admin/exportar/respostas.csv", data={"password": "test-admin-password"})
        self.assertEqual(resp.location, "/admin/exportar/respostas.csv")


if __name__ == "__main__":
    unittest.main()
