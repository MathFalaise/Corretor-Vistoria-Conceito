"""Testes da ferramenta de coleta de casos reais (tools/collect_case.py).

Testa apenas as funções puras (build_case, append_case). O loop
interativo (run_interactive) não é testado aqui por depender de input().
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.collect_case import append_case, build_case


class TestBuildCase(unittest.TestCase):
    def test_correction_valido(self):
        case = build_case(
            case_type="correction",
            source_text="comporta",
            target_text="com porta",
            session="sessao-1",
            notes="",
        )
        self.assertEqual(case["source_text"], "comporta")
        self.assertEqual(case["target_text"], "com porta")
        self.assertEqual(case["case_type"], "correction")
        self.assertEqual(case["edits"], [])
        self.assertEqual(case["split"], "unreviewed")
        self.assertTrue(case["id"])

    def test_correction_sem_target_falha(self):
        with self.assertRaises(ValueError):
            build_case(case_type="correction", source_text="comporta", target_text="")

    def test_no_correction_needed_usa_source_como_target(self):
        case = build_case(
            case_type="no_correction_needed",
            source_text="spot quadrado de sobrepor LED",
        )
        self.assertEqual(case["target_text"], "spot quadrado de sobrepor LED")

    def test_adversarial_trap_exige_notes(self):
        with self.assertRaises(ValueError):
            build_case(
                case_type="adversarial_trap",
                source_text="uso comum",
                notes="",
            )

    def test_adversarial_trap_valido(self):
        case = build_case(
            case_type="adversarial_trap",
            source_text="uso comum",
            notes="Não deve virar 'uso com um'.",
        )
        self.assertEqual(case["target_text"], "uso comum")
        self.assertEqual(case["notes"], "Não deve virar 'uso com um'.")

    def test_case_type_invalido_falha(self):
        with self.assertRaises(ValueError):
            build_case(case_type="invalido", source_text="texto")

    def test_source_text_vazio_falha(self):
        with self.assertRaises(ValueError):
            build_case(case_type="no_correction_needed", source_text="   ")

    def test_ids_sao_unicos(self):
        case_1 = build_case(case_type="no_correction_needed", source_text="a")
        case_2 = build_case(case_type="no_correction_needed", source_text="a")
        self.assertNotEqual(case_1["id"], case_2["id"])


class TestAppendCase(unittest.TestCase):
    def test_append_grava_jsonl_valido(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "corpus_real.jsonl"
            case_1 = build_case(case_type="no_correction_needed", source_text="a")
            case_2 = build_case(case_type="no_correction_needed", source_text="b")

            append_case(case_1, path)
            append_case(case_2, path)

            lines = path.read_text(encoding="utf-8").strip().split("\n")
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["source_text"], "a")
            self.assertEqual(json.loads(lines[1])["source_text"], "b")


if __name__ == "__main__":
    unittest.main()
