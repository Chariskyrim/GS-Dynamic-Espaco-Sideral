"""
src/data_loader.py
------------------
Carrega focos de calor da API NASA FIRMS (MODIS/VIIRS) e
bases de bombeiros de arquivo CSV local.

Fonte dos dados:
  - NASA FIRMS: https://firms.modaps.eosdis.nasa.gov/api/
  - Bases: dados simulados representando estrutura real do
    Corpo de Bombeiros do Estado de São Paulo / PREVFOGO
"""

import csv
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any

import urllib.request
import urllib.error

log = logging.getLogger(__name__)

# Chave pública de demonstração da NASA FIRMS
# (limite: 30 requisições/IP/hora — suficiente para o projeto)
NASA_FIRMS_MAP_KEY = "DEMO_KEY"
NASA_FIRMS_URL = (
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    "{key}/VIIRS_SNPP_NRT/{area}/{days}"
)
# Bounding box: Brasil aproximado
BRASIL_AREA = "-73.99,-33.75,-34.73,5.27"


class DataLoader:
    """Responsável por carregar e normalizar todas as fontes de dados."""

    def __init__(self, cache_path: str = "data/focos_cache.json"):
        self.cache_path = cache_path

    # ── Focos de Calor ────────────────────────────────────────────────
    def carregar_focos(self) -> list[dict[str, Any]]:
        """
        Tenta carregar da API NASA FIRMS.
        Em caso de falha (sem internet, limite de requisições),
        carrega de CSV local pré-salvo.
        """
        # Tenta cache recente (< 1 hora)
        focos = self._carregar_cache()
        if focos:
            log.info("Focos carregados do cache local")
            return focos

        # Tenta API NASA
        try:
            focos = self._buscar_nasa_firms(days=7)
            self._salvar_cache(focos)
            log.info(f"Focos obtidos da API NASA FIRMS: {len(focos)} registros")
            return focos
        except Exception as e:
            log.warning(f"API NASA indisponível ({e}). Usando dados locais.")

        # Fallback: CSV local embutido
        focos = self._gerar_dados_simulados()
        self._salvar_cache(focos)
        log.info(f"Dados simulados (estrutura FIRMS real): {len(focos)} registros")
        return focos

    def _buscar_nasa_firms(self, days: int = 7) -> list[dict]:
        url = NASA_FIRMS_URL.format(
            key=NASA_FIRMS_MAP_KEY,
            area=BRASIL_AREA,
            days=days,
        )
        req = urllib.request.Request(url, headers={"User-Agent": "GS-Incendios/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8").splitlines()

        reader = csv.DictReader(content)
        focos = []
        for row in reader:
            try:
                focos.append({
                    "id": f"F{len(focos):04d}",
                    "lat": float(row["latitude"]),
                    "lon": float(row["longitude"]),
                    "frp": float(row.get("frp", 0) or 0),          # Fire Radiative Power (MW)
                    "brightness": float(row.get("bright_ti4", 0) or 0),
                    "confidence": row.get("confidence", "nominal"),
                    "data": row.get("acq_date", ""),
                    "hora": row.get("acq_time", ""),
                    "satelite": row.get("satellite", "VIIRS"),
                    "bioma": _inferir_bioma(float(row["latitude"]), float(row["longitude"])),
                })
            except (ValueError, KeyError):
                continue
        return focos

    def _gerar_dados_simulados(self) -> list[dict]:
        """
        Gera focos representativos do Brasil com distribuição
        geográfica real (concentração no Cerrado e Amazônia).
        Estrutura idêntica à API FIRMS para troca transparente.
        """
        import random
        random.seed(42)

        # Regiões com maior incidência histórica
        clusters = [
            # (lat_centro, lon_centro, raio, n_focos, bioma, frp_medio)
            (-12.5, -55.0, 4.0, 35, "Cerrado",  45.0),   # MT centro
            (-10.0, -52.0, 3.5, 28, "Amazônia", 62.0),   # PA/MT
            (-8.5,  -45.0, 3.0, 22, "Cerrado",  38.0),   # PI/TO
            (-15.0, -47.5, 2.5, 18, "Cerrado",  29.0),   # GO/DF
            (-3.5,  -62.0, 4.0, 24, "Amazônia", 71.0),   # AM
            (-6.0,  -35.0, 2.0, 14, "Caatinga", 22.0),   # RN/PB
            (-19.5, -44.0, 2.0, 12, "Cerrado",  31.0),   # MG
            (-22.5, -47.0, 1.5,  8, "Mata Atlântica", 19.0),  # SP interior
            (-5.0,  -49.0, 3.0, 20, "Amazônia", 55.0),   # PA
            (-13.0, -39.0, 2.0, 10, "Mata Atlântica", 24.0),  # BA
        ]

        focos = []
        hoje = datetime.now()
        for lat_c, lon_c, raio, n, bioma, frp_med in clusters:
            for _ in range(n):
                lat = lat_c + random.uniform(-raio, raio)
                lon = lon_c + random.uniform(-raio, raio)
                dias_atras = random.randint(0, 6)
                dt = hoje - timedelta(days=dias_atras)
                frp = max(1.0, random.gauss(frp_med, frp_med * 0.3))
                focos.append({
                    "id": f"F{len(focos):04d}",
                    "lat": round(lat, 4),
                    "lon": round(lon, 4),
                    "frp": round(frp, 1),
                    "brightness": round(300 + frp * 1.2 + random.gauss(0, 5), 1),
                    "confidence": random.choice(["low", "nominal", "high"]),
                    "data": dt.strftime("%Y-%m-%d"),
                    "hora": f"{random.randint(0,23):02d}{random.randint(0,59):02d}",
                    "satelite": random.choice(["VIIRS", "MODIS"]),
                    "bioma": bioma,
                })
        return focos

    def _salvar_cache(self, focos: list) -> None:
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "focos": focos}, f)
        except OSError as e:
            log.warning(f"Não foi possível salvar cache: {e}")

    def _carregar_cache(self) -> list | None:
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)
            # Cache válido por 1 hora
            if time.time() - data["timestamp"] < 3600:
                return data["focos"]
        except (OSError, KeyError, json.JSONDecodeError):
            pass
        return None

    # ── Bases de Bombeiros ────────────────────────────────────────────
    def carregar_bases_bombeiros(self) -> list[dict]:
        """
        Bases do PREVFOGO / Corpo de Bombeiros com coordenadas reais.
        """
        bases = [
            {"id": "BASE_SP",  "nome": "Base SP — Campinas",      "lat": -22.90, "lon": -47.06, "equipes": 4},
            {"id": "BASE_MT",  "nome": "Base MT — Cuiabá",         "lat": -15.60, "lon": -56.10, "equipes": 6},
            {"id": "BASE_PA",  "nome": "Base PA — Belém",          "lat": -1.46,  "lon": -48.50, "equipes": 5},
            {"id": "BASE_GO",  "nome": "Base GO — Goiânia",        "lat": -16.68, "lon": -49.25, "equipes": 4},
            {"id": "BASE_AM",  "nome": "Base AM — Manaus",         "lat": -3.10,  "lon": -60.02, "equipes": 5},
            {"id": "BASE_BA",  "nome": "Base BA — Feira de Santana","lat": -12.27, "lon": -38.96, "equipes": 3},
            {"id": "BASE_PI",  "nome": "Base PI — Teresina",       "lat": -5.09,  "lon": -42.80, "equipes": 3},
        ]
        return bases

    # ── Regiões para Programação Dinâmica ────────────────────────────
    def carregar_regioes(self) -> list[dict]:
        """
        Regiões prioritárias com custo de intervenção e
        impacto estimado (índice composto de área + biodiversidade).
        """
        return [
            {"nome": "Amazônia Ocidental",  "custo": 30, "impacto": 95, "focos_historico": 1200},
            {"nome": "Cerrado MT/PA",       "custo": 25, "impacto": 80, "focos_historico": 980},
            {"nome": "Pantanal",            "custo": 20, "impacto": 85, "focos_historico": 760},
            {"nome": "Cerrado GO/DF",       "custo": 15, "impacto": 60, "focos_historico": 540},
            {"nome": "Caatinga NE",         "custo": 12, "impacto": 50, "focos_historico": 420},
            {"nome": "Mata Atlântica SP",   "custo": 18, "impacto": 70, "focos_historico": 310},
            {"nome": "Pampa RS",            "custo":  8, "impacto": 35, "focos_historico": 180},
            {"nome": "Mata Atlântica BA",   "custo": 14, "impacto": 55, "focos_historico": 290},
            {"nome": "Amazônia Oriental",   "custo": 28, "impacto": 90, "focos_historico": 1050},
            {"nome": "Tocantins/Araguaia",  "custo": 16, "impacto": 65, "focos_historico": 600},
        ]


def _inferir_bioma(lat: float, lon: float) -> str:
    """Inferência simplificada de bioma por coordenada."""
    if lat > -12 and lon < -50:
        return "Amazônia"
    if -20 < lat < -5 and lon > -50:
        return "Caatinga"
    if lat < -28:
        return "Pampa"
    if -20 < lat < -12:
        return "Cerrado"
    return "Mata Atlântica"
