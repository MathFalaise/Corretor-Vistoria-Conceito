"""Ponte entre a sessão de trabalho e o motor de correção.

Único lugar da aplicação que importa o engine, para não duplicar
regras nem lógica de processamento na GUI (window.py só chama
process_and_store).
"""

from engine.pipeline import process_text
from engine.rules import RULES

EMPTY_CLIPBOARD_MESSAGE = "Não há texto disponível no clipboard."
COPIED_MESSAGE = "Resultado copiado para o clipboard."


def process_and_store(session, text):
    """Roda o motor sobre `text` e atualiza a sessão com o resultado.

    Retorna o ProcessResult para a UI exibir. A sessão guarda o texto
    original, o resultado completo e a lista de edits — tudo em
    memória, nada persistido.
    """
    result = process_text(text, RULES)
    session.last_source_text = result.original_text
    session.last_result = result
    session.edits = list(result.edits)
    return result
