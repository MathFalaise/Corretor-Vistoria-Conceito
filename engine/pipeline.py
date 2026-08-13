"""Núcleo de processamento do motor de correção.

Independente de interface, clipboard, banco de dados ou IA. Recebe uma
string e uma lista de regras; devolve o texto original, o texto
corrigido e o registro de todas as alterações realizadas.

Determinístico por construção: a mesma entrada com as mesmas regras
sempre produz a mesma saída (sem aleatoriedade, sem chamadas externas).
"""

import re

from engine.models import Edit, ProcessResult


def process_text(text, rules):
    """Aplica `rules` sobre `text` e retorna um ProcessResult.

    As regras são aplicadas em sequência, na ordem da lista. Cada
    ocorrência casada é substituída e gera um Edit correspondente.
    """
    working_text = text
    edits = []

    for rule in rules:
        pattern = re.compile(rule.pattern)

        def _replace(match, rule=rule):
            edits.append(
                Edit(
                    original=match.group(0),
                    corrected=rule.replacement,
                    category=rule.category,
                    rule_id=rule.rule_id,
                    correction_source="rule",
                )
            )
            return rule.replacement

        working_text = pattern.sub(_replace, working_text)

    return ProcessResult(
        original_text=text,
        corrected_text=working_text,
        edits=edits,
    )
