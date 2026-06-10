"""
src/randomizado.py
------------------
Algoritmo Randomizado — Simulação de Monte Carlo para
propagação de incêndios florestais.

Cada simulação:
  1. Começa com focos ativos reais como sementes.
  2. A cada passo de tempo, cada célula vizinha tem
     probabilidade `prob` de ser atingida (influenciada
     por FRP e direção de vento simulada aleatoriamente).
  3. Acumula a área estimada afetada em km².

Complexidade: O(S * P * F) — S simulações, P passos, F focos.

Resultado: distribuição estatística da área afetada,
zonas de risco alto (P(afetado) > 60%) e mapa de calor.
"""

import logging
import math
import random
from typing import Any

log = logging.getLogger(__name__)

CELL_SIZE_KM = 10.0          # Cada célula da grade = 10 km²
GRID_RESOLUTION = 0.09       # ~10 km em graus (1° ≈ 111 km)


def simulacao_propagacao(
    focos: list[dict[str, Any]],
    n_simulacoes: int = 500,
    passos: int = 10,
    prob_base: float = 0.35,
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Executa simulação Monte Carlo de propagação.

    Parâmetros
    ----------
    focos : list[dict]
        Focos reais como estado inicial
    n_simulacoes : int
        Número de simulações Monte Carlo
    passos : int
        Passos de tempo por simulação (cada passo ≈ 6 horas)
    prob_base : float
        Probabilidade base de propagação por passo
    seed : int | None
        Semente para reprodutibilidade (None = aleatório)

    Retorna
    -------
    dict com estatísticas agregadas das simulações
    """
    if seed is not None:
        random.seed(seed)

    if not focos:
        return _resultado_vazio()

    # Discretiza focos em células de grade
    celulas_iniciais = _focos_para_celulas(focos)
    log.debug(f"Monte Carlo: {len(celulas_iniciais)} células iniciais")

    areas_afetadas: list[float] = []
    contagem_afetada: dict[tuple, int] = {}  # célula → nº vezes afetada

    for sim in range(n_simulacoes):
        # Estado da simulação: conjunto de células ativas
        ativas: set[tuple[int, int]] = set(celulas_iniciais.keys())
        novas: set[tuple[int, int]] = set()

        # Vento simulado: direção aleatória por simulação
        vento_dx = random.gauss(0, 1)
        vento_dy = random.gauss(0, 1)
        intensidade_vento = math.sqrt(vento_dx ** 2 + vento_dy ** 2)

        for _passo in range(passos):
            expansao: set[tuple[int, int]] = set()
            for (cx, cy) in list(ativas):
                frp_local = celulas_iniciais.get((cx, cy), {}).get("frp", 20.0)
                frp_factor = min(2.0, frp_local / 30.0)
                prob = min(0.85, prob_base * frp_factor)

                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        vizinho = (cx + dx, cy + dy)
                        if vizinho in ativas:
                            continue
                        align = (dx * vento_dx + dy * vento_dy)
                        if intensidade_vento > 0:
                            align /= (intensidade_vento * math.sqrt(dx * dx + dy * dy))
                        prob_viz = min(0.90, prob * (1.0 + 0.3 * align))
                        if random.random() < prob_viz:
                            expansao.add(vizinho)

            ativas |= expansao
            # Cap para manter simulação eficiente (máx 400 células ativas)
            if len(ativas) > 400:
                break

        # Área total afetada (km²)
        area = len(ativas) * CELL_SIZE_KM ** 2
        areas_afetadas.append(area)
        novas |= ativas

        # Acumula para mapa de probabilidade
        for cel in ativas:
            contagem_afetada[cel] = contagem_afetada.get(cel, 0) + 1

    # Estatísticas
    areas_afetadas.sort()
    n = len(areas_afetadas)
    media = sum(areas_afetadas) / n
    p50 = areas_afetadas[n // 2]
    p95 = areas_afetadas[int(n * 0.95)]
    p99 = areas_afetadas[int(n * 0.99)]

    # Zonas com probabilidade > 60% de serem afetadas
    zonas_risco_alto = sum(
        1 for cnt in contagem_afetada.values()
        if cnt / n_simulacoes > 0.60
    )

    # Mapa de risco: célula → probabilidade
    mapa_risco = {
        cel: round(cnt / n_simulacoes, 3)
        for cel, cnt in contagem_afetada.items()
    }

    resultado = {
        "n_simulacoes": n_simulacoes,
        "passos_por_sim": passos,
        "prob_base": prob_base,
        "area_media_km2": round(media, 1),
        "area_mediana_km2": round(p50, 1),
        "area_p95_km2": round(p95, 1),
        "area_p99_km2": round(p99, 1),
        "area_minima_km2": round(areas_afetadas[0], 1),
        "area_maxima_km2": round(areas_afetadas[-1], 1),
        "zonas_risco_alto": zonas_risco_alto,
        "mapa_risco": mapa_risco,
        "distribuicao_amostral": areas_afetadas,
    }
    log.info(
        f"Monte Carlo: média={media:.0f}km², P95={p95:.0f}km², "
        f"zonas_risco_alto={zonas_risco_alto}"
    )
    return resultado


def _focos_para_celulas(focos: list[dict]) -> dict[tuple[int, int], dict]:
    """Converte coordenadas geográficas em índices de grade discreta."""
    celulas: dict[tuple[int, int], dict] = {}
    for foco in focos:
        cx = int(foco["lat"] / GRID_RESOLUTION)
        cy = int(foco["lon"] / GRID_RESOLUTION)
        chave = (cx, cy)
        if chave not in celulas or foco.get("frp", 0) > celulas[chave].get("frp", 0):
            celulas[chave] = {"frp": foco.get("frp", 20.0), "id": foco["id"]}
    return celulas


def _resultado_vazio() -> dict:
    return {
        "n_simulacoes": 0, "passos_por_sim": 0, "prob_base": 0,
        "area_media_km2": 0, "area_mediana_km2": 0,
        "area_p95_km2": 0, "area_p99_km2": 0,
        "area_minima_km2": 0, "area_maxima_km2": 0,
        "zonas_risco_alto": 0, "mapa_risco": {}, "distribuicao_amostral": [],
    }
