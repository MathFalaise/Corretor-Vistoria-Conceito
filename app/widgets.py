"""Widgets PySide6 compartilhados entre app/window.py e app/window_v2.py.

Extraído para cá (sem alterar comportamento) para evitar import
circular: window_v2.py precisa reaproveitar _card/_InspectionCodeLineEdit,
e window.py precisa importar as telas de window_v2.py — se um
importasse o outro diretamente, o carregamento do módulo travaria.
Este módulo não depende de nenhum dos dois.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLineEdit, QVBoxLayout

from app.models import (
    cursor_position_after_digit_count,
    extract_inspection_digits,
    format_inspection_code,
)


def _card(layout_cls=QVBoxLayout, spacing=12):
    """Cria um QFrame com objectName 'card' (estilizado em styles.py)."""
    frame = QFrame()
    frame.setObjectName("card")
    layout = layout_cls(frame)
    layout.setContentsMargins(28, 28, 28, 28)
    layout.setSpacing(spacing)
    return frame, layout


class _InspectionCodeLineEdit(QLineEdit):
    """QLineEdit do código da vistoria.

    A filtragem de caracteres e a inserção automática dos pontos vêm de
    NewInspectionScreen._on_code_text_changed (via sinal textChanged).
    Esta subclasse só existe para Backspace/Delete: sem ela, apagar o
    caractere logo antes/depois de um ponto automático (ex.: o ponto de
    "00000.") faria o handler de textChanged reinserir o mesmo ponto
    imediatamente, e o campo pareceria "travado". Aqui a remoção é
    feita em termos de dígitos, não de caracteres — sempre remove um
    dígito de verdade, mantendo a formatação consistente.
    """

    def keyPressEvent(self, event):
        if not self.hasSelectedText() and event.key() in (
            Qt.Key_Backspace,
            Qt.Key_Delete,
        ):
            if self._delete_one_digit(event.key()):
                return
        super().keyPressEvent(event)

    def _delete_one_digit(self, key):
        text = self.text()
        cursor_pos = self.cursorPosition()
        digits = extract_inspection_digits(text)
        digit_index = len(extract_inspection_digits(text[:cursor_pos]))

        if key == Qt.Key_Backspace:
            if digit_index == 0:
                return False
            new_digits = digits[: digit_index - 1] + digits[digit_index:]
            new_digit_count = digit_index - 1
        else:
            if digit_index >= len(digits):
                return False
            new_digits = digits[:digit_index] + digits[digit_index + 1 :]
            new_digit_count = digit_index

        formatted = format_inspection_code(new_digits)
        self.setText(formatted)
        self.setCursorPosition(
            cursor_position_after_digit_count(formatted, new_digit_count)
        )
        return True


def connect_inspection_code_formatting(line_edit):
    """Liga a formatação automática (00000.000.00) a um QLineEdit —
    normalmente um _InspectionCodeLineEdit, para o Backspace/Delete
    também funcionarem corretamente. Reaproveitável por qualquer tela
    que precise do campo de código (ex.: app.window_v2).

    V1 (NewInspectionScreen, em app/window.py) mantém sua própria cópia
    equivalente deste handler — não foi retocada nesta etapa para não
    alterar um fluxo já testado sem necessidade.
    """
    state = {"formatting": False}

    def _on_text_changed(text):
        if state["formatting"]:
            return
        digits = extract_inspection_digits(text)
        formatted = format_inspection_code(digits)
        if formatted == text:
            return

        cursor_pos = line_edit.cursorPosition()
        digits_before_cursor = len(extract_inspection_digits(text[:cursor_pos]))

        state["formatting"] = True
        line_edit.setText(formatted)
        line_edit.setCursorPosition(
            cursor_position_after_digit_count(formatted, digits_before_cursor)
        )
        state["formatting"] = False

    line_edit.textChanged.connect(_on_text_changed)
