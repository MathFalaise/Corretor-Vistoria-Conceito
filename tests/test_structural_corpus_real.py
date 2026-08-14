"""Regressão da Camada 0 contra corpus/corpus_real.jsonl (somente leitura).

corpus_real.jsonl tem todos os casos com split="unreviewed" — ainda não
passou por curadoria. Mesmo assim, os casos de segurança
(adversarial_trap e no_correction_needed) já servem como guarda de
regressão: a normalização estrutural não pode alterá-los, com uma
única exceção documentada abaixo.
"""

import json
import re
import unittest
from pathlib import Path

from engine.structural import normalize_structural

CORPUS_REAL_PATH = (
    Path(__file__).resolve().parent.parent / "corpus" / "corpus_real.jsonl"
)

# Único caso, dentre os 37 reais, em que um no_correction_needed sem "*"
# recebe o marcador sob a nova regra. É um dado do lote de 2026-08-12,
# anterior à criação dos campos room/component e à convenção "*"
# consistente (ver auditoria) — não é um caso deliberadamente curado
# como o adversarial_trap, e sim uma inconsistência do dado
# "unreviewed" a ser revisada na curadoria do corpus. Documentado aqui
# explicitamente para não mascarar uma regressão real no futuro: se
# outro caso além deste passar a divergir, o teste abaixo aponta o
# culpado.
KNOWN_UNREVIEWED_INCONSISTENCY_ID = "df0b04ee-b6b3-4843-b954-963fa84cedb7"

# Único caso real que contém o resíduo "\nfim" — usado para validar que
# a remoção é o único conteúdo perdido nesse caso específico.
FIM_ARTIFACT_CASE_ID = "b6fef927-0b8a-42ad-b5e9-202b9982b081"


def _load_corpus_real():
    cases = []
    with open(CORPUS_REAL_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def _core(text):
    """Remove espaços e '*' para comparar apenas o conteúdo semântico."""
    return re.sub(r"[\s*]+", "", text)


class TestStructuralAgainstRealCorpus(unittest.TestCase):
    def test_corpus_real_existe_e_nao_esta_vazio(self):
        self.assertTrue(_load_corpus_real())

    def test_nao_lanca_excecao_em_nenhum_caso_real(self):
        for case in _load_corpus_real():
            with self.subTest(case_id=case["id"]):
                normalize_structural(case["source_text"])

    def test_preserva_conteudo_semantico_em_todo_o_corpus_real(self):
        """Fora espaço/'*'/o resíduo 'fim' conhecido, nada é perdido."""
        for case in _load_corpus_real():
            result = normalize_structural(case["source_text"])
            expected_core = _core(case["source_text"])
            if case["id"] == FIM_ARTIFACT_CASE_ID:
                expected_core = expected_core.replace("fim", "", 1)
            with self.subTest(case_id=case["id"]):
                self.assertEqual(_core(result.corrected_text), expected_core)

    def test_adversarial_trap_permanece_inalterado(self):
        cases = [
            c for c in _load_corpus_real() if c["case_type"] == "adversarial_trap"
        ]
        self.assertGreaterEqual(len(cases), 1, "esperado ao menos 1 adversarial_trap")
        for case in cases:
            with self.subTest(case_id=case["id"]):
                result = normalize_structural(case["source_text"])
                self.assertEqual(result.corrected_text, case["source_text"])
                self.assertEqual(result.edits, [])

    def test_no_correction_needed_permanece_inalterado(self):
        cases = [
            c for c in _load_corpus_real() if c["case_type"] == "no_correction_needed"
        ]
        self.assertGreaterEqual(len(cases), 1)
        for case in cases:
            result = normalize_structural(case["source_text"])
            if case["id"] == KNOWN_UNREVIEWED_INCONSISTENCY_ID:
                # Ver comentário no topo do arquivo.
                self.assertEqual(
                    result.corrected_text, "*" + case["source_text"]
                )
                continue
            with self.subTest(case_id=case["id"]):
                self.assertEqual(result.corrected_text, case["source_text"])
                self.assertEqual(result.edits, [])


if __name__ == "__main__":
    unittest.main()
