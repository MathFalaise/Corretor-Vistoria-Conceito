"""Ponte entre a sessão de trabalho e o motor de correção.

Único lugar da aplicação que importa o engine, para não duplicar
regras nem lógica de processamento na GUI (window.py só chama
process_and_store/approve_suggestion/reject_suggestion).

process_and_store usa engine.pipeline.analyze_text — Camada 0
(estrutural) + Camada 1 (regras determinísticas, aplicadas) + Camada 2
(análise contextual, gera apenas sugestões, nunca aplica sozinha).
approve_suggestion/reject_suggestion são o único caminho para uma
Suggestion da Camada 2 virar (ou não) parte do texto, e exigem a
sugestão exata devolvida por analyze_text — é assim que a aprovação
explícita do usuário fica garantida.
"""

from engine.candidates import apply_suggestion
from engine.models import ProcessResult
from engine.pipeline import analyze_text
from engine.rules import RULES

EMPTY_CLIPBOARD_MESSAGE = "Não há texto disponível no clipboard."
COPIED_MESSAGE = "Resultado copiado para o clipboard."


def process_and_store(session, text):
    """Roda o motor sobre `text` e atualiza a sessão com o resultado.

    Passa para analyze_text o contexto que já existe na sessão (room,
    component, inspection_code) — nenhum campo novo foi criado para
    isso. Retorna o ProcessResult (original_text, corrected_text,
    edits já aplicados, suggestions pendentes de aprovação) para a UI
    exibir. Tudo em memória, nada persistido.
    """
    result = analyze_text(
        text,
        RULES,
        room=session.current_room,
        component=session.current_component,
        inspection_code=session.inspection_code,
    )
    session.last_source_text = result.original_text
    session.last_result = result
    session.edits = list(result.edits)
    return result


def approve_suggestion(session, suggestion, candidate_index=0):
    """Aprova explicitamente uma Suggestion pendente da sessão atual.

    Usa apply_suggestion() (engine/candidates.py) para materializar o
    candidato escolhido sobre o corrected_text atual, soma o Edit
    resultante aos edits já aplicados e remove só essa sugestão da
    lista de pendências — as demais continuam intactas até serem
    aprovadas ou rejeitadas individualmente.
    """
    current = session.last_result
    new_text, edit = apply_suggestion(
        current.corrected_text, suggestion, candidate_index
    )
    remaining = [s for s in current.suggestions if s is not suggestion]

    new_result = ProcessResult(
        original_text=current.original_text,
        corrected_text=new_text,
        edits=current.edits + [edit],
        suggestions=remaining,
    )
    session.last_result = new_result
    session.edits = list(new_result.edits)
    return new_result


def reject_suggestion(session, suggestion):
    """Rejeita explicitamente uma Suggestion pendente: remove da lista
    de pendências sem tocar no texto corrigido.

    Não existe hoje nenhuma estrutura de histórico de rejeições na
    sessão — por instrução explícita, nenhuma é criada nesta etapa.
    """
    current = session.last_result
    remaining = [s for s in current.suggestions if s is not suggestion]

    new_result = ProcessResult(
        original_text=current.original_text,
        corrected_text=current.corrected_text,
        edits=current.edits,
        suggestions=remaining,
    )
    session.last_result = new_result
    return new_result
