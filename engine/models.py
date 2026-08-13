"""Estruturas de dados do motor de correção.

Mantidas propositalmente simples: apenas o necessário para a Etapa 1
(motor determinístico mínimo). Nenhum campo especulativo para
funcionalidades futuras (aprendizado, IA, etc.) foi adicionado aqui.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rule:
    """Uma regra de correção determinística e literal.

    O pattern é uma expressão regular aplicada tal como está — sem
    fuzzy matching, sem normalização heurística. Cada regra deve ser
    específica o bastante para não gerar falsos positivos.
    """

    rule_id: str
    pattern: str
    replacement: str
    category: str
    description: str = ""


@dataclass(frozen=True)
class Edit:
    """Registro de uma alteração realizada pelo motor."""

    original: str
    corrected: str
    category: str
    rule_id: str
    correction_source: str = "rule"


@dataclass(frozen=True)
class ProcessResult:
    """Resultado do processamento de um texto pelo motor."""

    original_text: str
    corrected_text: str
    edits: list = field(default_factory=list)
