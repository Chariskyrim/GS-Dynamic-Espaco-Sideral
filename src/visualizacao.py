"""
src/visualizacao.py
-------------------
Geração de gráficos com matplotlib.
"""

import logging
import os
from typing import Any

log = logging.getLogger(__name__)


def visualizar_grafo(
    grafo: Any,
    caminho_dijkstra: list[str],
    brigadas: list[dict],
    path: str = "output/grafo_incendios.png",
) -> None:
    """Plota o grafo de focos com o caminho Dijkstra e posição das brigadas."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        log.warning("matplotlib não instalado. Pulando visualização do grafo.")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor("#0d1117")
    fig.patch.set_facecolor("#0d1117")

    # Arestas do grafo
    nos_desenhados: set[str] = set()
    for u, vizinhos in grafo.adj.items():
        if u not in grafo.nos:
            continue
        nu = grafo.nos[u]
        for v in vizinhos:
            if v in nos_desenhados or v not in grafo.nos:
                continue
            nv = grafo.nos[v]
            ax.plot(
                [nu["lon"], nv["lon"]], [nu["lat"], nv["lat"]],
                color="#2a4a6b", linewidth=0.4, alpha=0.4, zorder=1,
            )
        nos_desenhados.add(u)

    # Caminho Dijkstra destacado
    caminho_set = set(zip(caminho_dijkstra[:-1], caminho_dijkstra[1:]))
    for u, v in caminho_set:
        if u in grafo.nos and v in grafo.nos:
            nu, nv = grafo.nos[u], grafo.nos[v]
            ax.plot(
                [nu["lon"], nv["lon"]], [nu["lat"], nv["lat"]],
                color="#00d4ff", linewidth=2.5, alpha=0.9, zorder=3,
            )

    # Focos de calor
    focos = [(nid, nd) for nid, nd in grafo.nos.items() if nd.get("tipo") == "foco"]
    if focos:
        lons = [nd["lon"] for _, nd in focos]
        lats = [nd["lat"] for _, nd in focos]
        frps = [nd.get("frp", 10) for _, nd in focos]
        sc = ax.scatter(
            lons, lats, c=frps, cmap="YlOrRd",
            s=[max(20, f * 1.5) for f in frps],
            alpha=0.8, zorder=4, edgecolors="#ff4400", linewidths=0.3,
        )
        plt.colorbar(sc, ax=ax, label="FRP (MW)", pad=0.02)

    # Bases de bombeiros
    for nid, nd in grafo.nos.items():
        if nd.get("tipo") == "base":
            ax.scatter(
                nd["lon"], nd["lat"],
                marker="^", s=150, color="#00ff88",
                zorder=5, edgecolors="white", linewidths=1,
            )
            ax.annotate(
                nd.get("nome", nid).split("—")[0].strip(),
                (nd["lon"], nd["lat"]),
                textcoords="offset points", xytext=(5, 5),
                fontsize=7, color="#00ff88",
            )

    # Brigadas
    for b in brigadas:
        ax.scatter(
            b["lon"], b["lat"],
            marker="*", s=220, color="#ffdd00",
            zorder=6, edgecolors="#ff8800", linewidths=1,
        )

    # Destaque nos-do-caminho
    for nid in caminho_dijkstra:
        if nid in grafo.nos:
            nd = grafo.nos[nid]
            ax.scatter(nd["lon"], nd["lat"], s=90, color="#00d4ff",
                       zorder=7, edgecolors="white", linewidths=1)

    # Legenda
    handles = [
        mpatches.Patch(color="#e84040", label="Focos de calor (tamanho ∝ FRP)"),
        mpatches.Patch(color="#00ff88", label="Bases de bombeiros"),
        mpatches.Patch(color="#ffdd00", label="Brigadas (Algoritmo Guloso)"),
        mpatches.Patch(color="#00d4ff", label="Caminho mínimo (Dijkstra)"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8,
              facecolor="#1a2a3a", edgecolor="gray", labelcolor="white")

    ax.set_xlabel("Longitude", color="white", fontsize=9)
    ax.set_ylabel("Latitude", color="white", fontsize=9)
    ax.tick_params(colors="gray")
    for spine in ax.spines.values():
        spine.set_edgecolor("#2a4a6b")
    ax.set_title(
        "Rede de Focos de Incêndio — Brasil\n"
        "Grafo, Caminho Mínimo (Dijkstra) e Cobertura de Brigadas (Guloso)",
        color="white", fontsize=11, pad=10,
    )
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    log.info(f"Grafo salvo: {path}")


def visualizar_mapa_calor(
    focos: list[dict],
    simulacao: dict[str, Any],
    path: str = "output/mapa_calor.png",
) -> None:
    """Plota mapa de calor com probabilidade de propagação e distribuição."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
    except ImportError:
        log.warning("matplotlib não instalado. Pulando mapa de calor.")
        return

    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig = plt.figure(figsize=(14, 6), facecolor="#0d1117")
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)

    # ── Painel 1: Mapa de risco por célula ──────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#0d1117")

    mapa = simulacao.get("mapa_risco", {})
    if mapa:
        lats_r = [k[0] * 0.09 for k in mapa]
        lons_r = [k[1] * 0.09 for k in mapa]
        probs = list(mapa.values())
        sc = ax1.scatter(
            lons_r, lats_r, c=probs, cmap="hot",
            s=8, alpha=0.6, vmin=0, vmax=1,
        )
        plt.colorbar(sc, ax=ax1, label="P(afetado)", fraction=0.03)

    # Focos reais sobrepostos
    if focos:
        ax1.scatter(
            [f["lon"] for f in focos],
            [f["lat"] for f in focos],
            c="cyan", s=15, zorder=5, alpha=0.8, label="Focos reais",
        )

    ax1.set_title("Mapa de Risco — Monte Carlo", color="white", fontsize=10)
    ax1.set_xlabel("Longitude", color="gray", fontsize=8)
    ax1.set_ylabel("Latitude", color="gray", fontsize=8)
    ax1.tick_params(colors="gray")
    for sp in ax1.spines.values():
        sp.set_edgecolor("#2a4a6b")

    # ── Painel 2: Histograma da distribuição de áreas ────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#0d1117")

    dist = simulacao.get("distribuicao_amostral", [])
    if dist:
        ax2.hist(dist, bins=40, color="#ff4400", alpha=0.75, edgecolor="none")
        p95 = simulacao.get("area_p95_km2", 0)
        media = simulacao.get("area_media_km2", 0)
        ax2.axvline(media, color="cyan", linestyle="--", linewidth=1.5,
                    label=f"Média: {media:.0f} km²")
        ax2.axvline(p95, color="yellow", linestyle=":", linewidth=1.5,
                    label=f"P95: {p95:.0f} km²")
        ax2.legend(fontsize=8, facecolor="#1a2a3a", edgecolor="gray", labelcolor="white")

    ax2.set_title("Distribuição — Área Propagada", color="white", fontsize=10)
    ax2.set_xlabel("Área afetada (km²)", color="gray", fontsize=8)
    ax2.set_ylabel("Frequência", color="gray", fontsize=8)
    ax2.tick_params(colors="gray")
    for sp in ax2.spines.values():
        sp.set_edgecolor("#2a4a6b")

    plt.suptitle(
        "Simulação Monte Carlo — Propagação de Incêndios",
        color="white", fontsize=12, y=1.01,
    )
    plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    log.info(f"Mapa de calor salvo: {path}")
