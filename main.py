"""
=============================================================
  GS — Monitoramento de Incêndios Florestais via Satélite
  Disciplina: Estruturas de Dados e Algoritmos
  Tema: Incêndios florestais e focos de calor
=============================================================
  Algoritmos implementados:
    1. Grafos          — rede de focos de calor por proximidade
    2. Dijkstra        — caminho mínimo de resposta entre bases
    3. Algoritmo Guloso — cobertura mínima de brigadas
    4. Algoritmo Random — simulação Monte Carlo de propagação
    5. Prog. Dinâmica  — alocação ótima de recursos por região
=============================================================
"""

import logging
import os
import sys
import time


from src.data_loader import DataLoader
from src.grafo import GrafoIncendios
from src.dijkstra import dijkstra, reconstruir_caminho
from src.guloso import cobertura_gulosa
from src.randomizado import simulacao_propagacao
from src.dinamico import alocacao_recursos
from src.relatorio import gerar_relatorio
from src.visualizacao import visualizar_grafo, visualizar_mapa_calor

# ── Configuração de log ──────────────────────────────────────
# Garante que pastas existam antes de configurar log/arquivos
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/execucao.log", encoding="utf-8"),
    ],
)

log = logging.getLogger(__name__)


def separador(titulo: str) -> None:
    log.info("")
    log.info("=" * 60)
    log.info(f"  {titulo}")
    log.info("=" * 60)


def main() -> None:
    log.info("Iniciando sistema de monitoramento de incêndios florestais")
    inicio_total = time.perf_counter()

    # ── 1. CARREGAMENTO DE DADOS ─────────────────────────────
    separador("1. CARREGAMENTO E PRÉ-PROCESSAMENTO DE DADOS")
    loader = DataLoader()
    focos = loader.carregar_focos()
    bases = loader.carregar_bases_bombeiros()
    regioes = loader.carregar_regioes()
    log.info(f"  Focos carregados  : {len(focos)}")
    log.info(f"  Bases de bombeiros: {len(bases)}")
    log.info(f"  Regiões analisadas: {len(regioes)}")

    # ── 2. CONSTRUÇÃO DO GRAFO ───────────────────────────────
    separador("2. CONSTRUÇÃO DO GRAFO DE FOCOS")
    t0 = time.perf_counter()
    grafo = GrafoIncendios(raio_km=400)
    grafo.construir(focos, bases)
    t1 = time.perf_counter()
    log.info(f"  Nós   : {grafo.num_nos()}")
    log.info(f"  Arestas: {grafo.num_arestas()}")
    log.info(f"  Componentes conectados: {grafo.num_componentes()}")
    log.info(f"  Tempo de construção: {t1 - t0:.4f}s")

    # ── 3. DIJKSTRA — CAMINHO MÍNIMO ────────────────────────
    separador("3. DIJKSTRA — CAMINHO MÍNIMO DE RESPOSTA")
    t0 = time.perf_counter()
    base_origem = "BASE_SP"
    foco_critico = grafo.foco_mais_critico()
    distancias, predecessores = dijkstra(grafo, base_origem)
    caminho = reconstruir_caminho(predecessores, base_origem, foco_critico)
    t1 = time.perf_counter()
    dist_km = distancias.get(foco_critico, float("inf"))
    log.info(f"  Origem  : {base_origem}")
    log.info(f"  Destino : {foco_critico} (foco mais crítico)")
    log.info(f"  Distância mínima: {dist_km:.1f} km")
    log.info(f"  Caminho : {' → '.join(caminho)}")
    log.info(f"  Tempo Dijkstra : {t1 - t0:.6f}s")

    # Comparação: força bruta (BFS ingênuo)
    t0 = time.perf_counter()
    _ = grafo.bfs_distancia(base_origem, foco_critico)
    t1 = time.perf_counter()
    log.info(f"  Tempo BFS (força bruta): {t1 - t0:.6f}s")

    # ── 4. ALGORITMO GULOSO — COBERTURA DE BRIGADAS ─────────
    separador("4. ALGORITMO GULOSO — COBERTURA MÍNIMA DE BRIGADAS")
    t0 = time.perf_counter()
    brigadas, focos_cobertos = cobertura_gulosa(
        focos, raio_cobertura_km=200, max_brigadas=5
    )
    t1 = time.perf_counter()
    pct = 100 * len(focos_cobertos) / len(focos) if focos else 0
    log.info(f"  Brigadas alocadas: {len(brigadas)}")
    log.info(f"  Focos cobertos   : {len(focos_cobertos)} / {len(focos)} ({pct:.1f}%)")
    for i, b in enumerate(brigadas, 1):
        log.info(f"    Brigada {i}: lat={b['lat']:.2f}, lon={b['lon']:.2f}, "
                 f"focos={b['focos_cobertos']}, FRP_total={b['frp_total']:.0f}")
    log.info(f"  Tempo guloso: {t1 - t0:.6f}s")

    # ── 5. ALGORITMO RANDOMIZADO — SIMULAÇÃO MONTE CARLO ────
    separador("5. MONTE CARLO — SIMULAÇÃO DE PROPAGAÇÃO")
    t0 = time.perf_counter()
    resultado_sim = simulacao_propagacao(
        focos, n_simulacoes=500, passos=10, prob_base=0.35
    )
    t1 = time.perf_counter()
    log.info(f"  Simulações      : {resultado_sim['n_simulacoes']}")
    log.info(f"  Área média afetada : {resultado_sim['area_media_km2']:.1f} km²")
    log.info(f"  Área máx. (95°p): {resultado_sim['area_p95_km2']:.1f} km²")
    log.info(f"  Risco alto (>60%): {resultado_sim['zonas_risco_alto']} zonas")
    log.info(f"  Tempo simulação : {t1 - t0:.4f}s")

    # ── 6. PROGRAMAÇÃO DINÂMICA — ALOCAÇÃO DE RECURSOS ──────
    separador("6. PROG. DINÂMICA — ALOCAÇÃO ÓTIMA DE RECURSOS")
    t0 = time.perf_counter()
    resultado_pd = alocacao_recursos(regioes, orcamento_total=100)
    t1 = time.perf_counter()
    log.info(f"  Orçamento total : R$ {resultado_pd['orcamento_usado']:.0f}M")
    log.info(f"  Impacto máximo  : {resultado_pd['impacto_total']:.1f} pts")
    log.info(f"  Regiões atendidas:")
    for r in resultado_pd["regioes_selecionadas"]:
        log.info(f"    {r['nome']:20s} custo=R${r['custo']}M  impacto={r['impacto']}")
    log.info(f"  Tempo DP        : {t1 - t0:.6f}s")
    log.info(f"  Comparação — força bruta O(2^n): estimado {resultado_pd['tempo_forca_bruta_estimado']:.4f}s")

    # ── 7. VISUALIZAÇÕES ────────────────────────────────────
    separador("7. GERAÇÃO DE VISUALIZAÇÕES")
    try:
        visualizar_grafo(grafo, caminho, brigadas, "output/grafo_incendios.png")
        visualizar_mapa_calor(focos, resultado_sim, "output/mapa_calor.png")
        log.info("  Gráficos salvos em output/")
    except Exception as e:
        log.warning(f"  Visualização não gerada: {e}")

    # ── 8. RELATÓRIO FINAL ──────────────────────────────────
    separador("8. RELATÓRIO FINAL")
    gerar_relatorio(
        focos=focos,
        bases=bases,
        grafo=grafo,
        caminho_dijkstra=caminho,
        distancia_dijkstra=dist_km,
        brigadas=brigadas,
        focos_cobertos=focos_cobertos,
        simulacao=resultado_sim,
        alocacao=resultado_pd,
        path="output/relatorio_final.txt",
    )
    log.info("  Relatório salvo em output/relatorio_final.txt")

    fim_total = time.perf_counter()
    separador("EXECUÇÃO CONCLUÍDA")
    log.info(f"  Tempo total: {fim_total - inicio_total:.2f}s")


if __name__ == "__main__":
    main()
