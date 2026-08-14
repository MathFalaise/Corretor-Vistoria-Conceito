# Corretor Vistoria

Aplicação desktop offline (Windows) para pós-processar transcrições de
vistoria copiadas do CloudSLIM. Não integra com o CloudSLIM: o fluxo é
manual e explícito, via clipboard.

```
CloudSLIM → Ctrl+C → Corretor Vistoria → processamento → Ctrl+V → CloudSLIM
```

## Instalação

Requer Python 3.10+.

```bash
pip install -e .
```

Ou, sem instalar o pacote, apenas a dependência:

```bash
pip install PySide6
```

## Execução

```bash
python -m app
```

## Testes

```bash
python -m unittest discover -s tests -t . -v
```

Os testes cobrem o motor de correção (`engine/`), a ferramenta de
coleta de corpus (`tools/collect_case.py`) e a camada de aplicação
(`app/models.py`, `app/session.py`) — validação de código de vistoria,
`InspectionSession`, e o processamento via `RULES` do engine. Testes de
interface gráfica (renderização de janelas) não fazem parte desta
suíte; a lógica que a interface usa é testada isoladamente.

## Fluxo da V1

1. **Tela inicial** — botão "NOVA VISTORIA".
2. **Nova vistoria** — informe o código no formato `00000.000.00`
   (ex.: `00959.002.02`). Código inválido mostra a mensagem de erro e
   não avança.
3. **Tela principal** — para cada trecho da vistoria:
   - preencha (opcionalmente) Cômodo e Parte do cômodo — são apenas
     contexto visual nesta versão, não afetam o processamento;
   - copie o texto no CloudSLIM (Ctrl+C);
   - clique em **PROCESSAR CLIPBOARD** — o app lê o clipboard, mostra
     o texto original, aplica as regras determinísticas do motor
     (`engine/rules.py`) e mostra o resultado, com a contagem de
     alterações aplicadas;
   - clique em **COPIAR RESULTADO** — o texto corrigido vai para o
     clipboard, pronto para Ctrl+V de volta no CloudSLIM;
   - repita para o próximo trecho, ou clique em **NOVA VISTORIA** para
     começar outra vistoria (a sessão atual é descartada).

## Clipboard explícito

O app **nunca** monitora o clipboard em segundo plano. A leitura e a
escrita só acontecem em resposta direta a um clique seu
("PROCESSAR CLIPBOARD" / "COPIAR RESULTADO"). Não há atalho global de
teclado nesta versão.

## Limitações atuais (V1)

- Nenhuma persistência: a sessão de vistoria (código, cômodo, parte,
  último texto processado) existe apenas em memória e é descartada ao
  iniciar uma nova vistoria ou fechar o app.
- Nenhum banco de dados (SQLite vem em etapa futura).
- Nenhuma IA, aprendizado automático, fuzzy matching ou modelo
  estatístico — só as regras determinísticas do `engine/`.
- Cômodo e Parte do cômodo são apenas texto livre de contexto; não há
  resolução de referências entre cômodos (ex.: "Igual Sala de
  Jantar") — isso é um passo futuro, que usará obrigatoriamente o
  código da vistoria para nunca cruzar referências entre imóveis
  diferentes.
- Sem processamento de OCR/PDF, sem login, sem nuvem, sem internet.
- Regras de correção continuam vivendo exclusivamente em
  `engine/rules.py` — a interface não duplica nem reimplementa nada
  do motor.
