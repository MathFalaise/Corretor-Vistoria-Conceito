"""Gera PDFs sintéticos para os testes de pdf_import/.

Não há PDFs reais no repositório para usar como referência — este
helper cria documentos mínimos reproduzindo o formato descrito no
projeto (identificação no início, cômodos, partes conhecidas, "*" em
itens de Mobília/OBS, múltiplas páginas), só para validar a extração.
Não é usado fora de tests/.
"""

import fitz


def build_pdf(path, pages):
    """`pages`: lista de listas de strings (uma lista de linhas por
    página do PDF gerado). Grava o arquivo em `path`."""
    document = fitz.open()
    for lines in pages:
        page = document.new_page()
        page.insert_text((36, 36), "\n".join(lines), fontsize=11)
    document.save(str(path))
    document.close()


# Layout de uma página típica descrita no projeto: identificação no
# início, cômodos com partes conhecidas, itens de Mobília/OBS com "*".
SAMPLE_INSPECTION_PAGE = [
    "Relatório de Vistoria - CloudSLIM",
    "Código da vistoria: 00959.002.02",
    "Imóvel: Rua Exemplo, 123",
    "",
    "Sala",
    "Parede",
    "*Paredes em alvenaria, na cor branco neve acrílico fosco pintura nova.",
    "Piso",
    "*Piso em alvenaria, revestido com cerâmicas na cor cinza em bom estado.",
    "Cozinha",
    "Teto",
    "*Teto em alvenaria, na cor branco gelo acrílico fosco pintura nova.",
]
