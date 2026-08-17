"""Testes de pdf_import/importer.py: extração de PDF único, pareamento
por código, PDFs sem par, códigos diferentes, geração do dataset em
data/extracted/. Usa diretórios temporários — nunca escreve na pasta
data/ real do projeto."""

import json
import tempfile
import unittest
from pathlib import Path

from pdf_import.importer import extract_pdf, run_import
from tests.pdf_fixtures import SAMPLE_INSPECTION_PAGE, build_pdf


class TestExtractPdf(unittest.TestCase):
    def test_extrai_codigo_comodos_e_componentes_de_um_pdf_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "00959.002.02.pdf"
            build_pdf(pdf_path, [SAMPLE_INSPECTION_PAGE])

            extracted = extract_pdf(pdf_path)

            self.assertIsNone(extracted.error)
            self.assertEqual(extracted.inspection_code, "00959.002.02")
            nomes_comodos = [r["name"] for r in extracted.rooms]
            self.assertIn("Sala", nomes_comodos)
            self.assertIn("Cozinha", nomes_comodos)

    def test_pdf_inexistente_vira_erro_sem_lancar_excecao(self):
        extracted = extract_pdf("caminho/que/nao/existe.pdf")
        self.assertIsNotNone(extracted.error)
        self.assertEqual(extracted.rooms, [])


class TestRunImportPareamento(unittest.TestCase):
    def test_par_valido_quando_mesmo_codigo_nas_duas_pastas(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            uncorrected_dir = tmp / "nao_corrigidos"
            corrected_dir = tmp / "corrigidos"
            extracted_dir = tmp / "extracted"
            uncorrected_dir.mkdir()
            corrected_dir.mkdir()

            build_pdf(uncorrected_dir / "a.pdf", [SAMPLE_INSPECTION_PAGE])
            build_pdf(corrected_dir / "b.pdf", [SAMPLE_INSPECTION_PAGE])

            summary = run_import(uncorrected_dir, corrected_dir, extracted_dir)

            self.assertIn("00959.002.02", summary.paired_codes)
            self.assertEqual(summary.unpaired_uncorrected, [])
            self.assertEqual(summary.unpaired_corrected, [])

            diff_path = extracted_dir / "pairs" / "00959.002.02_diff.json"
            self.assertTrue(diff_path.exists())

    def test_pdf_sem_par_fica_marcado_como_unpaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            uncorrected_dir = tmp / "nao_corrigidos"
            corrected_dir = tmp / "corrigidos"
            uncorrected_dir.mkdir()
            corrected_dir.mkdir()

            build_pdf(uncorrected_dir / "a.pdf", [SAMPLE_INSPECTION_PAGE])
            # pasta de corrigidos vazia -> sem par

            summary = run_import(uncorrected_dir, corrected_dir, tmp / "extracted")

            self.assertEqual(summary.paired_codes, [])
            self.assertIn("00959.002.02", summary.unpaired_uncorrected)

    def test_codigos_diferentes_nao_formam_par(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            uncorrected_dir = tmp / "nao_corrigidos"
            corrected_dir = tmp / "corrigidos"
            uncorrected_dir.mkdir()
            corrected_dir.mkdir()

            pagina_a = [
                "Código da vistoria: 00959.002.02",
                "Sala",
                "Parede",
                "*Paredes ok.",
            ]
            pagina_b = [
                "Código da vistoria: 00471.002.05",
                "Sala",
                "Parede",
                "*Paredes diferentes.",
            ]
            build_pdf(uncorrected_dir / "a.pdf", [pagina_a])
            build_pdf(corrected_dir / "b.pdf", [pagina_b])

            summary = run_import(uncorrected_dir, corrected_dir, tmp / "extracted")

            self.assertEqual(summary.paired_codes, [])
            self.assertIn("00959.002.02", summary.unpaired_uncorrected)
            self.assertIn("00471.002.05", summary.unpaired_corrected)
            # nenhum diff foi gerado para códigos diferentes.
            self.assertFalse((tmp / "extracted" / "pairs").exists())


class TestGeracaoDoDatasetExtraido(unittest.TestCase):
    def test_gera_json_estruturado_por_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            uncorrected_dir = tmp / "nao_corrigidos"
            corrected_dir = tmp / "corrigidos"
            extracted_dir = tmp / "extracted"
            uncorrected_dir.mkdir()
            corrected_dir.mkdir()

            build_pdf(uncorrected_dir / "a.pdf", [SAMPLE_INSPECTION_PAGE])

            run_import(uncorrected_dir, corrected_dir, extracted_dir)

            json_path = extracted_dir / "nao_corrigidos" / "00959.002.02.json"
            self.assertTrue(json_path.exists())

            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["inspection_code"], "00959.002.02")
            self.assertIn("source_file", data)
            nomes_comodos = [r["name"] for r in data["rooms"]]
            self.assertIn("Sala", nomes_comodos)

            sala = next(r for r in data["rooms"] if r["name"] == "Sala")
            componentes = {c["name"]: c["text"] for c in sala["components"]}
            self.assertIn("Parede", componentes)
            self.assertTrue(componentes["Parede"].startswith("*"))

    def test_gera_resumo_da_importacao(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            uncorrected_dir = tmp / "nao_corrigidos"
            corrected_dir = tmp / "corrigidos"
            extracted_dir = tmp / "extracted"
            uncorrected_dir.mkdir()
            corrected_dir.mkdir()
            build_pdf(uncorrected_dir / "a.pdf", [SAMPLE_INSPECTION_PAGE])

            run_import(uncorrected_dir, corrected_dir, extracted_dir)

            summary_path = extracted_dir / "import_summary.json"
            self.assertTrue(summary_path.exists())
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(data["imported_count"], 1)

    def test_pdf_sem_codigo_identificavel_nao_e_perdido(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            uncorrected_dir = tmp / "nao_corrigidos"
            corrected_dir = tmp / "corrigidos"
            extracted_dir = tmp / "extracted"
            uncorrected_dir.mkdir()
            corrected_dir.mkdir()

            build_pdf(uncorrected_dir / "sem_codigo.pdf", [["Sala", "Parede", "*Ok."]])

            summary = run_import(uncorrected_dir, corrected_dir, extracted_dir)

            self.assertEqual(len(summary.imported), 1)
            self.assertEqual(len(summary.no_code_detected), 1)
            # ainda assim grava o json, usando o nome do arquivo.
            json_path = extracted_dir / "nao_corrigidos" / "sem_codigo.json"
            self.assertTrue(json_path.exists())


if __name__ == "__main__":
    unittest.main()
