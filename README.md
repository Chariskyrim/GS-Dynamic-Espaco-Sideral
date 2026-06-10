# 🔥 Monitoramento de Incêndios Florestais via Satélite

**Disciplina:** Estruturas de Dados e Algoritmos  
**Tema:** Incêndios florestais e focos de calor  
**Semestre:** 2º Semestre — Global Solution  

---

## 📌 Descrição do Projeto

Sistema de análise e suporte à decisão para combate a incêndios florestais no Brasil, utilizando dados reais de satélite da NASA (FIRMS/VIIRS) e algoritmos avançados para:

- Modelar a rede de focos de calor como um **grafo geográfico**
- Calcular a **rota ótima** de deslocamento de equipes de bombeiros
- Determinar o **posicionamento ideal de brigadas** com cobertura máxima
- **Simular a propagação** do fogo sob incerteza via Monte Carlo
- Realizar **alocação ótima de orçamento** por região prioritária

---

## 🎯 Objetivo da Solução

Fornecer uma ferramenta computacional que auxilie o PREVFOGO e Corpos de Bombeiros a tomar decisões baseadas em dados satelitais reais, otimizando o uso de recursos limitados frente a eventos de incêndio de larga escala.

---

## 🌎 Tema Escolhido

**Incêndios florestais e focos de calor** — o Brasil concentra uma das maiores incidências mundiais de focos de calor, especialmente no Cerrado e Amazônia. A análise em tempo real com dados de satélite é fundamental para resposta rápida e planejamento preventivo.

---

## 📡 Fonte dos Dados

| Fonte | Descrição | Link |
|-------|-----------|------|
| NASA FIRMS VIIRS | Focos de calor detectados pelo satélite Suomi NPP | [firms.modaps.eosdis.nasa.gov](https://firms.modaps.eosdis.nasa.gov/api/) |
| PREVFOGO/IBAMA | Estrutura de referência para bases de brigadas | [ibama.gov.br](https://www.ibama.gov.br/prevfogo) |

> A aplicação tenta carregar dados em tempo real da API NASA FIRMS. Em caso de indisponibilidade, utiliza dados simulados com distribuição geográfica e estatística representativa do Brasil (seed fixo para reprodutibilidade).

---

## ⚙️ Algoritmos Implementados

### 1. 🗺️ Grafos (`src/grafo.py`)
- **Estrutura:** lista de adjacência `dict[str, dict[str, float]]`
- **Nós:** focos de calor + bases de bombeiros
- **Arestas:** pares de nós dentro de um raio (padrão: 150 km), ponderadas pela distância Haversine
- **Operações:** construção O(n²), BFS, contagem de componentes, grau médio

### 2. 🔵 Dijkstra — Caminho Mínimo (`src/dijkstra.py`)
- **Complexidade:** O((V + E) log V) com heap binário (`heapq`)
- **Aplicação:** rota mais curta em km da base de bombeiros até o foco com maior FRP
- **Comparação:** benchmarkado contra BFS (força bruta sem peso)

### 3. 🟢 Algoritmo Guloso — Cobertura de Brigadas (`src/guloso.py`)
- **Estratégia:** a cada passo, posiciona a brigada no centroide que maximiza o FRP total coberto
- **Complexidade:** O(k × n)
- **Aplicação:** decide posicionamento ótimo de até 5 brigadas de combate

### 4. 🎲 Algoritmo Randomizado — Monte Carlo (`src/randomizado.py`)
- **Técnica:** simulação probabilística de propagação em grade discreta
- **Parâmetros:** direção de vento aleatória por simulação, prob. influenciada por FRP
- **Saída:** distribuição de área afetada, percentis P50/P95/P99, zonas de risco alto

### 5. 📐 Programação Dinâmica — Alocação de Recursos (`src/dinamico.py`)
- **Algoritmo:** Knapsack 0/1 com tabela DP 2D e reconstrução de solução
- **Complexidade:** O(n × W) vs O(2ⁿ) da força bruta
- **Aplicação:** maximiza o impacto de intervenções dado orçamento limitado (R$ 100M)

---

## 🗂️ Modelagem com Grafos

```
Nós:   focos de calor (F0000..F0190)  +  bases bombeiros (BASE_SP, BASE_MT, ...)
Arestas: distância Haversine ≤ raio_km (padrão 150 km)
Peso:  distância em km (grafo ponderado, não-dirigido)

Aplicações no projeto:
  • Dijkstra percorre o grafo para encontrar rota mínima BASE → FOCO_CRÍTICO
  • BFS percorre para contagem de componentes conectados
  • Guloso usa distâncias Haversine (sem grafo) para cobertura por raio
```

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso |
|------------|-----|
| Python 3.11+ | Linguagem principal |
| `heapq` (stdlib) | Dijkstra com heap binário |
| `collections.deque` (stdlib) | BFS no grafo |
| `urllib` (stdlib) | Requisições à API NASA FIRMS |
| `json`, `csv`, `logging` (stdlib) | I/O e logs |
| `matplotlib` | Visualizações (grafo, mapa de calor, histograma) |
| `random`, `math` (stdlib) | Monte Carlo e Haversine |

---

## 📁 Estrutura do Projeto

```
gs_incendios/
├── main.py                  # Ponto de entrada principal
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── data_loader.py       # Carregamento NASA FIRMS + fallback
│   ├── grafo.py             # Estrutura de grafo e operações
│   ├── dijkstra.py          # Caminho mínimo com heap
│   ├── guloso.py            # Cobertura de brigadas
│   ├── randomizado.py       # Monte Carlo de propagação
│   ├── dinamico.py          # Knapsack DP para alocação
│   ├── visualizacao.py      # Gráficos com matplotlib
│   └── relatorio.py         # Relatório textual completo
├── data/
│   └── focos_cache.json     # Cache automático (gerado na execução)
├── logs/
│   └── execucao.log         # Log completo (gerado na execução)
└── output/
    ├── grafo_incendios.png  # Visualização do grafo
    ├── mapa_calor.png       # Mapa de propagação Monte Carlo
    └── relatorio_final.txt  # Relatório completo
```

---

## ▶️ Instruções de Execução

### Pré-requisitos
```bash
python --version   # Python 3.11+
```

### Instalação
```bash
git clone https://github.com/seu-usuario/gs-incendios-florestais.git
cd gs-incendios-florestais
pip install -r requirements.txt
```

### Execução
```bash
python main.py
```

Os resultados são gerados em `output/` e os logs em `logs/execucao.log`.

### Saída esperada
```
[INFO] Iniciando sistema de monitoramento de incêndios florestais
[INFO] ============================================================
[INFO]   1. CARREGAMENTO E PRÉ-PROCESSAMENTO DE DADOS
...
[INFO]   Focos carregados  : 191
[INFO]   Bases de bombeiros: 7
...
[INFO]   Dijkstra: distância mínima: 312.4 km
...
[INFO]   Guloso: 5 brigadas cobrem 185/191 focos (96.9%)
...
[INFO]   Monte Carlo: média=12500km², P95=28700km²
...
[INFO]   DP Knapsack: speedup ≈ 102400×
[INFO] Tempo total: 2.31s
```

---

## 👥 Integrantes

| Nome Completo | RM |
|---------------|----|
| [Nome do Integrante 1] | RM XXXXX |
| [Nome do Integrante 2] | RM XXXXX |
| [Nome do Integrante 3] | RM XXXXX |

---

## 📄 Licença

Projeto acadêmico — FIAP 2025. Dados NASA FIRMS sob [licença pública NASA](https://firms.modaps.eosdis.nasa.gov/api/).
