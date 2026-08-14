"""Camada 2 — análise contextual e geração de candidatos de correção.

Diferença fundamental para engine/rules.py (Camada 1): aqui não existe
uma lista de frases literais que cresce a cada erro novo. Existe um
PADRÃO (prefixo comum de fusão + validação contra um vocabulário de
domínio extraído do corpus) que generaliza para palavras nunca vistas
antes, e um conjunto pequeno de sinais de contexto (evidenciados no
corpus real) que decidem a confiança de cada candidato.

Esta camada NUNCA aplica uma correção sozinha. Ela sempre produz
Suggestion — candidatos com confiança e justificativa — que só viram
Edit através de aprovação explícita (ver apply_suggestion).

Sinais usados, todos determinísticos e auditáveis, sem estatística/IA:
- o "resto" da palavra, depois de remover o prefixo, precisa ser uma
  palavra reconhecida no vocabulário do domínio (engine/vocabulary.py,
  extraído do corpus) — sem isso, nenhum candidato é gerado;
- se a palavra fundida TAMBÉM é, por si só, uma palavra válida do
  domínio (ex.: "comum"), a ambiguidade reduz a confiança de base;
- se a palavra está no início de uma frase/cláusula (início do texto,
  ou logo após . ! ? \\n , ou o marcador *), isso aumenta a confiança —
  padrão confirmado por dois casos reais do corpus ("Comum corredor...",
  "...em bom estado, comum sifão...", ambos corrigidos para "com um");
- se a palavra imediatamente anterior é um gatilho de uso adjetival
  ("uso", "área" — evidenciado por "uso comum" no corpus e "área comum"
  como caso de segurança explícito), o candidato NÃO é gerado.
"""

import re

from engine.models import Candidate, Edit, Suggestion
from engine.vocabulary import KNOWN_WORDS

# Variantes de prefixo com evidência real de fusão indevida pelo ASR,
# mapeadas para a forma canônica que deve aparecer na correção. "com"
# é a evidência direta (engine/rules.py: comporta -> com porta). "con"
# também tem evidência direta no corpus (condobradiças -> com
# dobradiças) — assimilação nasal do português antes de consoante
# ("com dobradiças" falado soa como "con-dobradiças"). Novas variantes
# só devem ser adicionadas com evidência equivalente, não por suposição.
FUSABLE_PREFIXES = {
    "com": "com",
    "con": "com",
}

# Palavras que, imediatamente antes do token, indicam o uso adjetival
# legítimo de "comum" (e de qualquer outra fusão candidata), suprimindo
# a sugestão. "uso" tem evidência direta no corpus (uso comum); "área"/
# "area" vêm do caso de segurança explicitamente exigido para este
# motor ("área comum").
ADJECTIVE_CONTEXT_TRIGGERS = frozenset({"uso", "área", "area"})

_CLAUSE_BOUNDARY_CHARS = ".!?\n,*"

_WORD_PATTERN = re.compile(r"[A-Za-zÀ-ÿ]+")

MIN_SUGGESTION_CONFIDENCE = 0.2


def _previous_word(text, token_start):
    prefix = text[:token_start]
    matches = list(_WORD_PATTERN.finditer(prefix))
    return matches[-1].group(0) if matches else None


def _is_clause_start(text, token_start):
    prefix = text[:token_start].rstrip()
    if not prefix:
        return True
    return prefix[-1] in _CLAUSE_BOUNDARY_CHARS


def _build_rationale(prefix, rest, fused_known, previous_word, clause_start):
    parts = [
        f"'{prefix}' + '{rest}' é uma segmentação plausível "
        f"('{rest}' está no vocabulário do domínio)."
    ]
    if fused_known:
        parts.append(
            f"'{prefix}{rest}' também é uma palavra válida por si só "
            "— ambiguidade reduz a confiança."
        )
    else:
        parts.append(
            f"'{prefix}{rest}' não é reconhecida como palavra do "
            "domínio isoladamente, o que reduz a chance de ser a "
            "leitura correta."
        )
    if clause_start:
        parts.append("aparece no início de uma frase/cláusula.")
    if previous_word:
        parts.append(f"palavra anterior: '{previous_word}'.")
    return " ".join(parts)


def generate_candidates(text):
    """Analisa `text` e retorna uma lista de Suggestion (Camada 2).

    Não altera `text`. Cada Suggestion carrega ao menos um Candidate
    com confiança e justificativa. Nenhuma decisão de aplicar é tomada
    aqui — isso é sempre responsabilidade de quem aprova.
    """
    suggestions = []

    for match in _WORD_PATTERN.finditer(text):
        token = match.group(0)
        token_lower = token.lower()

        for prefix_variant, canonical_prefix in FUSABLE_PREFIXES.items():
            if not token_lower.startswith(prefix_variant):
                continue

            rest = token_lower[len(prefix_variant):]
            if len(rest) < 2 or rest not in KNOWN_WORDS:
                continue

            previous_word = _previous_word(text, match.start())
            if previous_word and previous_word.lower() in ADJECTIVE_CONTEXT_TRIGGERS:
                # Evidência contextual contra a fusão (ex.: "uso comum",
                # "área comum") — não gera candidato algum.
                break

            fused_known = token_lower in KNOWN_WORDS
            clause_start = _is_clause_start(text, match.start())

            confidence = 0.25 if fused_known else 0.55
            if clause_start:
                confidence += 0.35
            confidence = min(confidence, 0.95)

            if confidence < MIN_SUGGESTION_CONFIDENCE:
                break

            corrected_prefix = (
                canonical_prefix.capitalize() if token[0].isupper() else canonical_prefix
            )
            corrected = f"{corrected_prefix} {rest}"

            candidate = Candidate(
                corrected=corrected,
                confidence=round(confidence, 2),
                rationale=_build_rationale(
                    canonical_prefix, rest, fused_known, previous_word, clause_start
                ),
                category="possible_word_fusion",
            )
            suggestions.append(
                Suggestion(
                    original=token,
                    start=match.start(),
                    end=match.end(),
                    candidates=[candidate],
                )
            )
            break  # um token só gera no máx. uma sugestão (1º prefixo válido)

    return suggestions


def apply_suggestion(text, suggestion, candidate_index=0):
    """Materializa a Candidate escolhida de uma Suggestion aprovada.

    Só deve ser chamada após aprovação explícita (fora do engine — a
    aprovação é responsabilidade da camada de aplicação/UI). Retorna o
    novo texto e o Edit resultante, para manter o registro rastreável
    de que a alteração veio de uma sugestão aprovada, não de uma regra
    automática.
    """
    candidate = suggestion.candidates[candidate_index]
    new_text = text[: suggestion.start] + candidate.corrected + text[suggestion.end :]
    edit = Edit(
        original=suggestion.original,
        corrected=candidate.corrected,
        category=candidate.category,
        rule_id="contextual_suggestion_approved",
        correction_source=candidate.correction_source,
    )
    return new_text, edit
