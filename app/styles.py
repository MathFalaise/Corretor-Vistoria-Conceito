"""Folha de estilos (QSS) da aplicação.

Inspirada livremente em identidades institucionais do setor imobiliário
(fundo claro, azul institucional de destaque, neutros, tipografia
limpa, cards discretos, bordas suaves) — sem copiar nenhuma marca
literalmente. Nada exagerado: poucas cores, hierarquia clara, bastante
espaço em branco.
"""

COLOR_BACKGROUND = "#F5F7FA"
COLOR_CARD = "#FFFFFF"
COLOR_BORDER = "#E1E6EC"
COLOR_TEXT_PRIMARY = "#1F2933"
COLOR_TEXT_SECONDARY = "#5A6472"
COLOR_BLUE = "#0F5FA6"
COLOR_BLUE_HOVER = "#0C4C85"
COLOR_BLUE_PRESSED = "#0A3F6E"
COLOR_ERROR = "#B3261E"
COLOR_SUCCESS = "#2E7D32"

STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Calibri", sans-serif;
    color: {COLOR_TEXT_PRIMARY};
}}

QWidget {{
    background-color: {COLOR_BACKGROUND};
}}

QWidget#card {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 10px;
}}

QLabel#titleLabel {{
    font-size: 22px;
    font-weight: 600;
    color: {COLOR_TEXT_PRIMARY};
}}

QLabel#subtitleLabel {{
    font-size: 13px;
    color: {COLOR_TEXT_SECONDARY};
}}

QLabel#sectionLabel {{
    font-size: 12px;
    font-weight: 600;
    color: {COLOR_TEXT_SECONDARY};
    letter-spacing: 0.5px;
}}

QLabel#inspectionCodeLabel {{
    font-size: 15px;
    font-weight: 600;
    color: {COLOR_BLUE};
}}

QLabel#errorLabel {{
    color: {COLOR_ERROR};
    font-size: 12px;
}}

QLabel#statusLabel {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 12px;
    padding: 4px 0px;
}}

QLineEdit, QTextEdit {{
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 13px;
    selection-background-color: {COLOR_BLUE};
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLOR_BLUE};
}}

QPushButton {{
    background-color: {COLOR_BLUE};
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {COLOR_BLUE_HOVER};
}}

QPushButton:pressed {{
    background-color: {COLOR_BLUE_PRESSED};
}}

QPushButton#secondaryButton {{
    background-color: transparent;
    color: {COLOR_BLUE};
    border: 1px solid {COLOR_BLUE};
}}

QPushButton#secondaryButton:hover {{
    background-color: #EAF2FA;
}}

QSplitter::handle {{
    background-color: {COLOR_BACKGROUND};
    width: 16px;
    height: 16px;
}}
"""
