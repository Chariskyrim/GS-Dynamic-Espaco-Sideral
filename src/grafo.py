"""
src/grafo.py
------------
Modelagem do problema com Grafo.

Nós   : focos de calor + bases de bombeiros
Arestas: conexão entre nós dentro de um raio (km), ponderada
         pela distância geográfica (Haversine).

Estrutura: lista de adjacência (dict of dict) — O(V+E) memória.
"""

import logging
import math
from collections import deque
from typing import Any

log = logging.getLogger(__name__)

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em km entre dois pontos geográficos (fórmula Haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


class GrafoIncendios:
    """
    Grafo não-dirigido ponderado.

    Atributos
    ---------
    adj : dict[str, dict[str, float]]
        Adjacência: adj[u][v] = distância_km
    nos : dict[str, dict]
        Dados de cada nó (lat, lon, tipo, frp, ...)
    raio_km : float
        Raio máximo para criar aresta entre dois nós
    """

    def __init__(self, raio_km: float = 150.0):
        self.raio_km = raio_km
        self.adj: dict[str, dict[str, float]] = {}
        self.nos: dict[str, dict[str, Any]] = {}

    # ── Construção ────────────────────────────────────────────────────
    def construir(self, focos: list[dict], bases: list[dict]) -> None:
        """Constrói o grafo a partir dos focos e bases."""
        # Adiciona nós
        for foco in focos:
            self._adicionar_no(foco["id"], {**foco, "tipo": "foco"})
        for base in bases:
            self._adicionar_no(base["id"], {**base, "tipo": "base"})

        todos = list(self.nos.values())
        n = len(todos)
        arestas_criadas = 0

        # Conecta nós dentro do raio — O(n²) aceitável para ~300 nós
        for i in range(n):
            for j in range(i + 1, n):
                ni, nj = todos[i], todos[j]
                dist = haversine(ni["lat"], ni["lon"], nj["lat"], nj["lon"])
                if dist <= self.raio_km:
                    self._adicionar_aresta(ni["id"], nj["id"], dist)
                    arestas_criadas += 1

        log.info(f"Grafo construído: {n} nós, {arestas_criadas} arestas (raio={self.raio_km}km)")

    def _adicionar_no(self, id_: str, dados: dict) -> None:
        self.nos[id_] = dados
        self.adj.setdefault(id_, {})

    def _adicionar_aresta(self, u: str, v: str, peso: float) -> None:
        self.adj[u][v] = peso
        self.adj[v][u] = peso

    # ── Consultas ─────────────────────────────────────────────────────
    def num_nos(self) -> int:
        return len(self.nos)

    def num_arestas(self) -> int:
        return sum(len(v) for v in self.adj.values()) // 2

    def vizinhos(self, no_id: str) -> dict[str, float]:
        return self.adj.get(no_id, {})

    def peso(self, u: str, v: str) -> float:
        return self.adj[u].get(v, float("inf"))

    def foco_mais_critico(self) -> str:
        """Retorna o foco com maior FRP (Fire Radiative Power)."""
        focos = [(nid, nd) for nid, nd in self.nos.items() if nd.get("tipo") == "foco"]
        if not focos:
            raise ValueError("Nenhum foco no grafo")
        return max(focos, key=lambda x: x[1].get("frp", 0))[0]

    def focos_ids(self) -> list[str]:
        return [nid for nid, nd in self.nos.items() if nd.get("tipo") == "foco"]

    def bases_ids(self) -> list[str]:
        return [nid for nid, nd in self.nos.items() if nd.get("tipo") == "base"]

    def num_componentes(self) -> int:
        """Conta componentes conectados via BFS."""
        visitados: set[str] = set()
        componentes = 0
        for no in self.nos:
            if no not in visitados:
                fila = deque([no])
                while fila:
                    atual = fila.popleft()
                    if atual in visitados:
                        continue
                    visitados.add(atual)
                    for viz in self.adj.get(atual, {}):
                        if viz not in visitados:
                            fila.append(viz)
                componentes += 1
        return componentes

    def bfs_distancia(self, origem: str, destino: str) -> float:
        """
        BFS para distância (força bruta, sem peso).
        Usado para comparação de desempenho com Dijkstra.
        """
        if origem not in self.adj or destino not in self.adj:
            return float("inf")
        visitados: set[str] = set()
        fila: deque[tuple[str, float]] = deque([(origem, 0.0)])
        while fila:
            atual, dist_acum = fila.popleft()
            if atual == destino:
                return dist_acum
            if atual in visitados:
                continue
            visitados.add(atual)
            for viz, peso in self.adj[atual].items():
                if viz not in visitados:
                    fila.append((viz, dist_acum + peso))
        return float("inf")

    def grau_medio(self) -> float:
        if not self.adj:
            return 0.0
        return sum(len(v) for v in self.adj.values()) / len(self.adj)
