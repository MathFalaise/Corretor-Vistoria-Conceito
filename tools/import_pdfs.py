"""CLI offline para importar PDFs de vistoria.

Uso (precisa ser `-m`, não `python tools/import_pdfs.py` — o script
importa o pacote irmão pdf_import/, que só é resolvido com a raiz do
projeto no sys.path):
    python -m tools.import_pdfs
    python -m tools.import_pdfs --uncorrected caminho --corrected caminho

Só gera o dataset estruturado em data/extracted/ (extração + pareamento
por inspection_code + diff dos pares válidos). Não conecta ao motor de
correção nem ao corpus.
"""

import argparse

from pdf_import.importer import (
    DEFAULT_CORRECTED_DIR,
    DEFAULT_EXTRACTED_DIR,
    DEFAULT_UNCORRECTED_DIR,
    run_import,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uncorrected", default=DEFAULT_UNCORRECTED_DIR)
    parser.add_argument("--corrected", default=DEFAULT_CORRECTED_DIR)
    parser.add_argument("--extracted", default=DEFAULT_EXTRACTED_DIR)
    args = parser.parse_args()

    summary = run_import(args.uncorrected, args.corrected, args.extracted)

    print(f"Importados: {len(summary.imported)}")
    for item in summary.imported:
        codigo = item.inspection_code or "(código não identificado)"
        print(f"  {item.source_file}: {codigo}")

    print(f"\nPares encontrados: {len(summary.paired_codes)}")
    for code in summary.paired_codes:
        print(f"  {code}")

    print(f"\nSem par (só em não corrigidos): {summary.unpaired_uncorrected}")
    print(f"Sem par (só em corrigidos): {summary.unpaired_corrected}")

    if summary.no_code_detected:
        print("\nSem código identificado:")
        for source_file in summary.no_code_detected:
            print(f"  {source_file}")

    if summary.errors:
        print("\nErros de leitura:")
        for source_file, message in summary.errors:
            print(f"  {source_file}: {message}")


if __name__ == "__main__":
    main()
