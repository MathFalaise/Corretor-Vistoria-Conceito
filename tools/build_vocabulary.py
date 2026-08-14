"""Regenera engine/vocabulary.py a partir do corpus atual.

Extrai as palavras que aparecem em target_text (o lado já corrigido)
de corpus/corpus_seed.jsonl e corpus/corpus_real.jsonl. Não inventa
nada: só palavras que já apareceram de fato como texto final correto
de alguma vistoria entram no vocabulário.

Uso:
    python tools/build_vocabulary.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_FILES = [ROOT / "corpus" / "corpus_seed.jsonl", ROOT / "corpus" / "corpus_real.jsonl"]
OUTPUT_PATH = ROOT / "engine" / "vocabulary.py"

WORD_PATTERN = re.compile(r"[A-Za-zÀ-ÿ]+")


def extract_words(path):
    words = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            for token in WORD_PATTERN.findall(case["target_text"]):
                if len(token) >= 2:
                    words.add(token.lower())
    return words


def build():
    combined = set()
    for path in CORPUS_FILES:
        if path.exists():
            combined |= extract_words(path)

    lines = [
        '"""Vocabulário de domínio extraído do corpus (Etapa 0 + coleta real).\n',
        "\n",
        "Gerado a partir das palavras que aparecem em target_text de\n",
        "corpus/corpus_seed.jsonl e corpus/corpus_real.jsonl — ou seja, do\n",
        "lado JÁ CORRIGIDO/validado do corpus, não do lado bruto de ASR.\n",
        "Isso é o que torna o dicionário um sinal de evidência real (uma\n",
        "palavra aparecer aqui significa que ela já foi usada, de fato, como\n",
        "texto final correto de uma vistoria), não uma lista inventada.\n",
        "\n",
        "Regenerar quando o corpus crescer: python tools/build_vocabulary.py\n",
        '"""\n',
        "\n",
        "KNOWN_WORDS = frozenset({\n",
    ]
    for word in sorted(combined):
        lines.append(f"    {word!r},\n")
    lines.append("})\n")

    OUTPUT_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"Escrito {OUTPUT_PATH} com {len(combined)} palavras.")


if __name__ == "__main__":
    build()
