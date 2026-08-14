"""Regras determinísticas de correção.

Cada regra é um casamento literal (com fronteira de palavra), nunca uma
substituição genérica. Isso é o que impede, por exemplo, que a regra de
"comum armário" -> "com um armário" afete "uso comum": o padrão exige a
frase completa, não apenas a palavra "comum" isolada.

Para adicionar uma nova regra: acrescente um novo `Rule` a RULES.
Para remover: apague o item correspondente. O pipeline não precisa ser
alterado em nenhum dos dois casos.
"""

from engine.models import Rule

RULES = [
    Rule(
        rule_id="word_split_comporta",
        pattern=r"\bcomporta\b",
        replacement="com porta",
        category="word_split",
        description=(
            "ASR funde 'com' + 'porta' na palavra existente 'comporta'. "
            "Casamento literal da palavra inteira."
        ),
    ),
    Rule(
        rule_id="word_split_condobradicas",
        pattern=r"\bcondobradiças\b",
        replacement="com dobradiças",
        category="word_split",
        description=(
            "ASR funde 'com' + 'dobradiças' em uma palavra inexistente. "
            "Casamento literal da palavra inteira."
        ),
    ),
    Rule(
        rule_id="word_split_comum_armario",
        pattern=r"\bcomum armário\b",
        replacement="com um armário",
        category="word_split",
        description=(
            "Aplica somente quando 'comum' é seguido exatamente por "
            "'armário'. Não afeta outros usos válidos de 'comum' "
            "(ex.: 'uso comum'), pois o padrão exige a frase completa."
        ),
    ),
]
