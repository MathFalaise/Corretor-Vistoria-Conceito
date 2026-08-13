"""Testes do mecanismo do motor (independentes do corpus)."""

import unittest

from engine.models import Rule
from engine.pipeline import process_text


class TestPipelineMechanics(unittest.TestCase):
    def test_texto_sem_padroes_permanece_inalterado(self):
        result = process_text("piso em porcelanato sem avarias", rules=[])
        self.assertEqual(result.corrected_text, result.original_text)
        self.assertEqual(result.edits, [])

    def test_determinismo_mesma_entrada_mesma_saida(self):
        from engine.rules import RULES

        texto = "a comporta apresenta condobradiças soltas"
        resultado_1 = process_text(texto, RULES)
        resultado_2 = process_text(texto, RULES)
        self.assertEqual(resultado_1.corrected_text, resultado_2.corrected_text)
        self.assertEqual(
            [e.__dict__ for e in resultado_1.edits],
            [e.__dict__ for e in resultado_2.edits],
        )

    def test_edit_registra_todos_os_campos_exigidos(self):
        rule = Rule(
            rule_id="regra_teste",
            pattern=r"\bcomporta\b",
            replacement="com porta",
            category="word_split",
        )
        result = process_text("comporta", rules=[rule])

        self.assertEqual(len(result.edits), 1)
        edit = result.edits[0]
        self.assertEqual(edit.original, "comporta")
        self.assertEqual(edit.corrected, "com porta")
        self.assertEqual(edit.category, "word_split")
        self.assertEqual(edit.rule_id, "regra_teste")
        self.assertEqual(edit.correction_source, "rule")

    def test_original_text_preservado_mesmo_apos_correcao(self):
        from engine.rules import RULES

        result = process_text("comporta", RULES)
        self.assertEqual(result.original_text, "comporta")
        self.assertEqual(result.corrected_text, "com porta")

    def test_regra_nao_dispara_em_substring_de_outra_palavra(self):
        rule = Rule(
            rule_id="regra_teste",
            pattern=r"\bcomum armário\b",
            replacement="com um armário",
            category="word_split",
        )
        # "comum" sem "armário" na sequência não deve disparar a regra.
        result = process_text("uso comum", rules=[rule])
        self.assertEqual(result.corrected_text, "uso comum")
        self.assertEqual(result.edits, [])


if __name__ == "__main__":
    unittest.main()
