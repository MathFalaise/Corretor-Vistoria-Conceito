"""Modelos de dados da aplicação (não confundir com engine/models.py).

Aqui vivem apenas os dados e regras de validação da própria interface:
o código da vistoria e a sessão de trabalho em memória. Nada aqui toca
o motor de correção — isso é responsabilidade de app/session.py.
"""

import re
from dataclasses import dataclass, field

INSPECTION_CODE_PATTERN = re.compile(r"^\d{5}\.\d{3}\.\d{2}$")

INVALID_CODE_MESSAGE = "Informe o código da vistoria no formato 00000.000.00."


def is_valid_inspection_code(code):
    """Valida o formato 00000.000.00. Não verifica existência real."""
    return bool(INSPECTION_CODE_PATTERN.match(code.strip()))


def extract_inspection_digits(text):
    """Extrai só os dígitos de `text`, ignorando letras/espaços/símbolos
    e os próprios pontos, limitando a 10 dígitos (o 11º em diante é
    descartado)."""
    return re.sub(r"\D", "", text)[:10]


def format_inspection_code(digits):
    """Formata uma string de até 10 dígitos como 00000.000.00.

    O primeiro ponto aparece assim que o 5º dígito é digitado (mesmo
    sem haver 6º ainda) e o segundo assim que o 8º é digitado — não só
    ao começar o próximo grupo. Para menos de 5 dígitos, nenhum ponto
    é inserido."""
    length = len(digits)
    if length < 5:
        return digits
    if length == 5:
        return f"{digits}."
    if length < 8:
        return f"{digits[:5]}.{digits[5:]}"
    if length == 8:
        return f"{digits[:5]}.{digits[5:8]}."
    return f"{digits[:5]}.{digits[5:8]}.{digits[8:]}"


def cursor_position_after_digit_count(formatted, digit_count):
    """Posição, dentro de `formatted`, logo após o dígito de índice
    `digit_count` (1-based) — pulando um ponto que tenha sido inserido
    automaticamente logo em seguida. Usado para manter o cursor no
    lugar certo enquanto o campo é reformatado durante a digitação."""
    if digit_count <= 0:
        return 0

    count = 0
    for i, char in enumerate(formatted):
        if char.isdigit():
            count += 1
            if count == digit_count:
                pos = i + 1
                if pos < len(formatted) and formatted[pos] == ".":
                    pos += 1
                return pos

    return len(formatted)


@dataclass
class InspectionSession:
    """Sessão de trabalho de uma vistoria, mantida apenas em memória.

    Não é persistida em banco de dados. Cômodo e Parte do cômodo são,
    nesta V1, apenas contexto informativo — não há nenhuma resolução
    de referência entre cômodos (ex.: "Igual Sala de Jantar").
    """

    inspection_code: str
    current_room: str = ""
    current_component: str = ""
    last_source_text: str = ""
    last_result: object = None
    edits: list = field(default_factory=list)

    def update_room(self, room):
        self.current_room = room.strip()

    def update_component(self, component):
        self.current_component = component.strip()


def create_session(inspection_code):
    """Cria uma InspectionSession validando o código da vistoria.

    Levanta ValueError com a mensagem de erro exibível ao usuário caso
    o código não siga o formato 00000.000.00.
    """
    code = inspection_code.strip()
    if not is_valid_inspection_code(code):
        raise ValueError(INVALID_CODE_MESSAGE)
    return InspectionSession(inspection_code=code)
