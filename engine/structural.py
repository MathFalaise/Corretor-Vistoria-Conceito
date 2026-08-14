"""Camada 0 — normalização estrutural.

Corrige apenas aspectos de FORMA que nunca alteram o conteúdo semântico
da vistoria: marcador de bullet "*", espaçamento e um resíduo de fala
conhecido ("fim" solto ao final do ditado, artefato do encerramento da
gravação). Nenhuma correção lexical mora aqui — isso é responsabilidade
exclusiva de engine/rules.py (Camada 1). Determinístico, sem IA, sem
estatística, sem n-gramas, sem contexto entre cômodos/vistoria.

Cada função abaixo só substitui trechos de espaço/marcador — nunca
palavras — e só quando o padrão é inequívoco.
"""

import re

from engine.models import Edit, ProcessResult

STRUCTURAL_SOURCE = "structural_normalization"

# "fim" sozinho na última linha do texto: artefato de encerramento de
# fala. Não casa "fim" seguido de pontuação (ex.: "Fim.") nem "fim" no
# meio do texto — só o token solto ao final, sem nada depois dele.
_TRAILING_FIM_PATTERN = re.compile(r"[ \t]*\n[ \t]*fim[ \t]*\Z", re.IGNORECASE)

_DUPLICATE_HORIZONTAL_WHITESPACE = re.compile(r"[ \t]{2,}")
_WHITESPACE_BEFORE_PUNCTUATION = re.compile(r"[ \t]+([,.;:!?])")


def _strip_trailing_fim(text, edits):
    """Remove o resíduo '\\nfim' ao final do texto, se existir."""
    match = _TRAILING_FIM_PATTERN.search(text)
    if not match:
        return text
    edits.append(
        Edit(
            original=match.group(0),
            corrected="",
            category="transcription_residue",
            rule_id="structural_trailing_fim",
            correction_source=STRUCTURAL_SOURCE,
        )
    )
    return text[: match.start()]


def _collapse_horizontal_whitespace(text, edits):
    """Colapsa sequências de espaços/tabs em um único espaço.

    Não toca quebras de linha (\\n) — elas continuam marcando limites
    de cláusula, fora do escopo desta camada.
    """

    def _replace(match):
        edits.append(
            Edit(
                original=match.group(0),
                corrected=" ",
                category="whitespace",
                rule_id="structural_collapse_whitespace",
                correction_source=STRUCTURAL_SOURCE,
            )
        )
        return " "

    return _DUPLICATE_HORIZONTAL_WHITESPACE.sub(_replace, text)


def _remove_space_before_punctuation(text, edits):
    """Remove espaço(s) imediatamente antes de , . ; : ! ?"""

    def _replace(match):
        edits.append(
            Edit(
                original=match.group(0),
                corrected=match.group(1),
                category="punctuation_spacing",
                rule_id="structural_space_before_punctuation",
                correction_source=STRUCTURAL_SOURCE,
            )
        )
        return match.group(1)

    return _WHITESPACE_BEFORE_PUNCTUATION.sub(_replace, text)


def _normalize_leading_bullet(text, edits):
    """Garante exatamente um '*' no início do texto, sem duplicar.

    Não insere o marcador quando o texto começa com letra minúscula:
    isso indica, com bastante segurança, um fragmento/continuação de
    frase (não o início de uma resposta nova) — padrão confirmado pelo
    próprio corpus real (caso adversarial_trap "de uso comum do
    prédio."), onde o marcador NÃO deve ser inserido.
    """
    stripped_all = text.lstrip()
    if not stripped_all:
        return text

    if stripped_all.startswith("*"):
        content = stripped_all.lstrip("*").lstrip(" \t")
    else:
        first_char = stripped_all[0]
        if first_char.isalpha() and first_char.islower():
            return text
        content = stripped_all

    new_text = "*" + content
    if new_text == text:
        return text

    old_prefix = text[: len(text) - len(content)]
    edits.append(
        Edit(
            original=old_prefix,
            corrected="*",
            category="bullet_marker",
            rule_id="structural_normalize_bullet",
            correction_source=STRUCTURAL_SOURCE,
        )
    )
    return new_text


def normalize_structural(text):
    """Aplica a Camada 0 sobre `text` e retorna um ProcessResult.

    Ordem: remove resíduo de fala -> normaliza espaçamento -> normaliza
    marcador de bullet. Cada alteração vira um Edit com
    correction_source="structural_normalization".
    """
    edits = []
    working = text
    working = _strip_trailing_fim(working, edits)
    working = _collapse_horizontal_whitespace(working, edits)
    working = _remove_space_before_punctuation(working, edits)
    working = _normalize_leading_bullet(working, edits)

    return ProcessResult(
        original_text=text,
        corrected_text=working,
        edits=edits,
    )
