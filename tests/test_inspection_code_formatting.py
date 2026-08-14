"""Testes da formatação automática do campo "Código da vistoria".

Cobre tanto as funções puras (app/models.py) quanto o comportamento do
próprio campo QLineEdit (app/window.py::NewInspectionScreen), incluindo
digitação, colagem, letras/símbolos, 11º dígito e backspace.

Não toca em nenhum outro campo, no motor, no corpus ou em regras de
correção — só no campo de código da vistoria.
"""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.models import (
    INVALID_CODE_MESSAGE,
    cursor_position_after_digit_count,
    extract_inspection_digits,
    format_inspection_code,
)
from app.window import NewInspectionScreen

_app = QApplication.instance() or QApplication([])


class TestFormatInspectionCodePure(unittest.TestCase):
    def test_progressao_exata_do_enunciado(self):
        progressao = [
            ("0", "0"),
            ("00", "00"),
            ("000", "000"),
            ("0000", "0000"),
            ("00000", "00000."),
            ("000000", "00000.0"),
            ("0000000", "00000.00"),
            ("00000000", "00000.000."),
            ("000000000", "00000.000.0"),
            ("0000000000", "00000.000.00"),
        ]
        for digits, esperado in progressao:
            with self.subTest(digits=digits):
                self.assertEqual(format_inspection_code(digits), esperado)


class TestExtractInspectionDigits(unittest.TestCase):
    def test_remove_pontos(self):
        self.assertEqual(extract_inspection_digits("00959.002.02"), "0095900202")

    def test_remove_letras_e_simbolos(self):
        self.assertEqual(extract_inspection_digits("a0b0-9!5@9#0$0%2^0&2"), "0095900202")

    def test_remove_espacos(self):
        self.assertEqual(extract_inspection_digits("0 0 9 5 9 0 0 2 0 2"), "0095900202")

    def test_limita_a_10_digitos(self):
        self.assertEqual(extract_inspection_digits("00959002021"), "0095900202")
        self.assertEqual(len(extract_inspection_digits("999999999999999")), 10)


class TestCursorPositionAfterDigitCount(unittest.TestCase):
    def test_pula_ponto_apos_5_digitos(self):
        formatted = "00000."
        self.assertEqual(cursor_position_after_digit_count(formatted, 5), 6)

    def test_pula_ponto_apos_8_digitos(self):
        formatted = "00000.000."
        self.assertEqual(cursor_position_after_digit_count(formatted, 8), 10)

    def test_posicao_no_meio_sem_ponto_adjacente(self):
        formatted = "00000.000.02"
        self.assertEqual(cursor_position_after_digit_count(formatted, 6), 7)

    def test_zero_digitos_retorna_inicio(self):
        self.assertEqual(cursor_position_after_digit_count("00000.", 0), 0)


class TestCampoDigitacao(unittest.TestCase):
    """Simula digitação real, tecla a tecla, no QLineEdit do campo."""

    def setUp(self):
        self.screen = NewInspectionScreen()

    def test_digitacao_progressiva_completa(self):
        estados_esperados = [
            "0",
            "00",
            "000",
            "0000",
            "00000.",
            "00000.0",
            "00000.00",
            "00000.000.",
            "00000.000.0",
            "00000.000.00",
        ]
        for digito, esperado in zip("0000000000", estados_esperados):
            QTest.keyClicks(self.screen.code_input, digito)
            self.assertEqual(self.screen.code_input.text(), esperado)

    def test_resultado_final_da_digitacao(self):
        QTest.keyClicks(self.screen.code_input, "0095900202")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")


class TestCampoColagem(unittest.TestCase):
    """Colar (setText programático, como o Qt faz ao colar do clipboard)."""

    def setUp(self):
        self.screen = NewInspectionScreen()

    def test_cola_10_digitos_puros(self):
        self.screen.code_input.setText("0095900202")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")

    def test_cola_ja_formatado(self):
        self.screen.code_input.setText("00959.002.02")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")

    def test_cola_com_11_digitos_ignora_o_ultimo(self):
        self.screen.code_input.setText("00959002021")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")

    def test_cola_com_letras_e_simbolos_misturados(self):
        self.screen.code_input.setText("00959-002/02abc")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")


class TestCampoRejeitaLetrasESimbolos(unittest.TestCase):
    def setUp(self):
        self.screen = NewInspectionScreen()

    def test_letras_digitadas_sao_ignoradas(self):
        QTest.keyClicks(self.screen.code_input, "abc00959xyz00202")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")

    def test_simbolos_digitados_sao_ignorados(self):
        QTest.keyClicks(self.screen.code_input, "00-959.002/02")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")

    def test_espacos_digitados_sao_ignorados(self):
        QTest.keyClicks(self.screen.code_input, "00 959 002 02")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")


class TestDecimoPrimeiroDigitoBloqueado(unittest.TestCase):
    def setUp(self):
        self.screen = NewInspectionScreen()

    def test_11o_digito_digitado_nao_e_aceito(self):
        QTest.keyClicks(self.screen.code_input, "00959002021")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")

    def test_digitos_apos_completo_continuam_bloqueados(self):
        QTest.keyClicks(self.screen.code_input, "0095900202")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")
        QTest.keyClicks(self.screen.code_input, "999")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")


class TestBackspace(unittest.TestCase):
    def setUp(self):
        self.screen = NewInspectionScreen()

    def test_backspace_remove_ultimo_digito_e_reformata(self):
        QTest.keyClicks(self.screen.code_input, "0095900202")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")

        QTest.keyClick(self.screen.code_input, Qt.Key_Backspace)
        self.assertEqual(self.screen.code_input.text(), "00959.002.0")

        QTest.keyClick(self.screen.code_input, Qt.Key_Backspace)
        self.assertEqual(self.screen.code_input.text(), "00959.002.")

    def test_backspace_atravessa_o_ponto_automatico(self):
        QTest.keyClicks(self.screen.code_input, "00000")
        self.assertEqual(self.screen.code_input.text(), "00000.")

        # backspace no fim de "00000." remove o dígito, não só o ponto
        # (o ponto é reconstruído/removido automaticamente).
        QTest.keyClick(self.screen.code_input, Qt.Key_Backspace)
        self.assertEqual(self.screen.code_input.text(), "0000")

    def test_backspace_ate_campo_vazio_permite_digitar_de_novo(self):
        QTest.keyClicks(self.screen.code_input, "0095900202")
        for _ in range(12):
            QTest.keyClick(self.screen.code_input, Qt.Key_Backspace)
        self.assertEqual(self.screen.code_input.text(), "")

        QTest.keyClicks(self.screen.code_input, "0095900202")
        self.assertEqual(self.screen.code_input.text(), "00959.002.02")


class TestOutrosComportamentosNaoForamAlterados(unittest.TestCase):
    """Garante que só o campo de código foi tocado: submit/erro seguem
    funcionando exatamente como antes."""

    def test_submit_com_codigo_valido_emite_sinal(self):
        screen = NewInspectionScreen()
        recebido = []
        screen.inspection_ready.connect(recebido.append)

        QTest.keyClicks(screen.code_input, "0095900202")
        screen._on_submit()

        self.assertEqual(recebido, ["00959.002.02"])

    def test_submit_incompleto_mostra_erro(self):
        # a tela nunca é exibida (.show()) neste teste, então
        # isVisible() sempre seria False independente do bug — a
        # asserção correta é sobre o texto de erro definido.
        screen = NewInspectionScreen()
        QTest.keyClicks(screen.code_input, "00959")  # só 5 dígitos -> "00959."
        screen._on_submit()
        self.assertEqual(screen.error_label.text(), INVALID_CODE_MESSAGE)

    def test_reset_limpa_campo(self):
        screen = NewInspectionScreen()
        QTest.keyClicks(screen.code_input, "0095900202")
        screen.reset()
        self.assertEqual(screen.code_input.text(), "")
        self.assertFalse(screen.error_label.isVisible())


if __name__ == "__main__":
    unittest.main()
