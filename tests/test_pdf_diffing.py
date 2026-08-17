"""Testes de pdf_import/diffing.py."""

import unittest

from pdf_import.diffing import diff_extractions
from pdf_import.importer import ExtractedPdf


def _extracted(code, rooms, source="teste.pdf"):
    return ExtractedPdf(
        source_file=source, inspection_code=code, rooms=rooms, unmatched_text=""
    )


class TestDiffExtractions(unittest.TestCase):
    def test_levanta_erro_para_codigos_diferentes(self):
        original = _extracted("00959.002.02", [])
        corrigido = _extracted("00471.002.05", [])
        with self.assertRaises(ValueError):
            diff_extractions(original, corrigido)

    def test_marca_componente_identico(self):
        rooms = [{"name": "Sala", "components": [{"name": "Piso", "text": "*Piso ok."}]}]
        original = _extracted("00959.002.02", rooms)
        corrigido = _extracted("00959.002.02", rooms)

        result = diff_extractions(original, corrigido)

        self.assertEqual(result["inspection_code"], "00959.002.02")
        componente = result["rooms"][0]["components"][0]
        self.assertEqual(componente["status"], "identical")

    def test_detecta_diferenca_e_gera_diff_legivel(self):
        original_rooms = [
            {
                "name": "Hall de Entrada",
                "components": [
                    {"name": "OBS", "text": "Comum corredor de uso comum do prédio."}
                ],
            }
        ]
        corrigido_rooms = [
            {
                "name": "Hall de Entrada",
                "components": [
                    {"name": "OBS", "text": "*Com um corredor de uso comum do prédio."}
                ],
            }
        ]
        original = _extracted("00959.002.02", original_rooms, "nao_corrigido.pdf")
        corrigido = _extracted("00959.002.02", corrigido_rooms, "corrigido.pdf")

        result = diff_extractions(original, corrigido)

        componente = result["rooms"][0]["components"][0]
        self.assertEqual(componente["status"], "different")
        self.assertEqual(
            componente["original_text"], "Comum corredor de uso comum do prédio."
        )
        self.assertEqual(
            componente["corrected_text"], "*Com um corredor de uso comum do prédio."
        )
        self.assertTrue(componente["differences"])
        self.assertEqual(
            result["source_files"],
            {"original": "nao_corrigido.pdf", "corrected": "corrigido.pdf"},
        )

    def test_componente_so_no_original_nao_e_inventado_no_corrigido(self):
        original_rooms = [
            {"name": "Sala", "components": [{"name": "Janela", "text": "*Janela ok."}]}
        ]
        corrigido_rooms = [{"name": "Sala", "components": []}]
        original = _extracted("00959.002.02", original_rooms)
        corrigido = _extracted("00959.002.02", corrigido_rooms)

        result = diff_extractions(original, corrigido)
        componente = result["rooms"][0]["components"][0]
        self.assertEqual(componente["status"], "only_in_original")

    def test_comodo_so_no_corrigido(self):
        original = _extracted("00959.002.02", [])
        corrigido_rooms = [{"name": "Varanda", "components": []}]
        corrigido = _extracted("00959.002.02", corrigido_rooms)

        result = diff_extractions(original, corrigido)
        self.assertEqual(result["rooms"][0]["status"], "only_in_corrected")


if __name__ == "__main__":
    unittest.main()
