"""V2 — reestruturação da interface: navegação inicial (Corrigir
Vistoria / Vistoria Jean) e o novo layout de "Corrigir Vistoria" (aba
por cômodo, 8 repartições fixas).

Só interface e navegação — nenhuma ligação com engine/ ainda. O botão
"CORRIGIR" existe visualmente mas não chama o motor de propósito (ver
CorrigirVistoriaScreen._on_correct_clicked). Reaproveita _card e
_InspectionCodeLineEdit de app.window em vez de recriá-los.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.inspection_v2 import SECTION_GRID, RoomData
from app.widgets import _card, _InspectionCodeLineEdit, connect_inspection_code_formatting

INITIAL_ROOM_COUNT = 5


class V2HomeScreen(QWidget):
    """Primeira tela do app: "Corrigir Vistoria" ou "Vistoria Jean"."""

    corrigir_vistoria_requested = Signal()
    vistoria_jean_requested = Signal()

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.addStretch(1)

        card, layout = _card()
        card.setMaximumWidth(480)

        title = QLabel("CORRETOR VISTORIA")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Selecione o tipo de vistoria")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)

        corrigir_button = QPushButton("CORRIGIR VISTORIA")
        corrigir_button.clicked.connect(self.corrigir_vistoria_requested)

        vistoria_jean_button = QPushButton("VISTORIA JEAN")
        vistoria_jean_button.setObjectName("secondaryButton")
        vistoria_jean_button.clicked.connect(self.vistoria_jean_requested)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(corrigir_button)
        layout.addWidget(vistoria_jean_button)

        centered_row = QHBoxLayout()
        centered_row.addStretch(1)
        centered_row.addWidget(card)
        centered_row.addStretch(1)

        outer.addLayout(centered_row)
        outer.addStretch(1)


class VistoriaJeanScreen(QWidget):
    """Placeholder: só navegação, layout ainda não implementado.

    Preparado para receber o PNG "Layout Jean" e as regras específicas
    numa etapa futura.
    """

    back_requested = Signal()

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.addStretch(1)

        card, layout = _card()
        card.setMaximumWidth(480)

        title = QLabel("VISTORIA JEAN")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        message = QLabel("Layout ainda não implementado nesta etapa.")
        message.setObjectName("subtitleLabel")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)

        back_button = QPushButton("VOLTAR")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_requested)

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addSpacing(8)
        layout.addWidget(back_button)

        centered_row = QHBoxLayout()
        centered_row.addStretch(1)
        centered_row.addWidget(card)
        centered_row.addStretch(1)

        outer.addLayout(centered_row)
        outer.addStretch(1)


def _build_room_tab(room):
    """Monta o conteúdo de uma aba de cômodo: grid 2x4 das 8
    repartições fixas, cada uma com rótulo + área de texto editável.

    Guarda os QTextEdit em `widget.section_edits` (nome -> QTextEdit)
    — é o ponto de leitura/escrita que uma etapa futura vai usar para
    ligar o motor de correção, sem precisar redesenhar a tela.
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)

    container = QWidget()
    grid = QGridLayout(container)
    grid.setContentsMargins(4, 4, 4, 4)
    grid.setHorizontalSpacing(16)
    grid.setVerticalSpacing(12)

    section_edits = {}
    for row_index, row_names in enumerate(SECTION_GRID):
        for col_index, section_name in enumerate(row_names):
            box, box_layout = _card(QVBoxLayout, spacing=4)
            label = QLabel(section_name)
            label.setObjectName("sectionLabel")
            text_edit = QTextEdit()
            text_edit.setPlainText(room.sections.get(section_name, ""))
            text_edit.setMinimumHeight(70)
            box_layout.addWidget(label)
            box_layout.addWidget(text_edit)
            grid.addWidget(box, row_index, col_index)
            section_edits[section_name] = text_edit

    scroll.setWidget(container)
    scroll.section_edits = section_edits
    scroll.room_data = room
    return scroll


class CorrigirVistoriaScreen(QWidget):
    """Layout "Corrigir Vistoria": código no topo, abas de cômodo,
    8 repartições fixas por cômodo, botão CORRIGIR ao final.

    Nenhuma correção é executada aqui ainda — CORRIGIR é um placeholder
    de propósito (ver _on_correct_clicked).
    """

    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self._room_counter = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        top_row = QHBoxLayout()
        back_button = QPushButton("← Voltar")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_requested)
        top_row.addWidget(back_button)
        top_row.addStretch(1)

        code_card, code_layout = _card(QVBoxLayout, spacing=4)
        code_label = QLabel("CÓDIGO DE VISTORIA")
        code_label.setObjectName("sectionLabel")
        self.code_input = _InspectionCodeLineEdit()
        self.code_input.setPlaceholderText("00000.000.00")
        self.code_input.setMaxLength(12)
        connect_inspection_code_formatting(self.code_input)
        code_layout.addWidget(code_label)
        code_layout.addWidget(self.code_input)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._on_close_room_tab)

        add_room_button = QPushButton("+")
        add_room_button.setFixedWidth(32)
        add_room_button.clicked.connect(self._on_add_room)
        self.tabs.setCornerWidget(add_room_button, Qt.TopRightCorner)

        for _ in range(INITIAL_ROOM_COUNT):
            self._add_room_tab()

        correct_button = QPushButton("CORRIGIR")
        correct_button.clicked.connect(self._on_correct_clicked)
        correct_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(correct_button)
        button_row.addStretch(1)

        outer.addLayout(top_row)
        outer.addWidget(code_card)
        outer.addWidget(self.tabs, stretch=1)
        outer.addLayout(button_row)

    def _next_room_name(self):
        self._room_counter += 1
        return f"CÔMODO {self._room_counter:02d}"

    def _add_room_tab(self):
        room = RoomData(name=self._next_room_name())
        tab_content = _build_room_tab(room)
        index = self.tabs.addTab(tab_content, room.name)
        self.tabs.setCurrentIndex(index)
        return index

    def _on_add_room(self):
        self._add_room_tab()

    def _on_close_room_tab(self, index):
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if widget is not None:
            widget.deleteLater()

    def get_room_texts(self, tab_index):
        """{NOME_REPARTIÇÃO: texto} do cômodo na aba `tab_index`.

        Ponto de leitura para a etapa futura de integração com o
        motor — nada chama o motor a partir daqui ainda.
        """
        widget = self.tabs.widget(tab_index)
        if widget is None:
            return {}
        return {name: edit.toPlainText() for name, edit in widget.section_edits.items()}

    def set_room_text(self, tab_index, section_name, text):
        """Escreve `text` na repartição `section_name` do cômodo na
        aba `tab_index`. Ponto de escrita para uma etapa futura (ex.:
        popular a partir de um PDF importado) — não usado ainda."""
        widget = self.tabs.widget(tab_index)
        if widget is not None and section_name in widget.section_edits:
            widget.section_edits[section_name].setPlainText(text)

    def _on_correct_clicked(self):
        """Placeholder proposital: a próxima etapa conecta isto ao
        motor de correção (engine.pipeline.analyze_text), repartição
        por repartição. Nada acontece ainda."""
        pass
