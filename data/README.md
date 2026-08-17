# data/

Pastas de entrada/saída da importação de PDFs. **Não é banco permanente
de imóveis** — só fonte de dados para gerar o dataset estruturado em
`extracted/`. PDFs reais de vistoria (com dados de clientes/imóveis)
não devem ser commitados neste repositório.

- `pdfs_nao_corrigidos/` — PDFs exportados do CloudSLIM, texto bruto de ASR.
- `pdfs_corrigidos/` — PDFs equivalentes já revisados manualmente.
- `extracted/` — gerado pela importação (`tools/import_pdfs.py` ou a
  tela "Importar PDFs" do app). Contém:
  - `nao_corrigidos/<código>.json` e `corrigidos/<código>.json` —
    extração estruturada de cada PDF (vistoria → cômodo → parte → texto).
  - `pairs/<código>_diff.json` — diferenças entre um par válido
    (mesmo `inspection_code` nas duas pastas).
  - `import_summary.json` — resumo da última importação.

Pareamento é sempre por `inspection_code` igual — PDFs de vistorias
diferentes nunca são tratados como par `source_text`/`target_text`.
