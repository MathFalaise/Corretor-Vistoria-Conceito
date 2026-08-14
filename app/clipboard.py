"""Acesso explícito ao clipboard via QClipboard.

Sem monitoramento contínuo e sem atalhos globais: o clipboard só é
lido ou escrito em resposta direta a uma ação do usuário (clique em
"PROCESSAR CLIPBOARD" ou "COPIAR RESULTADO").
"""

from PySide6.QtWidgets import QApplication


def read_clipboard_text():
    """Lê o texto atual do clipboard, explicitamente, sob demanda."""
    clipboard = QApplication.clipboard()
    return clipboard.text()


def write_clipboard_text(text):
    """Escreve `text` no clipboard, explicitamente, sob demanda."""
    clipboard = QApplication.clipboard()
    clipboard.setText(text)
