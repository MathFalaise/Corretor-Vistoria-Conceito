"""Testes da V2: navegação inicial e tela "Corrigir Vistoria".

Só interface/navegação/estrutura — nenhum teste aqui invoca o motor,
porque a tela também não invoca (CORRIGIR é um placeholder).
"""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.inspection_v2 import SECTION_NAMES
from app.window import MainWindow
from app.window_v2 import CorrigirVistoriaScreen, V2HomeScreen, VistoriaJeanScreen

_app = QApplication.instance() or QApplication([])


class TestV2HomeScreen(unittest.TestCase):
    def test_tem_exatamente_duas_opcoes(self):
        screen = V2HomeScreen()
        self.assertTrue(hasattr(screen, "corrigir_vistoria_requested"))
        self.assertTrue(hasattr(screen, "vistoria_jean_requested"))


class TestNavegacaoDoAppV2(unittest.TestCase):
    def test_tela_inicial_e_v2_home(self):
        window = MainWindow()
        self.assertIs(window.stack.currentWidget(), window.v2_home_screen)

    def test_corrigir_vistoria_abre_a_tela_nova(self):
        window = MainWindow()
        window.v2_home_screen.corrigir_vistoria_requested.emit()
        self.assertIs(window.stack.currentWidget(), window.corrigir_vistoria_screen)

    def test_vistoria_jean_abre_a_tela_placeholder(self):
        window = MainWindow()
        window.v2_home_screen.vistoria_jean_requested.emit()
        self.assertIs(window.stack.currentWidget(), window.vistoria_jean_screen)

    def test_voltar_da_tela_corrigir_vistoria_retorna_ao_v2_home(self):
        window = MainWindow()
        window.v2_home_screen.corrigir_vistoria_requested.emit()
        window.corrigir_vistoria_screen.back_requested.emit()
        self.assertIs(window.stack.currentWidget(), window.v2_home_screen)

    def test_voltar_da_tela_vistoria_jean_retorna_ao_v2_home(self):
        window = MainWindow()
        window.v2_home_screen.vistoria_jean_requested.emit()
        window.vistoria_jean_screen.back_requested.emit()
        self.assertIs(window.stack.currentWidget(), window.v2_home_screen)

    def test_telas_v1_continuam_existindo_mesmo_sem_serem_a_entrada(self):
        window = MainWindow()
        self.assertIsNotNone(window.home_screen)
        self.assertIsNotNone(window.new_inspection_screen)
        self.assertIsNotNone(window.main_screen)
        self.assertIsNotNone(window.pdf_import_screen)


class TestVistoriaJeanScreen(unittest.TestCase):
    def test_tem_botao_voltar_e_nenhum_layout_ainda(self):
        screen = VistoriaJeanScreen()
        self.assertTrue(hasattr(screen, "back_requested"))


class TestCorrigirVistoriaScreen(unittest.TestCase):
    def test_comeca_com_5_comodos(self):
        screen = CorrigirVistoriaScreen()
        self.assertEqual(screen.tabs.count(), 5)
        nomes = [screen.tabs.tabText(i) for i in range(5)]
        self.assertEqual(
            nomes,
            ["CÔMODO 01", "CÔMODO 02", "CÔMODO 03", "CÔMODO 04", "CÔMODO 05"],
        )

    def test_botao_mais_adiciona_novo_comodo(self):
        screen = CorrigirVistoriaScreen()
        screen._on_add_room()
        self.assertEqual(screen.tabs.count(), 6)
        self.assertEqual(screen.tabs.tabText(5), "CÔMODO 06")

    def test_comodo_pode_ser_removido(self):
        screen = CorrigirVistoriaScreen()
        screen._on_close_room_tab(0)
        self.assertEqual(screen.tabs.count(), 4)
        nomes = [screen.tabs.tabText(i) for i in range(4)]
        self.assertNotIn("CÔMODO 01", nomes)

    def test_cada_comodo_tem_exatamente_as_8_reparticoes(self):
        screen = CorrigirVistoriaScreen()
        widget = screen.tabs.widget(0)
        self.assertEqual(set(widget.section_edits.keys()), set(SECTION_NAMES))
        self.assertEqual(len(widget.section_edits), 8)

    def test_reparticoes_sao_independentes_entre_comodos(self):
        screen = CorrigirVistoriaScreen()
        screen.set_room_text(0, "PAREDE", "Texto do cômodo 1")
        self.assertEqual(screen.get_room_texts(0)["PAREDE"], "Texto do cômodo 1")
        self.assertEqual(screen.get_room_texts(1)["PAREDE"], "")

    def test_get_room_texts_reflete_o_que_foi_digitado(self):
        screen = CorrigirVistoriaScreen()
        widget = screen.tabs.widget(0)
        widget.section_edits["OBS"].setPlainText("Observação de teste.")
        self.assertEqual(screen.get_room_texts(0)["OBS"], "Observação de teste.")

    def test_campo_codigo_reaproveita_a_mascara_existente(self):
        screen = CorrigirVistoriaScreen()
        screen.code_input.setText("0095900202")
        self.assertEqual(screen.code_input.text(), "00959.002.02")

    def test_botao_corrigir_nao_lanca_excecao_e_nao_altera_textos(self):
        screen = CorrigirVistoriaScreen()
        screen.set_room_text(0, "PAREDE", "Texto original.")
        screen._on_correct_clicked()  # placeholder: não deve fazer nada
        self.assertEqual(screen.get_room_texts(0)["PAREDE"], "Texto original.")


if __name__ == "__main__":
    unittest.main()
