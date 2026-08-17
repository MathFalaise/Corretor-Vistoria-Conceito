"""Testes de pdf_import/text_extraction.py: extração de texto e remoção
de cabeçalho/rodapé repetitivo. PDFs sintéticos (ver tests/pdf_fixtures.py)."""

import tempfile
import unittest
from pathlib import Path

from pdf_import.text_extraction import (
    extract_clean_lines,
    extract_pages_text,
    strip_repeated_boilerplate,
)
from tests.pdf_fixtures import build_pdf


class TestExtractPagesText(unittest.TestCase):
    def test_extrai_texto_de_uma_pagina(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "teste.pdf"
            build_pdf(pdf_path, [["Piso em cerâmica.", "Sem avarias."]])

            pages = extract_pages_text(pdf_path)

            self.assertEqual(len(pages), 1)
            self.assertIn("Piso em cerâmica.", pages[0])
            self.assertIn("Sem avarias.", pages[0])

    def test_separacao_de_paginas(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "teste.pdf"
            build_pdf(
                pdf_path,
                [
                    ["Conteúdo da página 1"],
                    ["Conteúdo da página 2"],
                    ["Conteúdo da página 3"],
                ],
            )

            pages = extract_pages_text(pdf_path)

            self.assertEqual(len(pages), 3)
            self.assertIn("Conteúdo da página 1", pages[0])
            self.assertIn("Conteúdo da página 2", pages[1])
            self.assertIn("Conteúdo da página 3", pages[2])
            # conteúdo de uma página não vaza para outra.
            self.assertNotIn("Conteúdo da página 2", pages[0])


class TestStripRepeatedBoilerplate(unittest.TestCase):
    def test_remove_linha_repetida_em_todas_as_paginas(self):
        pages = [
            ["CloudSLIM - Relatório", "Conteúdo A"],
            ["CloudSLIM - Relatório", "Conteúdo B"],
            ["CloudSLIM - Relatório", "Conteúdo C"],
        ]
        cleaned = strip_repeated_boilerplate(pages)

        for page in cleaned:
            self.assertNotIn("CloudSLIM - Relatório", page)
        self.assertIn("Conteúdo A", cleaned[0])
        self.assertIn("Conteúdo B", cleaned[1])
        self.assertIn("Conteúdo C", cleaned[2])

    def test_nao_atua_com_uma_pagina_so(self):
        pages = [["Única página", "Única página"]]
        cleaned = strip_repeated_boilerplate(pages)
        self.assertEqual(cleaned, pages)

    def test_nao_remove_conteudo_que_nao_se_repete(self):
        pages = [["Conteúdo único 1"], ["Conteúdo único 2"]]
        cleaned = strip_repeated_boilerplate(pages)
        self.assertEqual(cleaned, pages)


class TestExtractCleanLines(unittest.TestCase):
    def test_concatena_paginas_sem_boilerplate(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "teste.pdf"
            build_pdf(
                pdf_path,
                [
                    ["Rodapé fixo", "Sala", "Parede", "*Texto da parede."],
                    ["Rodapé fixo", "Cozinha", "Piso", "*Texto do piso."],
                ],
            )

            lines = extract_clean_lines(pdf_path)

            self.assertNotIn("Rodapé fixo", lines)
            self.assertIn("Sala", lines)
            self.assertIn("Cozinha", lines)


if __name__ == "__main__":
    unittest.main()
