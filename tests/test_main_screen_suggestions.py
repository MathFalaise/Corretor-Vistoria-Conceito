"""Testes de fluxo completo: MainScreen conectada à Camada 2.

Cobre exatamente o roteiro pedido: caso real do corpus, rejeição,
múltiplas sugestões, texto sem sugestões, texto já correto, "Corrigir"
sem texto, e "Copiar resultado".
"""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.models import create_session
from app.window import MainScreen

_app = QApplication.instance() or QApplication([])


def _screen_with_session():
    screen = MainScreen()
    screen.start_session(create_session("00959.002.02"))
    # .show() é necessário para que isVisible() reflita setVisible():
    # um widget nunca exibido sempre reporta isVisible() == False,
    # independente do estado interno que os testes verificam.
    screen.show()
    return screen


class TestCasoRealComumCorredor(unittest.TestCase):
    """source: "Comum corredor de uso comum do prédio." — caso do
    diagnóstico anterior."""

    def test_gera_sugestao_para_o_primeiro_comum_apenas(self):
        screen = _screen_with_session()
        screen.original_text_edit.setPlainText(
            "Comum corredor de uso comum do prédio."
        )
        screen.process_button.click()

        suggestions = screen.session.last_result.suggestions
        origem = [s.original for s in suggestions]
        self.assertIn("Comum", origem)
        self.assertEqual(origem.count("comum"), 0)  # "uso comum" protegido

        # um item foi renderizado na lista de pendências.
        self.assertEqual(screen.suggestions_rows_layout.count(), len(suggestions))
        self.assertFalse(screen.suggestions_empty_label.isVisible())

    def test_aprovar_produz_o_resultado_esperado(self):
        screen = _screen_with_session()
        screen.original_text_edit.setPlainText(
            "Comum corredor de uso comum do prédio."
        )
        screen.process_button.click()

        suggestion = next(
            s for s in screen.session.last_result.suggestions if s.original == "Comum"
        )
        screen._on_approve_suggestion(suggestion)

        self.assertEqual(
            screen.result_text_edit.toPlainText(),
            "*Com um corredor de uso comum do prédio.",
        )
        # a sugestão aprovada some da lista de pendências.
        self.assertNotIn(suggestion, screen.session.last_result.suggestions)
        self.assertTrue(screen.suggestions_empty_label.isVisible())


class TestRejeicao(unittest.TestCase):
    def test_rejeitar_nao_altera_resultado_e_remove_da_lista(self):
        screen = _screen_with_session()
        screen.original_text_edit.setPlainText(
            "Comum corredor de uso comum do prédio."
        )
        screen.process_button.click()

        texto_antes = screen.result_text_edit.toPlainText()
        suggestion = screen.session.last_result.suggestions[0]

        screen._on_reject_suggestion(suggestion)

        self.assertEqual(screen.result_text_edit.toPlainText(), texto_antes)
        self.assertNotIn(suggestion, screen.session.last_result.suggestions)


class TestMultiplasSugestoes(unittest.TestCase):
    def test_duas_sugestoes_independentes(self):
        screen = _screen_with_session()
        screen.original_text_edit.setPlainText(
            "Apresenta comjardim. Comum acesso ao corredor."
        )
        screen.process_button.click()

        suggestions = screen.session.last_result.suggestions
        self.assertGreaterEqual(len(suggestions), 2)
        self.assertEqual(screen.suggestions_rows_layout.count(), len(suggestions))

        # aprova só a primeira; a outra continua pendente.
        primeira = suggestions[0]
        screen._on_approve_suggestion(primeira)
        self.assertEqual(len(screen.session.last_result.suggestions), len(suggestions) - 1)
        self.assertFalse(screen.suggestions_empty_label.isVisible())


class TestTextoSemSugestoes(unittest.TestCase):
    def test_texto_sem_padrao_nao_gera_sugestao(self):
        screen = _screen_with_session()
        screen.original_text_edit.setPlainText("Piso em porcelanato, sem avarias.")
        screen.process_button.click()

        self.assertEqual(screen.session.last_result.suggestions, [])
        self.assertTrue(screen.suggestions_empty_label.isVisible())
        self.assertEqual(screen.suggestions_rows_layout.count(), 0)


class TestTextoJaCorreto(unittest.TestCase):
    def test_texto_ja_formatado_permanece_igual(self):
        screen = _screen_with_session()
        texto = "*Piso em porcelanato, sem avarias."
        screen.original_text_edit.setPlainText(texto)
        screen.process_button.click()

        self.assertEqual(screen.result_text_edit.toPlainText(), texto)
        self.assertEqual(screen.session.last_result.edits, [])
        self.assertEqual(screen.session.last_result.suggestions, [])


class TestCorrigirSemTexto(unittest.TestCase):
    def test_corrigir_com_campo_vazio_mostra_status_e_nao_processa(self):
        screen = _screen_with_session()
        screen.process_button.click()

        self.assertEqual(screen.result_text_edit.toPlainText(), "")
        self.assertEqual(screen.status_label.text(), "Digite ou cole o texto para corrigir.")
        self.assertIsNone(screen.session.last_result)


class TestCopiarResultado(unittest.TestCase):
    def test_copiar_resultado_nao_reprocessa(self):
        screen = _screen_with_session()
        screen.original_text_edit.setPlainText("Piso em porcelanato, sem avarias.")
        screen.process_button.click()

        texto_resultado = screen.result_text_edit.toPlainText()
        screen.copy_button.click()

        self.assertEqual(screen.result_text_edit.toPlainText(), texto_resultado)
        self.assertEqual(_app.clipboard().text(), texto_resultado)
        self.assertEqual(screen.status_label.text(), "Resultado copiado para o clipboard.")


if __name__ == "__main__":
    unittest.main()
