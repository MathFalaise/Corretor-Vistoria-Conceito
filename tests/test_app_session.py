"""Testes de app/session.py: ponte entre a sessão e o engine (RULES)."""

import unittest

from app.models import create_session
from app.session import process_and_store


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


if __name__ == "__main__":
    unittest.main()
