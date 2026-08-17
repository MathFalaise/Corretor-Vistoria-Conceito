"""Testes de pdf_import/structure.py: código, cômodo, componente."""

import unittest

from pdf_import.structure import (
    find_inspection_code,
    match_component_label,
    parse_structure,
)


class TestFindInspectionCode(unittest.TestCase):
    def test_encontra_codigo_no_formato_correto(self):
        texto = "Relatório de Vistoria\nCódigo da vistoria: 00959.002.02\nImóvel..."
        self.assertEqual(find_inspection_code(texto), "00959.002.02")

    def test_retorna_none_quando_nao_ha_codigo(self):
        texto = "Relatório de Vistoria sem nenhum código reconhecível."
        self.assertIsNone(find_inspection_code(texto))

    def test_ignora_numero_fora_do_formato(self):
        texto = "Processo número 12345, telefone 99999-9999."
        self.assertIsNone(find_inspection_code(texto))

    def test_encontra_o_primeiro_codigo_quando_ha_mais_de_um(self):
        texto = "00959.002.02 é o código; não confundir com 00471.002.05."
        self.assertEqual(find_inspection_code(texto), "00959.002.02")


class TestMatchComponentLabel(unittest.TestCase):
    def test_reconhece_todos_os_componentes_do_enunciado(self):
        casos = {
            "Parede": "Parede",
            "Piso": "Piso",
            "Teto": "Teto",
            "Porta": "Porta",
            "Janela": "Janela",
            "Componentes Elétricos": "Componentes Elétricos",
            "Mobília": "Mobília",
            "OBS": "OBS",
        }
        for linha, esperado in casos.items():
            with self.subTest(linha=linha):
                self.assertEqual(match_component_label(linha), esperado)

    def test_reconhece_variante_sem_acento(self):
        self.assertEqual(match_component_label("Componentes Eletricos"), "Componentes Elétricos")
        self.assertEqual(match_component_label("Mobilia"), "Mobília")

    def test_ignora_caixa(self):
        self.assertEqual(match_component_label("parede"), "Parede")
        self.assertEqual(match_component_label("PISO"), "Piso")

    def test_nao_reconhece_texto_qualquer(self):
        self.assertIsNone(match_component_label("Paredes em bom estado."))
        self.assertIsNone(match_component_label("Sala"))


class TestParseStructure(unittest.TestCase):
    def test_identifica_comodo_por_lookahead_de_componente(self):
        lines = ["Sala", "Parede", "*Paredes em alvenaria."]
        result = parse_structure(lines)

        self.assertEqual(len(result["rooms"]), 1)
        self.assertEqual(result["rooms"][0]["name"], "Sala")
        self.assertEqual(
            result["rooms"][0]["components"],
            [{"name": "Parede", "text": "*Paredes em alvenaria."}],
        )

    def test_dois_comodos_com_varios_componentes(self):
        lines = [
            "Sala",
            "Parede",
            "*Paredes em alvenaria.",
            "Piso",
            "*Piso em cerâmica.",
            "Cozinha",
            "Teto",
            "*Teto pintura nova.",
        ]
        result = parse_structure(lines)

        nomes_comodos = [r["name"] for r in result["rooms"]]
        self.assertEqual(nomes_comodos, ["Sala", "Cozinha"])

        sala = result["rooms"][0]
        self.assertEqual(len(sala["components"]), 2)
        self.assertEqual(sala["components"][0]["name"], "Parede")
        self.assertEqual(sala["components"][1]["name"], "Piso")

        cozinha = result["rooms"][1]
        self.assertEqual(cozinha["components"], [{"name": "Teto", "text": "*Teto pintura nova."}])

    def test_texto_de_varias_linhas_no_mesmo_componente(self):
        lines = [
            "Sala",
            "Mobília",
            "*Com um sofá em tecido na cor cinza.",
            "*Com uma mesa de centro em madeira.",
        ]
        result = parse_structure(lines)
        texto = result["rooms"][0]["components"][0]["text"]
        self.assertEqual(
            texto,
            "*Com um sofá em tecido na cor cinza.\n*Com uma mesa de centro em madeira.",
        )

    def test_texto_sem_comodo_reconhecivel_vai_para_unmatched(self):
        lines = ["Texto solto sem nenhum cabeçalho de cômodo ou componente."]
        result = parse_structure(lines)

        self.assertEqual(result["rooms"], [])
        self.assertIn("Texto solto sem nenhum cabeçalho", result["unmatched_text"])

    def test_nao_inventa_comodo_para_linha_que_nao_precede_componente(self):
        # "Observações gerais" não é seguido de um componente conhecido,
        # então não deve virar cômodo — vai para unmatched.
        lines = ["Observações gerais", "Nada digno de nota."]
        result = parse_structure(lines)

        self.assertEqual(result["rooms"], [])
        self.assertIn("Observações gerais", result["unmatched_text"])

    def test_linhas_em_branco_sao_ignoradas(self):
        lines = ["Sala", "", "Parede", "", "*Paredes em alvenaria.", ""]
        result = parse_structure(lines)
        self.assertEqual(result["rooms"][0]["name"], "Sala")
        self.assertEqual(
            result["rooms"][0]["components"][0]["text"], "*Paredes em alvenaria."
        )


if __name__ == "__main__":
    unittest.main()
