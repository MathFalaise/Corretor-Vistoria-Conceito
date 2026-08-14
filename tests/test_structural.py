"""Testes de engine/structural.py — Camada 0 (normalização estrutural)."""

import re
import unittest

from engine.structural import STRUCTURAL_SOURCE, normalize_structural


class TestBulletMarker(unittest.TestCase):
    def test_insere_asterisco_quando_ausente_em_texto_com_maiuscula(self):
        result = normalize_structural("Porta em madeira em bom estado.")
        self.assertEqual(result.corrected_text, "*Porta em madeira em bom estado.")
        self.assertEqual(len(result.edits), 1)
        self.assertEqual(result.edits[0].category, "bullet_marker")
        self.assertEqual(result.edits[0].correction_source, STRUCTURAL_SOURCE)

    def test_nao_duplica_asterisco_ja_existente(self):
        texto = "*Paredes em alvenaria, na cor branco."
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, texto)
        self.assertEqual(result.edits, [])

    def test_colapsa_asteriscos_duplicados(self):
        result = normalize_structural("**Teto em alvenaria.")
        self.assertEqual(result.corrected_text, "*Teto em alvenaria.")

    def test_remove_espaco_entre_asterisco_e_conteudo(self):
        result = normalize_structural("*   Piso em cerâmica.")
        self.assertEqual(result.corrected_text, "*Piso em cerâmica.")

    def test_nao_insere_em_fragmento_iniciado_por_minuscula(self):
        # Caso real do corpus (adversarial_trap): fragmento de frase,
        # não o início de uma resposta nova — não deve ganhar marcador.
        texto = "de uso comum do prédio."
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, texto)
        self.assertEqual(result.edits, [])

    def test_texto_vazio_nao_gera_asterisco(self):
        result = normalize_structural("")
        self.assertEqual(result.corrected_text, "")
        self.assertEqual(result.edits, [])

    def test_texto_so_com_espacos_nao_gera_asterisco(self):
        # espaços puros são colapsados (whitespace), mas nenhum "*" é
        # inventado sobre um texto vazio de conteúdo.
        result = normalize_structural("   ")
        self.assertEqual(result.corrected_text, " ")
        self.assertNotIn("*", result.corrected_text)

    def test_insere_quando_texto_comeca_com_digito(self):
        result = normalize_structural("2 tomadas em bom estado.")
        self.assertEqual(result.corrected_text, "*2 tomadas em bom estado.")


class TestWhitespaceNormalization(unittest.TestCase):
    def test_colapsa_espacos_duplicados(self):
        # início minúsculo: isola o teste do comportamento de bullet.
        result = normalize_structural("piso  em   cerâmica.")
        self.assertEqual(result.corrected_text, "piso em cerâmica.")
        self.assertTrue(all(e.category == "whitespace" for e in result.edits))

    def test_nao_colapsa_quebra_de_linha(self):
        texto = "primeira frase.\nsegunda frase."
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, texto)

    def test_remove_espaco_antes_de_pontuacao(self):
        result = normalize_structural("bom estado , com folga .")
        self.assertEqual(result.corrected_text, "bom estado, com folga.")

    def test_nao_altera_pontuacao_ja_correta(self):
        texto = "bom estado, com folga."
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, texto)
        self.assertEqual(result.edits, [])


class TestTrailingFimResidue(unittest.TestCase):
    def test_remove_fim_solto_ao_final(self):
        # Exemplo real do corpus (id b6fef927): "*" também é inserido,
        # já que o texto começa com maiúscula — comportamento esperado
        # da camada completa, não um efeito colateral indesejado.
        texto = "Piso em bom estado. \nfim"
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, "*Piso em bom estado.")
        categorias = [e.category for e in result.edits]
        self.assertIn("transcription_residue", categorias)

    def test_nao_remove_fim_no_meio_do_texto(self):
        # "fim" como palavra legítima, não no final do texto. Início
        # minúsculo isola o teste do comportamento de bullet.
        texto = "reforma prevista para o fim do mês, ainda em andamento."
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, texto)
        self.assertEqual(result.edits, [])

    def test_nao_remove_fim_seguido_de_pontuacao(self):
        # "Fim." com maiúscula e ponto: parece conteúdo legítimo do
        # inspetor, não o artefato de encerramento de fala. O "*" é
        # inserido normalmente no início do texto.
        texto = "Vistoria concluída.\nFim."
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, "*" + texto)
        categorias = [e.category for e in result.edits]
        self.assertNotIn("transcription_residue", categorias)

    def test_nao_remove_fim_que_nao_esta_no_final_absoluto(self):
        texto = "primeira parte.\nfim\nsegunda parte real da vistoria."
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, texto)
        self.assertEqual(result.edits, [])


class TestPreservation(unittest.TestCase):
    def test_texto_ja_limpo_permanece_identico(self):
        texto = "*Piso em porcelanato, sem avarias."
        result = normalize_structural(texto)
        self.assertEqual(result.corrected_text, texto)
        self.assertEqual(result.original_text, texto)
        self.assertEqual(result.edits, [])

    def test_nao_altera_palavras_ou_conteudo_semantico(self):
        texto = "Porta com fechadura quebrada,  em mau estado ."
        result = normalize_structural(texto)
        # apenas espaço/pontuação/marcador mudam de posição — nenhum
        # caractere de conteúdo é removido, adicionado ou substituído.
        # (comparação por tokens de espaço não serve aqui: remover o
        # espaço antes de "." muda deliberadamente a tokenização.)
        original_core = re.sub(r"[\s*]+", "", texto)
        corrected_core = re.sub(r"[\s*]+", "", result.corrected_text)
        self.assertEqual(original_core, corrected_core)


class TestDeterminism(unittest.TestCase):
    def test_idempotente(self):
        texto = "porta  com   fechadura , quebrada ."
        primeira = normalize_structural(texto)
        segunda = normalize_structural(primeira.corrected_text)
        self.assertEqual(primeira.corrected_text, segunda.corrected_text)
        self.assertEqual(segunda.edits, [])

    def test_mesma_entrada_mesma_saida(self):
        texto = "Janela  em  ferro , trinco quebrado ."
        r1 = normalize_structural(texto)
        r2 = normalize_structural(texto)
        self.assertEqual(r1.corrected_text, r2.corrected_text)
        self.assertEqual(len(r1.edits), len(r2.edits))


if __name__ == "__main__":
    unittest.main()
