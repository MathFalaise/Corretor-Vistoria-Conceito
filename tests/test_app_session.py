"""Testes de app/session.py: ponte entre a sessão e o engine (RULES)."""

import unittest

from app.models import create_session
from app.session import approve_suggestion, process_and_store, reject_suggestion


class TestProcessAndStore(unittest.TestCase):
    def test_processamento_usa_rules_do_engine(self):
        session = create_session("00959.002.02")
        result = process_and_store(session, "a comporta apresenta condobradiças soltas")

        self.assertEqual(
            result.corrected_text,
            "a com porta apresenta com dobradiças soltas",
        )
        self.assertTrue(len(result.edits) >= 2)

    def test_preserva_original_text(self):
        session = create_session("00959.002.02")
        texto = "comporta"
        result = process_and_store(session, texto)

        self.assertEqual(result.original_text, texto)
        self.assertEqual(session.last_source_text, texto)

    def test_preserva_corrected_text(self):
        session = create_session("00959.002.02")
        result = process_and_store(session, "comum armário")

        self.assertEqual(result.corrected_text, "com um armário")

    def test_nao_altera_adversarial_trap(self):
        session = create_session("00959.002.02")
        result = process_and_store(session, "uso comum")

        self.assertEqual(result.corrected_text, "uso comum")
        self.assertEqual(result.edits, [])

    def test_sessao_guarda_resultado_e_edits(self):
        session = create_session("00959.002.02")
        result = process_and_store(session, "comporta")

        self.assertIs(session.last_result, result)
        self.assertEqual(session.edits, result.edits)


class TestProcessAndStoreUsaAnalyzeText(unittest.TestCase):
    """process_and_store agora usa analyze_text (Camada 0+1+2), não mais
    process_text (só Camada 1) — cobre o caso do diagnóstico."""

    def test_caso_real_comum_corredor_gera_sugestao(self):
        session = create_session("00959.002.02")
        result = process_and_store(
            session, "Comum corredor de uso comum do prédio."
        )

        # Camada 1 não tem regra para isso; nada é auto-aplicado além
        # da Camada 0 (o "*" inicial).
        self.assertEqual(
            result.corrected_text, "*Comum corredor de uso comum do prédio."
        )

        origem = [s.original for s in result.suggestions]
        self.assertIn("Comum", origem)
        # o segundo "comum" (em "uso comum") não deve gerar sugestão.
        self.assertEqual(origem.count("comum"), 0)

    def test_camada0_continua_aplicada(self):
        session = create_session("00959.002.02")
        result = process_and_store(session, "Piso em cerâmica, sem avarias.")
        self.assertTrue(result.corrected_text.startswith("*"))

    def test_sessao_guarda_suggestions(self):
        session = create_session("00959.002.02")
        result = process_and_store(
            session, "Comum corredor de uso comum do prédio."
        )
        self.assertEqual(session.last_result.suggestions, result.suggestions)


class TestApproveSuggestion(unittest.TestCase):
    def test_aprova_sugestao_do_caso_real(self):
        session = create_session("00959.002.02")
        result = process_and_store(
            session, "Comum corredor de uso comum do prédio."
        )
        suggestion = next(s for s in result.suggestions if s.original == "Comum")

        approved = approve_suggestion(session, suggestion)

        self.assertEqual(
            approved.corrected_text, "*Com um corredor de uso comum do prédio."
        )
        self.assertEqual(approved.suggestions, [])
        self.assertIs(session.last_result, approved)

    def test_aprovar_uma_sugestao_nao_remove_as_outras(self):
        session = create_session("00959.002.02")
        # dois candidatos independentes no mesmo texto.
        result = process_and_store(
            session, "Apresenta comjardim. Comum acesso ao corredor."
        )
        self.assertGreaterEqual(len(result.suggestions), 2)
        primeira = result.suggestions[0]

        approved = approve_suggestion(session, primeira)

        self.assertEqual(len(approved.suggestions), len(result.suggestions) - 1)
        self.assertNotIn(primeira, approved.suggestions)


class TestRejectSuggestion(unittest.TestCase):
    def test_rejeitar_nao_altera_o_texto(self):
        session = create_session("00959.002.02")
        result = process_and_store(
            session, "Comum corredor de uso comum do prédio."
        )
        suggestion = next(s for s in result.suggestions if s.original == "Comum")

        rejected = reject_suggestion(session, suggestion)

        self.assertEqual(rejected.corrected_text, result.corrected_text)
        self.assertNotIn(suggestion, rejected.suggestions)
        self.assertIs(session.last_result, rejected)

    def test_rejeitar_nao_cria_estrutura_de_historico(self):
        # Sessão não ganha nenhum campo novo de histórico de rejeição.
        session = create_session("00959.002.02")
        result = process_and_store(
            session, "Comum corredor de uso comum do prédio."
        )
        suggestion = result.suggestions[0]
        campos_antes = set(vars(session).keys())

        reject_suggestion(session, suggestion)

        self.assertEqual(set(vars(session).keys()), campos_antes)


if __name__ == "__main__":
    unittest.main()
