"""Orquestra a importação: extração -> gravação em data/extracted/ ->
pareamento por inspection_code -> diff dos pares válidos.

Nunca conecta a engine.pipeline.analyze_text nem escreve em
corpus/corpus_seed.jsonl / corpus/corpus_real.jsonl — só gera o dataset
separado descrito no README de data/.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from pdf_import.diffing import diff_extractions
from pdf_import.structure import find_inspection_code, parse_structure
from pdf_import.text_extraction import extract_clean_lines

DEFAULT_UNCORRECTED_DIR = "data/pdfs_nao_corrigidos"
DEFAULT_CORRECTED_DIR = "data/pdfs_corrigidos"
DEFAULT_EXTRACTED_DIR = "data/extracted"


@dataclass
class ExtractedPdf:
    """Resultado da extração de um único PDF."""

    source_file: str
    inspection_code: str
    rooms: list
    unmatched_text: str
    error: str = None


@dataclass
class ImportSummary:
    imported: list = field(default_factory=list)  # ExtractedPdf sem erro
    errors: list = field(default_factory=list)  # (source_file, mensagem)
    no_code_detected: list = field(default_factory=list)  # source_file
    paired_codes: list = field(default_factory=list)
    unpaired_uncorrected: list = field(default_factory=list)
    unpaired_corrected: list = field(default_factory=list)


def extract_pdf(pdf_path):
    """Extrai e estrutura um único PDF. Nunca lança para fora: falha de
    leitura de um PDF externo vira ExtractedPdf com `error` preenchido,
    para não interromper a importação dos demais arquivos."""
    pdf_path = Path(pdf_path)
    try:
        lines = extract_clean_lines(pdf_path)
    except Exception as exc:  # PDF externo pode vir corrompido/protegido
        return ExtractedPdf(
            source_file=str(pdf_path),
            inspection_code=None,
            rooms=[],
            unmatched_text="",
            error=str(exc),
        )

    full_text = "\n".join(lines)
    inspection_code = find_inspection_code(full_text)
    structure = parse_structure(lines)

    return ExtractedPdf(
        source_file=str(pdf_path),
        inspection_code=inspection_code,
        rooms=structure["rooms"],
        unmatched_text=structure["unmatched_text"],
    )


def extracted_pdf_to_dict(extracted):
    return {
        "inspection_code": extracted.inspection_code,
        "source_file": extracted.source_file,
        "rooms": extracted.rooms,
        "unmatched_text": extracted.unmatched_text,
    }


def _output_path(extracted_dir, subfolder, pdf_path, inspection_code):
    stem = inspection_code if inspection_code else Path(pdf_path).stem
    return Path(extracted_dir) / subfolder / f"{stem}.json"


def import_folder(folder, extracted_dir, subfolder):
    """Extrai todos os *.pdf de `folder`, grava um .json por PDF em
    extracted_dir/subfolder/. Retorna (lista de ExtractedPdf ok, lista
    de (source_file, erro))."""
    folder = Path(folder)
    ok = []
    errors = []
    if not folder.exists():
        return ok, errors

    for pdf_path in sorted(folder.glob("*.pdf")):
        extracted = extract_pdf(pdf_path)
        if extracted.error:
            errors.append((str(pdf_path), extracted.error))
            continue

        ok.append(extracted)
        output_path = _output_path(
            extracted_dir, subfolder, pdf_path, extracted.inspection_code
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(extracted_pdf_to_dict(extracted), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return ok, errors


def run_import(
    uncorrected_dir=DEFAULT_UNCORRECTED_DIR,
    corrected_dir=DEFAULT_CORRECTED_DIR,
    extracted_dir=DEFAULT_EXTRACTED_DIR,
):
    """Importa as duas pastas, pareia por inspection_code (nunca por
    nome de arquivo) e gera um diff para cada par válido. PDFs com
    códigos diferentes nunca são tratados como par."""
    summary = ImportSummary()

    uncorrected_ok, uncorrected_errors = import_folder(
        uncorrected_dir, extracted_dir, "nao_corrigidos"
    )
    corrected_ok, corrected_errors = import_folder(
        corrected_dir, extracted_dir, "corrigidos"
    )

    summary.imported = uncorrected_ok + corrected_ok
    summary.errors = uncorrected_errors + corrected_errors
    summary.no_code_detected = [
        e.source_file for e in summary.imported if not e.inspection_code
    ]

    uncorrected_by_code = {
        e.inspection_code: e for e in uncorrected_ok if e.inspection_code
    }
    corrected_by_code = {
        e.inspection_code: e for e in corrected_ok if e.inspection_code
    }

    paired_codes = sorted(set(uncorrected_by_code) & set(corrected_by_code))
    summary.paired_codes = paired_codes
    summary.unpaired_uncorrected = sorted(
        set(uncorrected_by_code) - set(corrected_by_code)
    )
    summary.unpaired_corrected = sorted(
        set(corrected_by_code) - set(uncorrected_by_code)
    )

    if paired_codes:
        pairs_dir = Path(extracted_dir) / "pairs"
        pairs_dir.mkdir(parents=True, exist_ok=True)
        for code in paired_codes:
            diff_dataset = diff_extractions(
                uncorrected_by_code[code], corrected_by_code[code]
            )
            (pairs_dir / f"{code}_diff.json").write_text(
                json.dumps(diff_dataset, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    summary_path = Path(extracted_dir) / "import_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(_summary_to_dict(summary), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return summary


def _summary_to_dict(summary):
    return {
        "imported_count": len(summary.imported),
        "imported": [
            {"source_file": e.source_file, "inspection_code": e.inspection_code}
            for e in summary.imported
        ],
        "errors": [
            {"source_file": path, "message": message}
            for path, message in summary.errors
        ],
        "no_code_detected": summary.no_code_detected,
        "paired_codes": summary.paired_codes,
        "unpaired_uncorrected": summary.unpaired_uncorrected,
        "unpaired_corrected": summary.unpaired_corrected,
    }
