"""Estrutura de dados da V2 (tela "Corrigir Vistoria"): cômodo -> 8
repartições fixas -> texto.

Puramente estrutural, sem Qt e sem nenhuma ligação com engine/ ainda —
é o ponto de conexão para uma etapa futura ligar o motor de correção a
cada repartição sem precisar redesenhar a interface.
"""

from dataclasses import dataclass, field

# Ordem exata pedida no enunciado, que também é a ordem de leitura do
# grid de 2 colunas x 4 linhas do layout (PNG de referência):
#   PAREDE               PISO
#   TETO                 PORTA
#   JANELA               COMPONENTES ELÉTRICOS
#   MOBÍLIA              OBS
SECTION_GRID = (
    ("PAREDE", "PISO"),
    ("TETO", "PORTA"),
    ("JANELA", "COMPONENTES ELÉTRICOS"),
    ("MOBÍLIA", "OBS"),
)

SECTION_NAMES = tuple(name for row in SECTION_GRID for name in row)


@dataclass
class RoomData:
    """Um cômodo: nome + texto de cada uma das 8 repartições fixas."""

    name: str
    sections: dict = field(default_factory=lambda: {name: "" for name in SECTION_NAMES})
