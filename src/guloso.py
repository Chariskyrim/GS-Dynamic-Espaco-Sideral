"""
src/guloso.py
-------------
Algoritmo Guloso — Cobertura Mínima de Brigadas.

Estratégia: a cada iteração, posiciona uma brigada no centroide
do cluster de focos não cobertos com maior FRP acumulado.
Equivalente ao problema Set Cover com peso.

Complexidade: O(k * n) onde k = brigadas alocadas, n = focos.

Aplicação: decide onde posicionar equipes de combate para
maximizar a cobertura de focos com maior poder radiativo.
"""

import logging
import math
from typing import Any

log = logging.getLogger(__name__)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2
         + math.cos(phi1) * math.cos(phi2)
         * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(a))


def cobertura_gulosa(
    focos: list[dict[str, Any]],
    raio_cobertura_km: float = 200.0,
    max_brigadas: int = 5,
) -> tuple[list[dict], list[str]]:
    """
    Algoritmo guloso para cobertura de focos por brigadas.

    A cada passo:
      1. Calcula, para cada foco não coberto, a soma de FRP
         de todos os focos que seriam cobertos se a brigada
         fosse posicionada ali.
      2. Escolhe o foco com maior FRP total (escolha gulosa).
      3. Marca todos os focos no raio como cobertos.
      4. Repete até atingir max_brigadas ou cobrir tudo.

    Parâmetros
    ----------
    focos : list[dict]
        Lista de focos com lat, lon, frp, id
    raio_cobertura_km : float
        Raio de atuação de cada brigada
    max_brigadas : int
        Número máximo de brigadas disponíveis

    Retorna
    -------
    brigadas : list[dict]
        Brigadas alocadas com posição e estatísticas
    focos_cobertos : list[str]
        IDs de todos os focos cobertos
    """
    if not focos:
        return [], []

    nao_cobertos = {f["id"]: f for f in focos}
    brigadas: list[dict] = []
    ids_cobertos: set[str] = set()

    iteracao = 0
    while nao_cobertos and len(brigadas) < max_brigadas:
        iteracao += 1
        melhor_foco_id = None
        melhor_frp = -1.0
        melhor_cobertura: list[str] = []

        # Avalia cada foco não coberto como candidato a posição de brigada
        for fid, foco_candidato in nao_cobertos.items():
            cobertos_aqui = []
            frp_aqui = 0.0

            for fid2, foco2 in nao_cobertos.items():
                dist = haversine(
                    foco_candidato["lat"], foco_candidato["lon"],
                    foco2["lat"], foco2["lon"],
                )
                if dist <= raio_cobertura_km:
                    cobertos_aqui.append(fid2)
                    frp_aqui += foco2.get("frp", 0)

            # Escolha gulosa: maximiza FRP coberto
            if frp_aqui > melhor_frp:
                melhor_frp = frp_aqui
                melhor_foco_id = fid
                melhor_cobertura = cobertos_aqui

        if melhor_foco_id is None:
            break

        foco_base = nao_cobertos[melhor_foco_id]

        # Calcula centroide dos focos cobertos para posicionar a brigada
        lat_c = sum(nao_cobertos[fid]["lat"] for fid in melhor_cobertura) / len(melhor_cobertura)
        lon_c = sum(nao_cobertos[fid]["lon"] for fid in melhor_cobertura) / len(melhor_cobertura)

        brigada = {
            "id": f"BRIGADA_{iteracao:02d}",
            "lat": round(lat_c, 4),
            "lon": round(lon_c, 4),
            "focos_cobertos": len(melhor_cobertura),
            "frp_total": round(melhor_frp, 1),
            "ids_focos": melhor_cobertura,
            "raio_km": raio_cobertura_km,
        }
        brigadas.append(brigada)

        # Remove focos cobertos
        for fid in melhor_cobertura:
            ids_cobertos.add(fid)
            nao_cobertos.pop(fid, None)

        log.debug(
            f"  Brigada {iteracao}: pos=({lat_c:.2f},{lon_c:.2f}) "
            f"cobre {len(melhor_cobertura)} focos, FRP={melhor_frp:.0f}MW"
        )

    focos_cobertos = list(ids_cobertos)
    log.info(
        f"Guloso: {len(brigadas)} brigadas cobrem "
        f"{len(focos_cobertos)}/{len(focos)} focos "
        f"({100 * len(focos_cobertos) / len(focos):.1f}%)"
    )
    return brigadas, focos_cobertos
