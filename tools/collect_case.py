"""Ferramenta temporária de coleta de casos reais para o corpus.

NÃO faz parte do aplicativo final. NÃO tenta descobrir correções
automaticamente, NÃO usa IA, NÃO faz fuzzy matching, NÃO gera regras.
Serve apenas para registrar pares (source_text, target_text) reais do
seu trabalho, preservando o ground truth manual, no mesmo schema do
corpus_seed.jsonl.

Os casos coletados vão para corpus/corpus_real.jsonl — um arquivo
separado do corpus_seed.jsonl, que permanece intocado e é o único
usado pelos testes automatizados da Etapa 1. Promover casos do
corpus_real.jsonl para um conjunto oficial de testes é uma decisão
manual, revisada por você, não algo que esta ferramenta faz sozinha.

Uso:
    python tools/collect_case.py
"""

import json
import sys
import uuid
from datetime import date
from pathlib import Path

VALID_CASE_TYPES = ("correction", "no_correction_needed", "adversarial_trap")

DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent / "corpus" / "corpus_real.jsonl"
)


def build_case(
    case_type, room, component, source_text, target_text=None, session="", notes=""
):
    """Monta um registro de caso no schema do corpus. Função pura, testável.

    Regras de validação mínimas (não é "descoberta automática de
    correção" — é só garantir consistência do registro):
    - case_type precisa ser um dos valores válidos.
    - room não pode ser vazio.
    - component não pode ser vazio.
    - source_text não pode ser vazio.
    - para no_correction_needed / adversarial_trap, target_text é
      igual a source_text por definição (se não vier explícito).
    - adversarial_trap exige notes, para documentar qual armadilha
      está sendo registrada.

    room/component registram apenas a localização do texto dentro da
    vistoria (ex.: "Quarto 01" / "Parede"). Nenhuma resolução de
    referência entre cômodos (ex.: "Igual Sala de Jantar") é feita
    aqui — são apenas strings livres, gravadas como vieram.
    """
    if case_type not in VALID_CASE_TYPES:
        raise ValueError(f"case_type inválido: {case_type!r}")

    room = room.strip()
    if not room:
        raise ValueError("room não pode ser vazio")

    component = component.strip()
    if not component:
        raise ValueError("component não pode ser vazio")

    source_text = source_text.strip()
    if not source_text:
        raise ValueError("source_text não pode ser vazio")

    if case_type == "correction":
        if not target_text or not target_text.strip():
            raise ValueError("correction exige target_text preenchido")
        target_text = target_text.strip()
    else:
        target_text = (target_text or source_text).strip()

    if case_type == "adversarial_trap" and not notes.strip():
        raise ValueError("adversarial_trap exige notes explicando a armadilha")

    return {
        "id": str(uuid.uuid4()),
        "source_session": session.strip(),
        "room": room,
        "component": component,
        "source_text": source_text,
        "target_text": target_text,
        "case_type": case_type,
        "edits": [],
        "notes": notes.strip(),
        "created_at": date.today().isoformat(),
        "split": "unreviewed",
    }


def append_case(case, path=DEFAULT_OUTPUT_PATH):
    """Acrescenta uma linha JSON ao arquivo de corpus real (append-only)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")


def _prompt_multiline(label):
    print(f"{label} (finalize com uma linha contendo apenas FIM):")
    lines = []
    while True:
        line = input()
        if line.strip() == "FIM":
            break
        lines.append(line)
    return "\n".join(lines)


def _prompt_case_type():
    print("Tipo de caso:")
    for i, t in enumerate(VALID_CASE_TYPES, start=1):
        print(f"  {i}) {t}")
    while True:
        choice = input("Escolha [1-3]: ").strip()
        if choice in ("1", "2", "3"):
            return VALID_CASE_TYPES[int(choice) - 1]
        print("Opção inválida.")


def run_interactive():
    print("=== Coleta de caso real — Vistoria Normalizer ===\n")
    case_type = _prompt_case_type()
    room = input("\nCômodo (ex.: 'Quarto 01'): ").strip()
    component = input("Parte do cômodo (ex.: 'Parede'): ").strip()
    source_text = _prompt_multiline("\nTexto original (source_text)")

    target_text = None
    if case_type == "correction":
        target_text = _prompt_multiline("\nTexto corrigido (target_text)")

    session = input("\nSessão/vistoria de origem (opcional): ").strip()
    notes = input("Observações (obrigatório para adversarial_trap): ").strip()

    try:
        case = build_case(
            case_type=case_type,
            room=room,
            component=component,
            source_text=source_text,
            target_text=target_text,
            session=session,
            notes=notes,
        )
    except ValueError as exc:
        print(f"\nErro: {exc}")
        return 1

    append_case(case)
    print(f"\nCaso registrado em {DEFAULT_OUTPUT_PATH}")
    print(json.dumps(case, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(run_interactive())
