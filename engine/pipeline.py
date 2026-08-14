"""Núcleo de processamento do motor de correção.

Independente de interface, clipboard, banco de dados ou IA. Recebe uma
string e uma lista de regras; devolve o texto original, o texto
corrigido e o registro de todas as alterações realizadas.

Determinístico por construção: a mesma entrada com as mesmas regras
sempre produz a mesma saída (sem aleatoriedade, sem chamadas externas).
"""

import re

from engine.candidates import generate_candidates
from engine.models import Edit, ProcessResult
from engine.structural import normalize_structural


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


def process_text_full(text, rules):
    """Camada 0 (normalização estrutural) seguida da Camada 1 (regras).

    Não altera process_text(): é uma função nova e separada, para não
    mudar o comportamento já validado da Etapa 1. Aplica primeiro
    normalize_structural (engine/structural.py) e depois process_text
    sobre o resultado, combinando os edits das duas camadas em um único
    ProcessResult.
    """
    structural_result = normalize_structural(text)
    lexical_result = process_text(structural_result.corrected_text, rules)

    return ProcessResult(
        original_text=text,
        corrected_text=lexical_result.corrected_text,
        edits=structural_result.edits + lexical_result.edits,
    )


def analyze_text(
    text,
    rules,
    room=None,
    component=None,
    inspection_code=None,
    other_texts=None,
):
    """Camada 0 + Camada 1 (aplicadas, como sempre) + Camada 2 (sugestões).

    `corrected_text` e `edits` continuam vindo exclusivamente de
    process_text_full — nada da Camada 2 é aplicado automaticamente
    aqui. `suggestions` traz os candidatos da análise contextual
    (engine.candidates), gerados sobre o texto já normalizado/corrigido
    pelas camadas 0 e 1, para não repetir uma sugestão sobre algo que
    uma regra determinística já resolveu.

    `room`, `component`, `inspection_code` e `other_texts` são aceitos
    para deixar a assinatura pronta para quando a análise precisar
    cruzar cômodos/vistoria (fora de escopo nesta etapa) — hoje não são
    usados na pontuação de confiança, que considera só o texto em si.
    """
    base_result = process_text_full(text, rules)
    suggestions = generate_candidates(base_result.corrected_text)

    return ProcessResult(
        original_text=text,
        corrected_text=base_result.corrected_text,
        edits=base_result.edits,
        suggestions=suggestions,
    )
