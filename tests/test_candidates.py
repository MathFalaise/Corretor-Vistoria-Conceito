"""Testes de engine/candidates.py — Camada 2 (análise contextual)."""

import unittest

from engine.candidates import apply_suggestion, generate_candidates


class TestConhecidosSemRegra(unittest.TestCase):
    """generate_candidates não usa engine/rules.py — mesmo assim detecta
    os mesmos casos conhecidos, via padrão (prefixo + vocabulário), não
    via frase literal cadastrada."""

    def test_detecta_comporta(self):
        suggestions = generate_candidates("Apresenta comporta solta na entrada.")
        alvo = [s for s in suggestions if s.original == "comporta"]
        self.assertEqual(len(alvo), 1)
        self.assertEqual(alvo[0].candidates[0].corrected, "com porta")
        self.assertGreater(alvo[0].candidates[0].confidence, 0)

    def test_detecta_condobradicas(self):
        suggestions = generate_candidates("Apresenta condobradiças soltas.")
        alvo = [s for s in suggestions if s.original == "condobradiças"]
        self.assertEqual(len(alvo), 1)
        self.assertEqual(alvo[0].candidates[0].corrected, "com dobradiças")


class TestGeneralizacaoParaCasosNaoCadastrados(unittest.TestCase):
    """O mecanismo precisa generalizar para fusões nunca vistas antes,
    sem que cada uma vire uma regra manual nova."""

    def test_detecta_fusao_nunca_cadastrada_como_regra(self):
        # "jardim" está no vocabulário do corpus real; "comjardim" nunca
        # apareceu em lugar nenhum, nem como regra, nem como exemplo.
        suggestions = generate_candidates("Apresenta comjardim com plantas.")
        alvo = [s for s in suggestions if s.original == "comjardim"]
        self.assertEqual(len(alvo), 1)
        self.assertEqual(alvo[0].candidates[0].corrected, "com jardim")

    def test_nao_gera_candidato_para_palavra_sem_fusao_plausivel(self):
        # "companhia": resto "panhia" não é palavra do vocabulário -> nada.
        suggestions = generate_candidates("Reforma feita pela companhia elétrica.")
        self.assertEqual(
            [s.original for s in suggestions if s.original.lower() == "companhia"], []
        )


class TestPreservacaoDeFrasesCorretas(unittest.TestCase):
    def test_texto_sem_padrao_de_fusao_nao_gera_sugestao(self):
        texto = "Piso em porcelanato, sem avarias."
        self.assertEqual(generate_candidates(texto), [])


class TestAdversarialTraps(unittest.TestCase):
    """Casos que devem permanecer intactos: nenhuma sugestão sequer é
    gerada quando há evidência contextual contra a fusão."""

    def test_uso_comum(self):
        self.assertEqual(generate_candidates("uso comum"), [])

    def test_de_uso_comum_do_predio(self):
        self.assertEqual(generate_candidates("de uso comum do prédio"), [])

    def test_area_comum(self):
        self.assertEqual(generate_candidates("área comum"), [])

    def test_uso_comum_dentro_de_frase_maior(self):
        texto = "Corredor de uso comum do prédio, em bom estado."
        suggestions = generate_candidates(texto)
        self.assertEqual([s.original for s in suggestions], [])


class TestAmbiguidadeComContexto(unittest.TestCase):
    """'comum' sem gatilho de supressão: gera candidato, mas nunca aplica
    sozinho — confiança reflete a ambiguidade real da palavra."""

    def test_comum_armario_gera_sugestao_nao_aplica(self):
        texto = "comum armário"
        suggestions = generate_candidates(texto)
        self.assertEqual(len(suggestions), 1)
        candidate = suggestions[0].candidates[0]
        self.assertEqual(candidate.corrected, "com um")
        self.assertGreater(candidate.confidence, 0)
        self.assertLess(candidate.confidence, 1)
        # o texto original não é alterado por generate_candidates.
        self.assertEqual(texto, "comum armário")

    def test_comum_no_inicio_de_frase_real_do_corpus(self):
        texto = "Comum corredor de uso comum do prédio."
        suggestions = generate_candidates(texto)
        # apenas o "Comum" inicial gera sugestão; o "comum" precedido
        # por "uso" não gera nenhuma.
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].original, "Comum")
        self.assertEqual(suggestions[0].candidates[0].corrected, "Com um")

    def test_comum_ambiguo_no_meio_da_frase_tem_confianca_menor(self):
        # sem gatilho de supressão nem início de cláusula: fica com
        # confiança baixa, mas ainda assim rastreável como sugestão.
        texto = "Apresenta acesso comum entre as unidades."
        suggestions = generate_candidates(texto)
        alvo = [s for s in suggestions if s.original == "comum"]
        self.assertEqual(len(alvo), 1)
        self.assertLess(alvo[0].candidates[0].confidence, 0.4)


class TestRastreabilidadeDaSugestao(unittest.TestCase):
    def test_sugestao_carrega_justificativa_e_metadados(self):
        suggestions = generate_candidates("comporta")
        self.assertEqual(len(suggestions), 1)
        suggestion = suggestions[0]
        self.assertEqual(suggestion.original, "comporta")
        self.assertEqual(suggestion.start, 0)
        self.assertEqual(suggestion.end, len("comporta"))
        candidate = suggestion.candidates[0]
        self.assertTrue(candidate.rationale)
        self.assertEqual(candidate.category, "possible_word_fusion")
        self.assertEqual(candidate.correction_source, "contextual_analysis")


class TestNaoAplicaBaixaConfiancaAutomaticamente(unittest.TestCase):
    def test_generate_candidates_nunca_altera_o_texto(self):
        texto = "Apresenta acesso comum entre as unidades, com comjardim."
        generate_candidates(texto)  # não deve mutar nada
        self.assertEqual(
            texto, "Apresenta acesso comum entre as unidades, com comjardim."
        )


class TestApplySuggestion(unittest.TestCase):
    """apply_suggestion é o único caminho para uma sugestão virar texto
    final — representa a aprovação explícita do usuário."""

    def test_aplica_candidato_escolhido(self):
        texto = "Apresenta comporta solta."
        suggestions = generate_candidates(texto)
        suggestion = suggestions[0]

        novo_texto, edit = apply_suggestion(texto, suggestion)

        self.assertEqual(novo_texto, "Apresenta com porta solta.")
        self.assertEqual(edit.original, "comporta")
        self.assertEqual(edit.corrected, "com porta")
        self.assertEqual(edit.correction_source, "contextual_analysis")

    def test_nao_aplica_sem_chamada_explicita(self):
        texto = "Apresenta comporta solta."
        generate_candidates(texto)
        # sem chamar apply_suggestion, o texto original nunca muda.
        self.assertEqual(texto, "Apresenta comporta solta.")


if __name__ == "__main__":
    unittest.main()
