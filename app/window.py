"""Interface gráfica (PySide6) do Corretor Vistoria.

Três telas em um QStackedWidget: Home -> Nova Vistoria -> Tela
Principal. Nenhuma posição absoluta / setGeometry(): tudo é layout
(QVBoxLayout, QHBoxLayout, QSplitter), responsivo por construção.

Esta é a única camada que conhece PySide6. Ela não importa o engine
diretamente nem duplica regras — todo processamento passa por
app.session.process_and_store.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.clipboard import read_clipboard_text, write_clipboard_text
from app.models import INVALID_CODE_MESSAGE, create_session, is_valid_inspection_code
from app.session import COPIED_MESSAGE, EMPTY_CLIPBOARD_MESSAGE, process_and_store

NARROW_WIDTH_THRESHOLD = 640


def _card(layout_cls=QVBoxLayout, spacing=12):
    """Cria um QFrame com objectName 'card' (estilizado em styles.py)."""
    frame = QFrame()
    frame.setObjectName("card")
    layout = layout_cls(frame)
    layout.setContentsMargins(28, 28, 28, 28)
    layout.setSpacing(spacing)
    return frame, layout


class HomeScreen(QWidget):
    """Tela inicial: título, subtítulo e botão NOVA VISTORIA."""

    start_requested = Signal()

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.addStretch(1)

        card, layout = _card()
        card.setMaximumWidth(480)

        title = QLabel("CORRETOR VISTORIA")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Processamento e normalização de transcrições de vistoria")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        start_button = QPushButton("NOVA VISTORIA")
        start_button.clicked.connect(self.start_requested)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(start_button)

        centered_row = QHBoxLayout()
        centered_row.addStretch(1)
        centered_row.addWidget(card)
        centered_row.addStretch(1)

        outer.addLayout(centered_row)
        outer.addStretch(1)


class NewInspectionScreen(QWidget):
    """Tela de entrada do código da vistoria, com validação de formato."""

    inspection_ready = Signal(str)

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.addStretch(1)

        card, layout = _card()
        card.setMaximumWidth(420)

        label = QLabel("Código da vistoria:")
        label.setObjectName("sectionLabel")

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("00000.000.00")
        self.code_input.returnPressed.connect(self._on_submit)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)

        submit_button = QPushButton("INICIAR VISTORIA")
        submit_button.clicked.connect(self._on_submit)

        layout.addWidget(label)
        layout.addWidget(self.code_input)
        layout.addWidget(self.error_label)
        layout.addWidget(submit_button)

        centered_row = QHBoxLayout()
        centered_row.addStretch(1)
        centered_row.addWidget(card)
        centered_row.addStretch(1)

        outer.addLayout(centered_row)
        outer.addStretch(1)

    def reset(self):
        self.code_input.clear()
        self.error_label.setVisible(False)

    def _on_submit(self):
        code = self.code_input.text()
        if not is_valid_inspection_code(code):
            self.error_label.setText(INVALID_CODE_MESSAGE)
            self.error_label.setVisible(True)
            return
        self.error_label.setVisible(False)
        self.inspection_ready.emit(code.strip())


class _ResponsiveSplitter(QSplitter):
    """QSplitter que alterna horizontal/vertical conforme a largura.

    Substitui a necessidade de posições absolutas: em telas largas os
    painéis ficam lado a lado, em telas estreitas ficam empilhados.
    """

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.size().width() < NARROW_WIDTH_THRESHOLD:
            self.setOrientation(Qt.Vertical)
        else:
            self.setOrientation(Qt.Horizontal)


class MainScreen(QWidget):
    """Tela principal: contexto da vistoria + processamento de clipboard."""

    new_inspection_requested = Signal()

    def __init__(self):
        super().__init__()
        self.session = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Cabeçalho: código da vistoria + campos de contexto.
        header_card, header_layout = _card(QVBoxLayout, spacing=10)

        self.inspection_label = QLabel("Vistoria:")
        self.inspection_label.setObjectName("inspectionCodeLabel")

        context_row = QHBoxLayout()
        context_row.setSpacing(16)

        room_col = QVBoxLayout()
        room_label = QLabel("Cômodo:")
        room_label.setObjectName("sectionLabel")
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("ex.: Quarto 01")
        self.room_input.textChanged.connect(self._on_room_changed)
        room_col.addWidget(room_label)
        room_col.addWidget(self.room_input)

        component_col = QVBoxLayout()
        component_label = QLabel("Parte do cômodo:")
        component_label.setObjectName("sectionLabel")
        self.component_input = QLineEdit()
        self.component_input.setPlaceholderText("ex.: Parede")
        self.component_input.textChanged.connect(self._on_component_changed)
        component_col.addWidget(component_label)
        component_col.addWidget(self.component_input)

        context_row.addLayout(room_col)
        context_row.addLayout(component_col)

        header_layout.addWidget(self.inspection_label)
        header_layout.addLayout(context_row)

        # Painéis de texto original / resultado, lado a lado ou empilhados.
        self.splitter = _ResponsiveSplitter(Qt.Horizontal)

        original_panel, original_layout = _card(QVBoxLayout)
        original_title = QLabel("TEXTO ORIGINAL")
        original_title.setObjectName("sectionLabel")
        self.original_text_edit = QTextEdit()
        self.original_text_edit.setPlaceholderText(
            "Copie o texto no CloudSLIM e clique em PROCESSAR CLIPBOARD."
        )
        self.process_button = QPushButton("PROCESSAR CLIPBOARD")
        self.process_button.clicked.connect(self._on_process_clipboard)
        original_layout.addWidget(original_title)
        original_layout.addWidget(self.original_text_edit)
        original_layout.addWidget(self.process_button)

        result_panel, result_layout = _card(QVBoxLayout)
        result_title = QLabel("RESULTADO")
        result_title.setObjectName("sectionLabel")
        self.result_text_edit = QTextEdit()
        self.copy_button = QPushButton("COPIAR RESULTADO")
        self.copy_button.clicked.connect(self._on_copy_result)
        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_text_edit)
        result_layout.addWidget(self.copy_button)

        for panel in (original_panel, result_panel):
            panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.splitter.addWidget(original_panel)
        self.splitter.addWidget(result_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        # Rodapé: status + nova vistoria.
        footer_row = QHBoxLayout()
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        new_inspection_button = QPushButton("NOVA VISTORIA")
        new_inspection_button.setObjectName("secondaryButton")
        new_inspection_button.clicked.connect(self.new_inspection_requested)

        footer_row.addWidget(self.status_label, stretch=1)
        footer_row.addWidget(new_inspection_button)

        root.addWidget(header_card)
        root.addWidget(self.splitter, stretch=1)
        root.addLayout(footer_row)

    def start_session(self, session):
        """Vincula uma nova InspectionSession à tela, limpando o estado visual."""
        self.session = session
        self.inspection_label.setText(f"Vistoria: {session.inspection_code}")
        self.room_input.setText(session.current_room)
        self.component_input.setText(session.current_component)
        self.original_text_edit.clear()
        self.result_text_edit.clear()
        self.status_label.setText("")

    def _on_room_changed(self, text):
        if self.session is not None:
            self.session.update_room(text)

    def _on_component_changed(self, text):
        if self.session is not None:
            self.session.update_component(text)

    def _on_process_clipboard(self):
        text = read_clipboard_text()
        if not text.strip():
            self.status_label.setText(EMPTY_CLIPBOARD_MESSAGE)
            return

        self.original_text_edit.setPlainText(text)
        result = process_and_store(self.session, text)
        self.result_text_edit.setPlainText(result.corrected_text)
        self.status_label.setText(
            f"Processado. {len(result.edits)} alteração(ões) aplicada(s)."
        )

    def _on_copy_result(self):
        write_clipboard_text(self.result_text_edit.toPlainText())
        self.status_label.setText(COPIED_MESSAGE)


class MainWindow(QMainWindow):
    """Janela principal, orquestra a navegação entre as três telas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Corretor Vistoria")
        self.resize(960, 640)
        self.setMinimumSize(420, 480)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_screen = HomeScreen()
        self.new_inspection_screen = NewInspectionScreen()
        self.main_screen = MainScreen()

        self.stack.addWidget(self.home_screen)
        self.stack.addWidget(self.new_inspection_screen)
        self.stack.addWidget(self.main_screen)

        self.home_screen.start_requested.connect(self._show_new_inspection)
        self.new_inspection_screen.inspection_ready.connect(self._start_inspection)
        self.main_screen.new_inspection_requested.connect(self._show_new_inspection)

        self.stack.setCurrentWidget(self.home_screen)

    def _show_new_inspection(self):
        self.new_inspection_screen.reset()
        self.stack.setCurrentWidget(self.new_inspection_screen)

    def _start_inspection(self, code):
        session = create_session(code)
        self.main_screen.start_session(session)
        self.stack.setCurrentWidget(self.main_screen)
