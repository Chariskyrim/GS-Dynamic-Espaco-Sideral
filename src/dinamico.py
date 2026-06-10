"""
src/dinamico.py
---------------
Programação Dinâmica — Alocação Ótima de Recursos (Knapsack 0/1).

Problema: dado um orçamento total e N regiões, cada uma com
custo de intervenção e impacto estimado (vidas salvas + área
protegida + biodiversidade), escolher quais regiões atender
para MAXIMIZAR o impacto total sem ultrapassar o orçamento.

Complexidade: O(n * W) onde n = regiões, W = orçamento inteiro.
Vs. força bruta: O(2^n) — comparado no relatório.

Uso de memoização: tabela DP 2D com reconstrução do caminho.
"""

import logging
import time
from typing import Any

log = logging.getLogger(__name__)


def alocacao_recursos(
    regioes: list[dict[str, Any]],
    orcamento_total: int = 100,
) -> dict[str, Any]:
    """
    Resolve o problema da mochila 0/1 com Programação Dinâmica.

    Parâmetros
    ----------
    regioes : list[dict]
        Cada região: {"nome": str, "custo": int, "impacto": float}
    orcamento_total : int
        Orçamento máximo em unidades inteiras (ex.: milhões R$)

    Retorna
    -------
    dict com regiões selecionadas, impacto total e comparações
    """
    if not regioes:
        return _resultado_vazio()

    n = len(regioes)
    custos = [r["custo"] for r in regioes]
    impactos = [int(r["impacto"] * 10) for r in regioes]  # multiplica p/ usar int
    W = orcamento_total

    # ── Tabela DP ────────────────────────────────────────────────────
    # dp[i][w] = máximo impacto usando as primeiras i regiões com orçamento w
    # Otimização de memória: usa apenas 2 linhas (rolling array)
    dp_atual = [0] * (W + 1)
    dp_anterior = [0] * (W + 1)

    # Mantém tabela completa apenas para reconstrução
    tabela = [[0] * (W + 1) for _ in range(n + 1)]

    t_inicio_dp = time.perf_counter()
    for i in range(1, n + 1):
        c = custos[i - 1]
        v = impactos[i - 1]
        for w in range(W + 1):
            if c > w:
                tabela[i][w] = tabela[i - 1][w]
            else:
                tabela[i][w] = max(
                    tabela[i - 1][w],          # não inclui região i
                    tabela[i - 1][w - c] + v,  # inclui região i
                )
    t_fim_dp = time.perf_counter()
    tempo_dp = t_fim_dp - t_inicio_dp

    # ── Reconstrução da solução ──────────────────────────────────────
    selecionadas: list[dict] = []
    w = W
    orcamento_usado = 0
    for i in range(n, 0, -1):
        if tabela[i][w] != tabela[i - 1][w]:
            regiao = regioes[i - 1]
            selecionadas.append(regiao)
            w -= custos[i - 1]
            orcamento_usado += custos[i - 1]
    selecionadas.reverse()

    impacto_total = tabela[n][W] / 10  # desfaz multiplicação

    # ── Estimativa tempo força bruta ─────────────────────────────────
    # T_fb ≈ 2^n * custo_por_subconjunto (estimado como 1µs)
    tempo_forca_bruta_estimado = (2 ** n) * 1e-6

    resultado = {
        "regioes_selecionadas": selecionadas,
        "orcamento_total": orcamento_total,
        "orcamento_usado": orcamento_usado,
        "orcamento_restante": orcamento_total - orcamento_usado,
        "impacto_total": impacto_total,
        "impacto_maximo_possivel": tabela[n][W] / 10,
        "tempo_dp_segundos": round(tempo_dp, 8),
        "tempo_forca_bruta_estimado": round(tempo_forca_bruta_estimado, 6),
        "speedup_estimado": round(tempo_forca_bruta_estimado / max(tempo_dp, 1e-9), 1),
        "n_regioes_total": n,
        "n_regioes_selecionadas": len(selecionadas),
        "tabela_dp": tabela,           # para visualização/debug
    }

    log.info(
        f"DP Knapsack: {len(selecionadas)}/{n} regiões, "
        f"impacto={impacto_total:.1f}, orçamento usado=R${orcamento_usado}M"
    )
    log.info(
        f"  Tempo DP={tempo_dp:.6f}s vs força_bruta≈{tempo_forca_bruta_estimado:.4f}s "
        f"(speedup ≈{resultado['speedup_estimado']}x)"
    )
    return resultado


def _resultado_vazio() -> dict:
    return {
        "regioes_selecionadas": [], "orcamento_total": 0,
        "orcamento_usado": 0, "orcamento_restante": 0,
        "impacto_total": 0, "impacto_maximo_possivel": 0,
        "tempo_dp_segundos": 0, "tempo_forca_bruta_estimado": 0,
        "speedup_estimado": 0, "n_regioes_total": 0,
        "n_regioes_selecionadas": 0, "tabela_dp": [],
    }
