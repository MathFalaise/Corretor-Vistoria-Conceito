"""Testes de engine/pipeline.py::analyze_text — Camada 0+1+2 combinadas.

Não modifica test_pipeline.py nem test_pipeline_structural.py:
process_text() e process_text_full() continuam exatamente como estavam
(comprovado por eles próprios continuarem passando). analyze_text() é
uma função nova e aditiva.
"""

import unittest

from engine.pipeline import analyze_text
from engine.rules import RULES


class TestAnalyzeTextCombinaCamadas(unittest.TestCase):
    def test_camada1_continua_auto_aplicando_como_antes(self):
        # "comporta" já é coberto por uma regra determinística (Camada
        # 1) — continua sendo corrigido automaticamente, sem virar
        # sugestão duplicada da Camada 2.
        result = analyze_text("Apresenta comporta solta.", RULES)
        self.assertEqual(result.corrected_text, "*Apresenta com porta solta.")
        self.assertEqual(
            [s.original for s in result.suggestions if s.original == "comporta"], []
        )

    def test_camada2_gera_sugestao_para_o_que_camada1_nao_cobre(self):
        result = analyze_text("Apresenta comjardim com plantas.", RULES)
        # corrected_text não é alterado pela Camada 2.
        self.assertIn("comjardim", result.corrected_text)
        alvo = [s for s in result.suggestions if s.original == "comjardim"]
        self.assertEqual(len(alvo), 1)
        self.assertEqual(alvo[0].candidates[0].corrected, "com jardim")

    def test_suggestions_nunca_alteram_corrected_text(self):
        # "acesso comum" não é coberto por nenhuma regra de Camada 1 —
        # só a Camada 2 o vê, e mesmo assim não pode alterar o texto.
        # O único edit presente deve ser o "*" da Camada 0 (estrutural),
        # nunca um edit lexical derivado da sugestão de "comum".
        texto = "Apresenta acesso comum entre as unidades."
        result = analyze_text(texto, RULES)
        self.assertGreaterEqual(len(result.suggestions), 1)
        self.assertIn("comum", result.corrected_text)
        self.assertNotIn("com um", result.corrected_text)
        categorias_dos_edits = [e.category for e in result.edits]
        self.assertNotIn("word_split", categorias_dos_edits)
        self.assertNotIn("possible_word_fusion", categorias_dos_edits)

    def test_adversarial_trap_no_pipeline_completo(self):
        for texto in ("uso comum", "de uso comum do prédio", "área comum"):
            with self.subTest(texto=texto):
                result = analyze_text(texto, RULES)
                self.assertEqual(result.corrected_text, texto)
                self.assertEqual(result.suggestions, [])

    def test_original_text_preservado(self):
        texto = "Apresenta comporta e comjardim."
        result = analyze_text(texto, RULES)
        self.assertEqual(result.original_text, texto)

    def test_aceita_parametros_de_contexto_opcionais(self):
        # A assinatura já aceita room/component/inspection_code/
        # other_texts (uso futuro) sem quebrar quando ausentes.
        result = analyze_text(
            "Apresenta comjardim.",
            RULES,
            room="Sala",
            component="Piso",
            inspection_code="00959.002.02",
            other_texts=["Piso em cerâmica."],
        )
        self.assertTrue(result.suggestions)


if __name__ == "__main__":
    unittest.main()
