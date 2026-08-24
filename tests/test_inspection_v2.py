"""Testes de app/inspection_v2.py — estrutura de dados pura (sem Qt)."""

import unittest

from app.inspection_v2 import SECTION_GRID, SECTION_NAMES, RoomData


class TestSectionNames(unittest.TestCase):
    def test_exatamente_as_8_reparticoes_pedidas(self):
        self.assertEqual(
            list(SECTION_NAMES),
            [
                "PAREDE",
                "PISO",
                "TETO",
                "PORTA",
                "JANELA",
                "COMPONENTES ELÉTRICOS",
                "MOBÍLIA",
                "OBS",
            ],
        )

    def test_grid_tem_4_linhas_de_2_colunas(self):
        self.assertEqual(len(SECTION_GRID), 4)
        for row in SECTION_GRID:
            self.assertEqual(len(row), 2)


class TestRoomData(unittest.TestCase):
    def test_cria_com_todas_as_secoes_vazias(self):
        room = RoomData(name="CÔMODO 01")
        self.assertEqual(room.name, "CÔMODO 01")
        for section in SECTION_NAMES:
            self.assertEqual(room.sections[section], "")

    def test_secoes_de_duas_instancias_sao_independentes(self):
        room_a = RoomData(name="CÔMODO 01")
        room_b = RoomData(name="CÔMODO 02")
        room_a.sections["PAREDE"] = "Texto do cômodo A"
        self.assertEqual(room_b.sections["PAREDE"], "")


if __name__ == "__main__":
    unittest.main()
