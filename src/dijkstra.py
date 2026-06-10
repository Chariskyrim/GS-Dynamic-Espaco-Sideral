"""
src/dijkstra.py
---------------
Algoritmo de Caminho Mínimo — Dijkstra com heap binário.

Complexidade: O((V + E) log V)

Aplicação no projeto:
    Encontrar a rota mais curta (em km) de uma base de bombeiros
    até o foco de incêndio mais crítico, percorrendo a rede de
    focos intermediários.
"""

import heapq
import logging
from typing import Any

log = logging.getLogger(__name__)


def dijkstra(
    grafo: Any,
    origem: str,
) -> tuple[dict[str, float], dict[str, str | None]]:
    """
    Executa Dijkstra a partir de `origem` no grafo fornecido.

    Parâmetros
    ----------
    grafo : GrafoIncendios
        Grafo com método `vizinhos(no) -> dict[str, float]`
    origem : str
        ID do nó de partida

    Retorna
    -------
    distancias : dict[str, float]
        Distância mínima da origem a cada nó
    predecessores : dict[str, str | None]
        Predecessor de cada nó no caminho mínimo
    """
    distancias: dict[str, float] = {no: float("inf") for no in grafo.nos}
    predecessores: dict[str, str | None] = {no: None for no in grafo.nos}

    if origem not in distancias:
        log.error(f"Nó de origem '{origem}' não encontrado no grafo")
        return distancias, predecessores

    distancias[origem] = 0.0
    # Heap: (distância, nó)
    heap: list[tuple[float, str]] = [(0.0, origem)]
    visitados: set[str] = set()

    iteracoes = 0
    while heap:
        dist_atual, no_atual = heapq.heappop(heap)
        iteracoes += 1

        if no_atual in visitados:
            continue
        visitados.add(no_atual)

        # Relaxamento das arestas
        for vizinho, peso in grafo.vizinhos(no_atual).items():
            nova_dist = dist_atual + peso
            if nova_dist < distancias[vizinho]:
                distancias[vizinho] = nova_dist
                predecessores[vizinho] = no_atual
                heapq.heappush(heap, (nova_dist, vizinho))

    log.debug(f"Dijkstra: {iteracoes} iterações, {len(visitados)} nós visitados")
    return distancias, predecessores


def reconstruir_caminho(
    predecessores: dict[str, str | None],
    origem: str,
    destino: str,
) -> list[str]:
    """
    Reconstrói o caminho mínimo de `origem` até `destino`
    usando o dicionário de predecessores retornado pelo Dijkstra.

    Retorna lista de IDs de nós, do início ao fim.
    Retorna lista vazia se não houver caminho.
    """
    caminho: list[str] = []
    atual: str | None = destino

    while atual is not None:
        caminho.append(atual)
        atual = predecessores.get(atual)
        # Evita loop infinito em grafos com ciclos inconsistentes
        if len(caminho) > len(predecessores) + 1:
            log.warning("Ciclo detectado na reconstrução do caminho")
            return []

    caminho.reverse()

    if caminho and caminho[0] == origem:
        return caminho
    return []  # Sem caminho
