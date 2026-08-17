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
    QFileDialog,
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

from app.clipboard import write_clipboard_text
from app.models import (
    INVALID_CODE_MESSAGE,
    create_session,
    cursor_position_after_digit_count,
    extract_inspection_digits,
    format_inspection_code,
    is_valid_inspection_code,
)
from app.session import (
    COPIED_MESSAGE,
    approve_suggestion,
    process_and_store,
    reject_suggestion,
)
from pdf_import.importer import (
    DEFAULT_CORRECTED_DIR,
    DEFAULT_UNCORRECTED_DIR,
    run_import,
)

NARROW_WIDTH_THRESHOLD = 640
EMPTY_INPUT_MESSAGE = "Digite ou cole o texto para corrigir."


def _card(layout_cls=QVBoxLayout, spacing=12):
    """Cria um QFrame com objectName 'card' (estilizado em styles.py)."""
    frame = QFrame()
    frame.setObjectName("card")
    layout = layout_cls(frame)
    layout.setContentsMargins(28, 28, 28, 28)
    layout.setSpacing(spacing)
    return frame, layout


class HomeScreen(QWidget):
    """Tela inicial: título, subtítulo, NOVA VISTORIA e IMPORTAR PDFS."""

    start_requested = Signal()
    import_pdfs_requested = Signal()

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

        import_pdfs_button = QPushButton("IMPORTAR PDFS")
        import_pdfs_button.setObjectName("secondaryButton")
        import_pdfs_button.clicked.connect(self.import_pdfs_requested)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(start_button)
        layout.addWidget(import_pdfs_button)

        centered_row = QHBoxLayout()
        centered_row.addStretch(1)
        centered_row.addWidget(card)
        centered_row.addStretch(1)

        outer.addLayout(centered_row)
        outer.addStretch(1)


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

        self._formatting_code = False

        self.code_input = _InspectionCodeLineEdit()
        self.code_input.setPlaceholderText("00000.000.00")
        self.code_input.setMaxLength(12)  # 10 dígitos + 2 pontos
        self.code_input.textChanged.connect(self._on_code_text_changed)
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

    def _on_code_text_changed(self, text):
        """Formata o campo como 00000.000.00 enquanto o usuário digita
        ou cola texto: só dígitos, no máximo 10, pontos automáticos
        após o 5º e o 8º dígito, cursor preservado na posição certa."""
        if self._formatting_code:
            return

        digits = extract_inspection_digits(text)
        formatted = format_inspection_code(digits)
        if formatted == text:
            return

        cursor_pos = self.code_input.cursorPosition()
        digits_before_cursor = len(extract_inspection_digits(text[:cursor_pos]))

        self._formatting_code = True
        self.code_input.setText(formatted)
        self.code_input.setCursorPosition(
            cursor_position_after_digit_count(formatted, digits_before_cursor)
        )
        self._formatting_code = False

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
        original_title = QLabel("TEXTO DE ENTRADA")
        original_title.setObjectName("sectionLabel")
        self.original_text_edit = QTextEdit()
        self.original_text_edit.setPlaceholderText(
            "Cole ou digite aqui o texto do CloudSLIM."
        )
        self.process_button = QPushButton("CORRIGIR")
        self.process_button.clicked.connect(self._on_correct)
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

        # Sugestões da Camada 2 (análise contextual) — nunca aplicadas
        # sozinhas: cada uma só vira parte do resultado se aprovada.
        suggestions_card, suggestions_layout = _card(QVBoxLayout, spacing=8)
        suggestions_title = QLabel("SUGESTÕES")
        suggestions_title.setObjectName("sectionLabel")
        self.suggestions_empty_label = QLabel("Nenhuma sugestão pendente.")
        self.suggestions_empty_label.setObjectName("statusLabel")
        self.suggestions_rows_layout = QVBoxLayout()
        self.suggestions_rows_layout.setSpacing(8)

        suggestions_layout.addWidget(suggestions_title)
        suggestions_layout.addWidget(self.suggestions_empty_label)
        suggestions_layout.addLayout(self.suggestions_rows_layout)
        self.suggestions_card = suggestions_card

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
        root.addWidget(self.suggestions_card)
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
        self._render_suggestions([])

    def _on_room_changed(self, text):
        if self.session is not None:
            self.session.update_room(text)

    def _on_component_changed(self, text):
        if self.session is not None:
            self.session.update_component(text)

    def _on_correct(self):
        text = self.original_text_edit.toPlainText()
        if not text.strip():
            self.status_label.setText(EMPTY_INPUT_MESSAGE)
            return

        result = process_and_store(self.session, text)
        self.result_text_edit.setPlainText(result.corrected_text)
        self._render_suggestions(result.suggestions)
        self.status_label.setText(
            f"Processado. {len(result.edits)} alteração(ões) aplicada(s), "
            f"{len(result.suggestions)} sugestão(ões) para revisão."
        )

    def _on_copy_result(self):
        write_clipboard_text(self.result_text_edit.toPlainText())
        self.status_label.setText(COPIED_MESSAGE)

    def _render_suggestions(self, suggestions):
        """Redesenha a lista de sugestões pendentes."""
        while self.suggestions_rows_layout.count():
            item = self.suggestions_rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.suggestions_empty_label.setVisible(not suggestions)

        for suggestion in suggestions:
            self.suggestions_rows_layout.addWidget(
                self._build_suggestion_row(suggestion)
            )

    def _build_suggestion_row(self, suggestion):
        candidate = suggestion.candidates[0]

        row = QFrame()
        row_layout = QHBoxLayout(row)

        text_label = QLabel(
            f'"{suggestion.original}" → "{candidate.corrected}" '
            f"(confiança: {round(candidate.confidence * 100)}%)"
        )
        text_label.setWordWrap(True)

        approve_button = QPushButton("Aprovar")
        approve_button.clicked.connect(
            lambda checked=False, s=suggestion: self._on_approve_suggestion(s)
        )

        reject_button = QPushButton("Rejeitar")
        reject_button.setObjectName("secondaryButton")
        reject_button.clicked.connect(
            lambda checked=False, s=suggestion: self._on_reject_suggestion(s)
        )

        row_layout.addWidget(text_label, stretch=1)
        row_layout.addWidget(approve_button)
        row_layout.addWidget(reject_button)
        return row

    def _on_approve_suggestion(self, suggestion):
        candidate = suggestion.candidates[0]
        result = approve_suggestion(self.session, suggestion)
        self.result_text_edit.setPlainText(result.corrected_text)
        self._render_suggestions(result.suggestions)
        self.status_label.setText(
            f'Sugestão aprovada: "{suggestion.original}" → "{candidate.corrected}".'
        )

    def _on_reject_suggestion(self, suggestion):
        result = reject_suggestion(self.session, suggestion)
        self._render_suggestions(result.suggestions)
        self.status_label.setText(f'Sugestão rejeitada: "{suggestion.original}".')


class PdfImportScreen(QWidget):
    """Importação offline de PDFs de vistoria (não corrigidos/corrigidos).

    Só gera o dataset estruturado em data/extracted/ via
    pdf_import.importer.run_import — não altera o fluxo principal de
    correção (MainScreen) nem o corpus.
    """

    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.uncorrected_dir = DEFAULT_UNCORRECTED_DIR
        self.corrected_dir = DEFAULT_CORRECTED_DIR

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        title = QLabel("IMPORTAR PDFS DE VISTORIA")
        title.setObjectName("titleLabel")

        uncorrected_card, uncorrected_layout = _card(QHBoxLayout)
        uncorrected_label = QLabel("PDFs NÃO CORRIGIDOS:")
        uncorrected_label.setObjectName("sectionLabel")
        self.uncorrected_path_label = QLabel(self.uncorrected_dir)
        uncorrected_select_button = QPushButton("Selecionar pasta...")
        uncorrected_select_button.clicked.connect(self._on_select_uncorrected)
        uncorrected_layout.addWidget(uncorrected_label)
        uncorrected_layout.addWidget(self.uncorrected_path_label, stretch=1)
        uncorrected_layout.addWidget(uncorrected_select_button)

        corrected_card, corrected_layout = _card(QHBoxLayout)
        corrected_label = QLabel("PDFs CORRIGIDOS:")
        corrected_label.setObjectName("sectionLabel")
        self.corrected_path_label = QLabel(self.corrected_dir)
        corrected_select_button = QPushButton("Selecionar pasta...")
        corrected_select_button.clicked.connect(self._on_select_corrected)
        corrected_layout.addWidget(corrected_label)
        corrected_layout.addWidget(self.corrected_path_label, stretch=1)
        corrected_layout.addWidget(corrected_select_button)

        self.import_button = QPushButton("INICIAR IMPORTAÇÃO")
        self.import_button.clicked.connect(self._on_import)

        result_card, result_layout = _card(QVBoxLayout)
        result_title = QLabel("RESULTADO")
        result_title.setObjectName("sectionLabel")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_text)

        back_button = QPushButton("VOLTAR")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.back_requested)

        outer.addWidget(title)
        outer.addWidget(uncorrected_card)
        outer.addWidget(corrected_card)
        outer.addWidget(self.import_button)
        outer.addWidget(result_card, stretch=1)
        outer.addWidget(back_button)

    def _on_select_uncorrected(self):
        path = QFileDialog.getExistingDirectory(
            self, "Selecionar pasta de PDFs não corrigidos", self.uncorrected_dir
        )
        if path:
            self.uncorrected_dir = path
            self.uncorrected_path_label.setText(path)

    def _on_select_corrected(self):
        path = QFileDialog.getExistingDirectory(
            self, "Selecionar pasta de PDFs corrigidos", self.corrected_dir
        )
        if path:
            self.corrected_dir = path
            self.corrected_path_label.setText(path)

    def _on_import(self):
        summary = run_import(self.uncorrected_dir, self.corrected_dir)
        self.result_text.setPlainText(self._format_summary(summary))

    @staticmethod
    def _format_summary(summary):
        lines = [f"Importados: {len(summary.imported)}", "", "Códigos identificados:"]
        for item in summary.imported:
            codigo = item.inspection_code or "(não identificado)"
            lines.append(f"  - {item.source_file}: {codigo}")

        lines.append("")
        lines.append(f"Pares encontrados ({len(summary.paired_codes)}):")
        for code in summary.paired_codes:
            lines.append(f"  - {code}")

        lines.append("")
        lines.append("PDFs sem par:")
        for code in summary.unpaired_uncorrected:
            lines.append(f"  - {code} (só em não corrigidos)")
        for code in summary.unpaired_corrected:
            lines.append(f"  - {code} (só em corrigidos)")

        if summary.no_code_detected:
            lines.append("")
            lines.append("Sem código identificado:")
            for source_file in summary.no_code_detected:
                lines.append(f"  - {source_file}")

        if summary.errors:
            lines.append("")
            lines.append("Erros de leitura:")
            for source_file, message in summary.errors:
                lines.append(f"  - {source_file}: {message}")

        return "\n".join(lines)


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
        self.pdf_import_screen = PdfImportScreen()

        self.stack.addWidget(self.home_screen)
        self.stack.addWidget(self.new_inspection_screen)
        self.stack.addWidget(self.main_screen)
        self.stack.addWidget(self.pdf_import_screen)

        self.home_screen.start_requested.connect(self._show_new_inspection)
        self.home_screen.import_pdfs_requested.connect(self._show_pdf_import)
        self.new_inspection_screen.inspection_ready.connect(self._start_inspection)
        self.main_screen.new_inspection_requested.connect(self._show_new_inspection)
        self.pdf_import_screen.back_requested.connect(self._show_home)

        self.stack.setCurrentWidget(self.home_screen)

    def _show_home(self):
        self.stack.setCurrentWidget(self.home_screen)

    def _show_new_inspection(self):
        self.new_inspection_screen.reset()
        self.stack.setCurrentWidget(self.new_inspection_screen)

    def _show_pdf_import(self):
        self.stack.setCurrentWidget(self.pdf_import_screen)

    def _start_inspection(self, code):
        session = create_session(code)
        self.main_screen.start_session(session)
        self.stack.setCurrentWidget(self.main_screen)
