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
    """Resultado do processamento de um texto pelo motor.

    `edits` são alterações JÁ aplicadas em `corrected_text` (Camada 0
    estrutural + Camada 1 regras determinísticas — sempre foram assim,
    continuam sendo). `suggestions` são candidatos da Camada 2 (análise
    contextual) que NÃO foram aplicados — corrected_text nunca reflete
    uma sugestão sem aprovação explícita do usuário.
    """

    original_text: str
    corrected_text: str
    edits: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)


@dataclass(frozen=True)
class Candidate:
    """Uma possível correção proposta pela Camada 2 (análise contextual).

    Nunca é aplicada automaticamente — é sempre um candidato, com sua
    confiança e a justificativa (rationale) de por que foi gerado.
    """

    corrected: str
    confidence: float
    rationale: str
    category: str
    correction_source: str = "contextual_analysis"


@dataclass(frozen=True)
class Suggestion:
    """Um trecho do texto identificado como possivelmente incongruente,
    com um ou mais Candidate de correção, aguardando aprovação humana.

    `start`/`end` são as posições do trecho `original` no texto em que
    a análise foi feita, para permitir localizar e aplicar a sugestão
    depois (ver engine.candidates.apply_suggestion).
    """

    original: str
    start: int
    end: int
    candidates: list = field(default_factory=list)
