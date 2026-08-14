"""Testes de engine/pipeline.py::process_text_full — Camada 0 + Camada 1.

Não modifica tests/test_pipeline.py: process_text() continua com o
comportamento original, testado ali. Aqui testamos apenas a nova
função de combinação.
"""

import unittest

from engine.pipeline import process_text, process_text_full
from engine.rules import RULES


class TestProcessTextFull(unittest.TestCase):
    def test_combina_estrutural_e_lexical(self):
        texto = "Apresenta   uma comporta  solta ,  com  folga ."
        result = process_text_full(texto, RULES)
        self.assertEqual(
            result.corrected_text,
            "*Apresenta uma com porta solta, com folga.",
        )
        categorias = {e.category for e in result.edits}
        self.assertIn("whitespace", categorias)
        self.assertIn("punctuation_spacing", categorias)
        self.assertIn("bullet_marker", categorias)
        self.assertIn("word_split", categorias)

    def test_original_text_preservado(self):
        texto = "comporta  solta"
        result = process_text_full(texto, RULES)
        self.assertEqual(result.original_text, texto)

    def test_nao_altera_process_text_original(self):
        # process_text() isolado continua sem normalização estrutural.
        texto = "porta   com espaços duplicados"
        resultado_puro = process_text(texto, RULES)
        self.assertEqual(resultado_puro.corrected_text, texto)

    def test_process_text_full_normaliza_mesmo_sem_padrao_lexical(self):
        texto = "Piso  em  cerâmica ,  sem avarias ."
        result = process_text_full(texto, [])
        self.assertEqual(result.corrected_text, "*Piso em cerâmica, sem avarias.")

    def test_adversarial_trap_permanece_intacto_no_pipeline_completo(self):
        texto = "de uso comum do prédio."
        result = process_text_full(texto, RULES)
        self.assertEqual(result.corrected_text, texto)
        self.assertEqual(result.edits, [])


if __name__ == "__main__":
    unittest.main()
