"""Extração de texto bruto de PDFs via PyMuPDF (fitz). Offline, sem
rede. Só extrai texto e remove cabeçalhos/rodapés repetitivos entre
páginas — não interpreta cômodo/parte (isso é pdf_import/structure.py).
"""

from collections import Counter

import fitz

MIN_PAGES_FOR_BOILERPLATE_DETECTION = 2
BOILERPLATE_MIN_PAGE_RATIO = 0.6


def extract_pages_text(pdf_path):
    """Abre o PDF e retorna uma lista de listas de linhas, uma por página."""
    document = fitz.open(pdf_path)
    try:
        return [page.get_text("text").splitlines() for page in document]
    finally:
        document.close()


def strip_repeated_boilerplate(pages_lines):
    """Remove linhas que se repetem na maioria das páginas — cabeçalho/
    rodapé do sistema externo. Só atua com 2+ páginas: com uma página só
    não há como identificar repetição ("quando identificável")."""
    if len(pages_lines) < MIN_PAGES_FOR_BOILERPLATE_DETECTION:
        return pages_lines

    counts = Counter()
    for lines in pages_lines:
        for line in {line.strip() for line in lines if line.strip()}:
            counts[line] += 1

    threshold = max(2, round(len(pages_lines) * BOILERPLATE_MIN_PAGE_RATIO))
    boilerplate = {line for line, count in counts.items() if count >= threshold}

    return [
        [line for line in lines if line.strip() not in boilerplate]
        for lines in pages_lines
    ]


def extract_clean_lines(pdf_path):
    """PDF -> uma única lista de linhas (todas as páginas concatenadas,
    sem cabeçalho/rodapé repetitivo). Não interpreta estrutura."""
    pages = strip_repeated_boilerplate(extract_pages_text(pdf_path))
    lines = []
    for page_lines in pages:
        lines.extend(page_lines)
    return lines
