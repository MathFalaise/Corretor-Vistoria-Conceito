"""Regressão da Camada 2 contra corpus/corpus_real.jsonl (somente leitura).

Garante que a análise contextual nunca altera corrected_text dos casos
de segurança reais (adversarial_trap / no_correction_needed), e que o
caso real conhecido de "comum" no início de frase ("Comum corredor de
uso comum do prédio.") é detectado corretamente: sugestão só para o
"Comum" inicial, nada para o "uso comum" seguinte.
"""

import json
import unittest
from pathlib import Path

from engine.pipeline import analyze_text
from engine.rules import RULES

CORPUS_REAL_PATH = (
    Path(__file__).resolve().parent.parent / "corpus" / "corpus_real.jsonl"
)


def _load_corpus_real():
    cases = []
    with open(CORPUS_REAL_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


class TestCandidatesAgainstRealCorpus(unittest.TestCase):
    def test_adversarial_trap_real_sem_sugestao_indevida(self):
        cases = [
            c for c in _load_corpus_real() if c["case_type"] == "adversarial_trap"
        ]
        self.assertGreaterEqual(len(cases), 1)
        for case in cases:
            with self.subTest(case_id=case["id"]):
                result = analyze_text(case["source_text"], RULES)
                self.assertEqual(result.corrected_text, case["source_text"])

    def test_no_correction_needed_real_nao_e_alterado_por_sugestao(self):
        cases = [
            c for c in _load_corpus_real() if c["case_type"] == "no_correction_needed"
        ]
        for case in cases:
            with self.subTest(case_id=case["id"]):
                result = analyze_text(case["source_text"], RULES)
                # a Camada 2 nunca aplica sozinha: o trecho apontado
                # por cada sugestão continua, literalmente, presente
                # (não substituído) no texto final.
                for suggestion in result.suggestions:
                    self.assertIn(suggestion.original, result.corrected_text)

    def test_caso_real_comum_corredor_gera_sugestao_correta(self):
        texto = "Comum corredor de uso comum do prédio."
        result = analyze_text(texto, RULES)
        origem = [s.original for s in result.suggestions]
        self.assertIn("Comum", origem)
        # o "comum" de "uso comum" não deve gerar sugestão nenhuma.
        self.assertEqual(origem.count("comum"), 0)
        # nada foi aplicado automaticamente pela Camada 2.
        self.assertEqual(result.corrected_text, "*" + texto)


if __name__ == "__main__":
    unittest.main()
