"""Compara duas extrações com o MESMO inspection_code e gera um dataset
de diferenças. Nunca vira regra, nunca altera engine/rules.py nem
corpus/ — é só um artefato de evidência para uma etapa futura.

Alinha por room -> component; texto sem correspondência nos dois lados
fica marcado como only_in_original/only_in_corrected, nunca é pareado
por suposição (ver princípio geral do projeto: não inventar).
"""

import difflib


def _components_by_name(room):
    return {c["name"]: c["text"] for c in room["components"]}


def _rooms_by_name(extracted):
    return {room["name"]: room for room in extracted.rooms}


def diff_extractions(uncorrected, corrected):
    """uncorrected/corrected: ExtractedPdf (pdf_import.importer) com o
    MESMO inspection_code. Levanta ValueError se os códigos diferirem —
    PDFs de vistorias diferentes nunca formam par."""
    if uncorrected.inspection_code != corrected.inspection_code:
        raise ValueError(
            "diff_extractions só compara extrações com o mesmo "
            f"inspection_code ({uncorrected.inspection_code!r} != "
            f"{corrected.inspection_code!r})"
        )

    uncorrected_rooms = _rooms_by_name(uncorrected)
    corrected_rooms = _rooms_by_name(corrected)
    room_names = sorted(set(uncorrected_rooms) | set(corrected_rooms))

    room_diffs = []
    for room_name in room_names:
        u_room = uncorrected_rooms.get(room_name)
        c_room = corrected_rooms.get(room_name)

        if u_room is None:
            room_diffs.append({"room": room_name, "status": "only_in_corrected"})
            continue
        if c_room is None:
            room_diffs.append({"room": room_name, "status": "only_in_original"})
            continue

        u_components = _components_by_name(u_room)
        c_components = _components_by_name(c_room)
        component_names = sorted(set(u_components) | set(c_components))

        component_diffs = []
        for name in component_names:
            u_text = u_components.get(name)
            c_text = c_components.get(name)

            if u_text is None:
                component_diffs.append({"component": name, "status": "only_in_corrected"})
                continue
            if c_text is None:
                component_diffs.append({"component": name, "status": "only_in_original"})
                continue
            if u_text == c_text:
                component_diffs.append({"component": name, "status": "identical"})
                continue

            component_diffs.append(
                {
                    "component": name,
                    "status": "different",
                    "original_text": u_text,
                    "corrected_text": c_text,
                    "differences": list(
                        difflib.unified_diff(
                            u_text.splitlines(), c_text.splitlines(), lineterm=""
                        )
                    ),
                }
            )

        room_diffs.append(
            {"room": room_name, "status": "compared", "components": component_diffs}
        )

    return {
        "inspection_code": uncorrected.inspection_code,
        "source_files": {
            "original": uncorrected.source_file,
            "corrected": corrected.source_file,
        },
        "rooms": room_diffs,
    }
