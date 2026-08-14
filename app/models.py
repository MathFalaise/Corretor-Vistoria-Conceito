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
