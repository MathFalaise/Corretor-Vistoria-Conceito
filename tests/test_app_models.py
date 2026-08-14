"""Testes de app/models.py: validação de código e InspectionSession."""

import unittest

from app.models import (
    INVALID_CODE_MESSAGE,
    InspectionSession,
    create_session,
    is_valid_inspection_code,
)


class TestInspectionCodeValidation(unittest.TestCase):
    def test_codigo_valido(self):
        self.assertTrue(is_valid_inspection_code("00959.002.02"))

    def test_codigo_invalido_formato_incompleto(self):
        self.assertFalse(is_valid_inspection_code("00959.002"))

    def test_codigo_invalido_letras(self):
        self.assertFalse(is_valid_inspection_code("ABCDE.002.02"))

    def test_codigo_invalido_separadores_errados(self):
        self.assertFalse(is_valid_inspection_code("00959-002-02"))

    def test_codigo_invalido_vazio(self):
        self.assertFalse(is_valid_inspection_code(""))

    def test_codigo_invalido_digitos_a_mais(self):
        self.assertFalse(is_valid_inspection_code("009599.002.02"))


class TestCreateSession(unittest.TestCase):
    def test_criacao_com_codigo_valido(self):
        session = create_session("00959.002.02")
        self.assertIsInstance(session, InspectionSession)
        self.assertEqual(session.inspection_code, "00959.002.02")
        self.assertEqual(session.current_room, "")
        self.assertEqual(session.current_component, "")
        self.assertEqual(session.last_source_text, "")
        self.assertIsNone(session.last_result)
        self.assertEqual(session.edits, [])

    def test_criacao_com_codigo_invalido_levanta_erro(self):
        with self.assertRaises(ValueError) as ctx:
            create_session("codigo-invalido")
        self.assertEqual(str(ctx.exception), INVALID_CODE_MESSAGE)


class TestInspectionSessionUpdates(unittest.TestCase):
    def test_atualizacao_de_room(self):
        session = create_session("00959.002.02")
        session.update_room("Quarto 01")
        self.assertEqual(session.current_room, "Quarto 01")

    def test_atualizacao_de_component(self):
        session = create_session("00959.002.02")
        session.update_component("Parede")
        self.assertEqual(session.current_component, "Parede")

    def test_atualizacao_faz_strip(self):
        session = create_session("00959.002.02")
        session.update_room("  Quarto 01  ")
        session.update_component("  Parede  ")
        self.assertEqual(session.current_room, "Quarto 01")
        self.assertEqual(session.current_component, "Parede")


if __name__ == "__main__":
    unittest.main()
