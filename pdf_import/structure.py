"""Interpretação estrutural do texto extraído de um PDF de vistoria:
vistoria -> cômodo -> parte -> texto.

Não inventa estrutura: texto que não puder ser associado a um cômodo/
parte reconhecido fica em `unmatched_text`, nunca é descartado nem
atribuído por suposição.

Reaproveita app.models.INSPECTION_CODE_PATTERN (mesma definição de
formato usada na tela "Nova Vistoria") em vez de redefinir o regex do
código — app.models não depende de PySide6, é seguro importar aqui.
"""

import re
import unicodedata

from app.models import INSPECTION_CODE_PATTERN

# app.models usa ^...$ para validar um campo inteiro; aqui procuramos o
# código em qualquer posição do texto extraído, por isso removemos as
# âncoras em vez de reescrever o padrão.
_CODE_SEARCH_PATTERN = re.compile(INSPECTION_CODE_PATTERN.pattern.strip("^$"))

# Nomes de parte/componente citados no enunciado do projeto. Variantes
# sem acento (como já aparecem em corpus/corpus_real.jsonl, coletadas
# manualmente) são aceitas como alias do mesmo nome canônico.
KNOWN_COMPONENTS = {
    "parede": "Parede",
    "piso": "Piso",
    "teto": "Teto",
    "porta": "Porta",
    "janela": "Janela",
    "componentes eletricos": "Componentes Elétricos",
    "componentes elétricos": "Componentes Elétricos",
    "mobilia": "Mobília",
    "mobília": "Mobília",
    "obs": "OBS",
}


def _strip_accents(text):
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _normalize_label(text):
    return _strip_accents(text).strip().lower()


def match_component_label(line):
    """Retorna o nome canônico do componente se `line` for exatamente um
    rótulo conhecido (ignorando acento/caixa), ou None."""
    return KNOWN_COMPONENTS.get(_normalize_label(line))


def find_inspection_code(text):
    """Primeiro código no formato NNNNN.NNN.NN encontrado em `text`,
    ou None se nenhum for encontrado."""
    match = _CODE_SEARCH_PATTERN.search(text)
    return match.group(0) if match else None


def _peek_next_nonblank(lines, start):
    for line in lines[start:]:
        if line.strip():
            return line.strip()
    return None


_ROOM_HEADING_MAX_LENGTH = 40
_ROOM_HEADING_FORBIDDEN_CHARS = ",.;:"


def _looks_like_room_heading(line):
    """Nomes de cômodo são curtos e sem pontuação de frase — diferente
    de texto de corpo (que pode ou não começar com "*", mas quase
    sempre tem vírgula/ponto). Sem essa distinção, uma linha de corpo
    seguida por um rótulo de componente seria confundida com cômodo."""
    if line.startswith("*"):
        return False
    if len(line) > _ROOM_HEADING_MAX_LENGTH:
        return False
    if any(ch in line for ch in _ROOM_HEADING_FORBIDDEN_CHARS):
        return False
    return True


def parse_structure(lines):
    """Interpreta uma lista de linhas já limpas em {rooms, unmatched_text}.

    Um cômodo só é reconhecido quando a linha seguinte não vazia é um
    componente conhecido — evita transformar texto solto em cômodo por
    engano. Uma parte/componente exige um rótulo exato conhecido.
    """
    rooms = []
    current_room = None
    current_component = None
    current_text_lines = []
    unmatched_lines = []

    def flush_component():
        nonlocal current_component, current_text_lines
        if current_component is not None:
            text = "\n".join(current_text_lines).strip()
            if current_room is not None:
                current_room["components"].append(
                    {"name": current_component, "text": text}
                )
            else:
                unmatched_lines.append(f"[{current_component}] {text}")
        current_component = None
        current_text_lines = []

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        canonical = match_component_label(line)
        if canonical:
            flush_component()
            current_component = canonical
            continue

        next_line = _peek_next_nonblank(lines, index + 1)
        if (
            _looks_like_room_heading(line)
            and next_line
            and match_component_label(next_line)
        ):
            flush_component()
            current_room = {"name": line, "components": []}
            rooms.append(current_room)
            continue

        if current_component is not None:
            current_text_lines.append(line)
        else:
            unmatched_lines.append(line)

    flush_component()
    return {"rooms": rooms, "unmatched_text": "\n".join(unmatched_lines).strip()}
