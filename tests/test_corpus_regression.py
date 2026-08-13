"""Testes de regressão que rodam o motor contra todo o corpus_seed.jsonl.

Dois tipos de asserção:
- case_type == "correction": a saída do motor deve bater exatamente
  com o target_text do corpus.
- case_type in ("no_correction_needed", "adversarial_trap"): a saída
  deve ser IDÊNTICA ao source_text. Qualquer alteração aqui é uma
  falha de segurança, não uma falha de cobertura, e deve travar o
  build.
"""

import json
import unittest
from pathlib import Path

from engine.pipeline import process_text
from engine.rules import RULES

CORPUS_PATH = Path(__file__).resolve().parent.parent / "corpus" / "corpus_seed.jsonl"


def load_corpus():
    cases = []
    with open(CORPUS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


class TestCorpusRegression(unittest.TestCase):
    def test_corpus_nao_esta_vazio(self):
        self.assertTrue(load_corpus(), "corpus_seed.jsonl não pode estar vazio")

    def test_casos_de_correcao(self):
        cases = [c for c in load_corpus() if c["case_type"] == "correction"]
        self.assertGreaterEqual(len(cases), 3, "esperado ao menos 3 casos de correção")

        for case in cases:
            with self.subTest(case_id=case["id"], source=case["source_text"]):
                result = process_text(case["source_text"], RULES)
                self.assertEqual(
                    result.corrected_text,
                    case["target_text"],
                    f"Falha na correção esperada para o caso {case['id']} "
                    f"('{case['source_text']}' -> esperado '{case['target_text']}', "
                    f"obtido '{result.corrected_text}')",
                )

    def test_casos_de_seguranca_nao_devem_ser_alterados(self):
        """no_correction_needed e adversarial_trap: saída == entrada, sempre."""
        cases = [
            c
            for c in load_corpus()
            if c["case_type"] in ("no_correction_needed", "adversarial_trap")
        ]
        self.assertGreaterEqual(
            len(cases), 2, "esperado ao menos 1 no_correction_needed e 1 adversarial_trap"
        )

        for case in cases:
            with self.subTest(case_id=case["id"], source=case["source_text"]):
                result = process_text(case["source_text"], RULES)
                self.assertEqual(
                    result.corrected_text,
                    case["source_text"],
                    f"REGRESSÃO DE SEGURANÇA no caso {case['id']} "
                    f"({case['case_type']}): '{case['source_text']}' foi "
                    f"alterado indevidamente para '{result.corrected_text}'",
                )
                self.assertEqual(
                    result.edits,
                    [],
                    f"REGRESSÃO DE SEGURANÇA no caso {case['id']}: nenhuma "
                    f"edição deveria ter sido registrada para um caso "
                    f"'{case['case_type']}'",
                )


if __name__ == "__main__":
    unittest.main()
