"""
src/relatorio.py
----------------
Gera relatório textual completo da execução.
"""

import logging
import os
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)


def gerar_relatorio(
    focos: list[dict],
    bases: list[dict],
    grafo: Any,
    caminho_dijkstra: list[str],
    distancia_dijkstra: float,
    brigadas: list[dict],
    focos_cobertos: list[str],
    simulacao: dict[str, Any],
    alocacao: dict[str, Any],
    path: str = "output/relatorio_final.txt",
) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)

    linhas: list[str] = []

    def linha(t: str = "") -> None:
        linhas.append(t)

    def titulo(t: str) -> None:
        linhas.append("")
        linhas.append("=" * 65)
        linhas.append(f"  {t}")
        linhas.append("=" * 65)

    def secao(t: str) -> None:
        linhas.append("")
        linhas.append(f"── {t} " + "─" * max(0, 55 - len(t)))

    # ── Cabeçalho ───────────────────────────────────────────────────
    titulo("RELATÓRIO DE ANÁLISE — INCÊNDIOS FLORESTAIS VIA SATÉLITE")
    linha(f"Gerado em : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    linha(f"Fonte     : NASA FIRMS VIIRS / Dados simulados (estrutura real)")
    linha(f"Projeto   : GS — Estruturas de Dados e Algoritmos")

    # ── Dados ───────────────────────────────────────────────────────
    titulo("1. DADOS CARREGADOS")
    linha(f"  Focos de calor detectados : {len(focos)}")
    linha(f"  Bases de bombeiros        : {len(bases)}")
    linha(f"  Satélites utilizados      : VIIRS (SNPP), MODIS")

    biomas: dict[str, int] = {}
    for f in focos:
        b = f.get("bioma", "Desconhecido")
        biomas[b] = biomas.get(b, 0) + 1
    secao("Distribuição por Bioma")
    for bioma, cnt in sorted(biomas.items(), key=lambda x: -x[1]):
        barra = "█" * min(30, cnt)
        linha(f"  {bioma:20s} {cnt:3d}  {barra}")

    frps = [f.get("frp", 0) for f in focos]
    if frps:
        secao("Estatísticas FRP (Fire Radiative Power — MW)")
        linha(f"  Mínimo  : {min(frps):.1f} MW")
        linha(f"  Máximo  : {max(frps):.1f} MW")
        linha(f"  Média   : {sum(frps)/len(frps):.1f} MW")
        linha(f"  Total   : {sum(frps):.0f} MW")

    # ── Grafo ───────────────────────────────────────────────────────
    titulo("2. MODELAGEM COM GRAFOS")
    linha(f"  Tipo              : Não-dirigido, ponderado (distância km)")
    linha(f"  Nós               : {grafo.num_nos()} (focos + bases)")
    linha(f"  Arestas           : {grafo.num_arestas()}")
    linha(f"  Raio de conexão   : {grafo.raio_km} km")
    linha(f"  Grau médio        : {grafo.grau_medio():.2f}")
    linha(f"  Componentes conec.: {grafo.num_componentes()}")
    linha("")
    linha("  Interpretação: cada aresta representa uma rota possível")
    linha("  de deslocamento de equipes ou propagação entre focos.")

    # ── Dijkstra ────────────────────────────────────────────────────
    titulo("3. DIJKSTRA — CAMINHO MÍNIMO DE RESPOSTA")
    linha(f"  Complexidade    : O((V + E) log V) com heap binário")
    if caminho_dijkstra:
        linha(f"  Origem          : {caminho_dijkstra[0]}")
        linha(f"  Destino         : {caminho_dijkstra[-1]} (foco mais crítico)")
        linha(f"  Distância total : {distancia_dijkstra:.1f} km")
        linha(f"  Nós no caminho  : {len(caminho_dijkstra)}")
        linha(f"  Caminho         : {' → '.join(caminho_dijkstra)}")
    else:
        linha("  Caminho não encontrado (nós desconectados)")
    linha("")
    linha("  Uso prático: rota ótima para o primeiro deslocamento")
    linha("  de equipes da base mais próxima ao foco crítico.")

    # ── Guloso ──────────────────────────────────────────────────────
    titulo("4. ALGORITMO GULOSO — COBERTURA DE BRIGADAS")
    linha(f"  Complexidade    : O(k × n) — k brigadas, n focos")
    linha(f"  Estratégia      : maximizar FRP coberto por brigada")
    linha(f"  Raio de atuação : {brigadas[0]['raio_km'] if brigadas else 'N/A'} km")
    linha(f"  Brigadas alocadas: {len(brigadas)}")
    linha(f"  Focos cobertos  : {len(focos_cobertos)} / {len(focos)} "
          f"({100 * len(focos_cobertos) / max(len(focos), 1):.1f}%)")
    linha("")
    linha("  Posicionamento das brigadas:")
    for b in brigadas:
        linha(f"    {b['id']}: lat={b['lat']:>8.3f}  lon={b['lon']:>9.3f}"
              f"  focos={b['focos_cobertos']:>3d}  FRP={b['frp_total']:>7.0f} MW")

    # ── Monte Carlo ─────────────────────────────────────────────────
    titulo("5. SIMULAÇÃO MONTE CARLO — PROPAGAÇÃO")
    linha(f"  Simulações      : {simulacao['n_simulacoes']}")
    linha(f"  Passos/sim.     : {simulacao['passos_por_sim']} (≈ {simulacao['passos_por_sim'] * 6}h)")
    linha(f"  Prob. base prop.: {simulacao['prob_base']:.0%}")
    linha("")
    linha("  Área propagada estimada:")
    linha(f"    Mínima  : {simulacao['area_minima_km2']:>8.0f} km²")
    linha(f"    Média   : {simulacao['area_media_km2']:>8.0f} km²")
    linha(f"    Mediana : {simulacao['area_mediana_km2']:>8.0f} km²")
    linha(f"    P95     : {simulacao['area_p95_km2']:>8.0f} km²")
    linha(f"    P99     : {simulacao['area_p99_km2']:>8.0f} km²")
    linha(f"    Máxima  : {simulacao['area_maxima_km2']:>8.0f} km²")
    linha("")
    linha(f"  Zonas com risco > 60%: {simulacao['zonas_risco_alto']}")
    linha("")
    linha("  Interpretação: em 95% dos cenários simulados, a área")
    linha(f"  afetada não excede {simulacao['area_p95_km2']:.0f} km².")

    # ── Prog. Dinâmica ───────────────────────────────────────────────
    titulo("6. PROGRAMAÇÃO DINÂMICA — ALOCAÇÃO DE RECURSOS")
    linha(f"  Algoritmo       : Knapsack 0/1 (mochila booleana)")
    linha(f"  Complexidade    : O(n × W) — n regiões, W orçamento")
    linha(f"  Orçamento total : R$ {alocacao['orcamento_total']}M")
    linha(f"  Orçamento usado : R$ {alocacao['orcamento_usado']}M")
    linha(f"  Orçamento livre : R$ {alocacao['orcamento_restante']}M")
    linha(f"  Impacto máximo  : {alocacao['impacto_total']:.1f} pontos")
    linha("")
    linha("  Regiões selecionadas para intervenção:")
    for r in alocacao["regioes_selecionadas"]:
        linha(f"    ✓ {r['nome']:25s}  custo=R${r['custo']:>2}M  impacto={r['impacto']:>3}")
    linha("")
    linha("  Comparação de desempenho:")
    linha(f"    Tempo DP        : {alocacao['tempo_dp_segundos']:.6f}s")
    linha(f"    Força bruta est.: {alocacao['tempo_forca_bruta_estimado']:.4f}s")
    linha(f"    Speedup         : ≈ {alocacao['speedup_estimado']:,.0f}×")

    # ── Conclusão ───────────────────────────────────────────────────
    titulo("7. CONCLUSÃO")
    linha("  O sistema integra dados reais de satélite (NASA FIRMS)")
    linha("  com quatro classes de algoritmos para suporte à decisão")
    linha("  em combate a incêndios florestais no Brasil:")
    linha("")
    linha("  • Grafo      → modelagem da rede de focos e bases")
    linha("  • Dijkstra   → rota ótima para deslocamento de equipes")
    linha("  • Guloso     → posicionamento eficiente de brigadas")
    linha("  • Monte Carlo → quantificação de risco de propagação")
    linha("  • DP Knapsack → alocação ótima de orçamento por região")

    # Salva
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    log.info(f"Relatório salvo: {path}")
