[🇺🇸 English](#transaction-monitor) | [🇧🇷 Português](#monitor-de-transações)

---

# Transaction Monitor

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Kafka](https://img.shields.io/badge/Apache_Kafka-KRaft-black)
![Redis](https://img.shields.io/badge/Redis-7-red)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B)
![License](https://img.shields.io/badge/License-MIT-green)

Real-time financial anomaly detection pipeline for a Brazilian confectionery manufacturer: streams cost center transactions through Kafka, compares each against a rolling per-center mean, and surfaces deviations beyond ±20% for human review via a Streamlit dashboard.

## The Problem

A Brazilian confectionery manufacturer with 28 production machines records all financial transactions manually. The factory needed a way to detect anomalous financial transactions in real time — payments that deviate significantly from historical cost center baselines — so staff could investigate before money was lost.

The source data contained no supplier-level descriptions; the factory never recorded which supplier each payment went to. The system operates at cost center granularity, the finest level the data actually supports. Fabricating supplier mappings was rejected: it would make anomaly detection misleading rather than useful.

## Architecture

```
Producer ──► Kafka (KRaft) ──► Consumer ──► Redis ──► SQLite ──► FastAPI ──► Streamlit
```

- **Producer** — reads cost center budget data from BigQuery and publishes transaction events to the `transactions` Kafka topic
- **Kafka (KRaft)** — durable event stream; consumer group offsets guarantee each transaction is processed and committed exactly once
- **Consumer** — reads events, compares each transaction against the Redis baseline, writes anomalies to SQLite, and updates the baseline for normal transactions
- **Redis** — stores rolling per-cost-center statistics (count, sum, mean) for O(1) baseline lookups
- **SQLite** — persists flagged alerts and their review status; chosen for operational simplicity at this scale
- **FastAPI** — REST layer exposing `/alerts` and `/resolutions`; the dashboard never talks to the database directly
- **Streamlit** — review dashboard where operators classify each alert as legitimate or fraud, with resolutions fed back into the Redis baseline

## Key Design Decisions

**1. Rule-based anomaly detection, not ML**

Zero labeled anomaly history makes supervised training impossible — there is nothing to train on. A model would be a guess dressed up as science. A statistical threshold flagging transactions beyond ±20% of each cost center's rolling mean is deterministic, auditable, and deployable on day one with no historical anomaly labels required.

**2. Cost center granularity**

The source data contains no supplier descriptions; the factory never recorded which supplier each payment went to. Fabricating mappings was rejected because it would make anomaly detection misleading rather than useful. Cost centers are the finest level of specificity the data actually supports, and the system is designed around that constraint rather than papering over it.

**3. Kafka in KRaft mode**

Eliminates ZooKeeper entirely, reducing the operational surface area of the stack. KRaft mode demonstrates durable offset-based consumption and consumer group rebalancing without the coordination overhead ZooKeeper introduces — concepts that matter in production streaming environments. The added complexity over Redis Streams is deliberate: it surfaces the distributed streaming primitives that simpler alternatives abstract away.

## Tech Stack

| Technology | Role |
|---|---|
| Python 3.11 | Core language |
| Apache Kafka (KRaft) | Event streaming — no ZooKeeper dependency |
| Redis | In-memory rolling baseline storage per cost center |
| SQLite | Lightweight alert persistence |
| FastAPI | REST API — `/alerts`, `/resolutions` |
| Streamlit | Anomaly review dashboard |
| BigQuery | Historical data warehouse |
| dbt | Bronze/silver/gold transformations |

## How It Works

1. The producer queries BigQuery for cost center budget data and publishes transaction events to the `transactions` Kafka topic.
2. The consumer reads each event and looks up the cost center's rolling baseline in Redis.
3. If the baseline exists and the transaction falls within ±20% of the mean, the baseline is updated incrementally (count, sum, mean) and the message is committed.
4. If the transaction deviates beyond ±20%, it is written to SQLite as an alert with its deviation percentage, then committed.
5. If no baseline exists for a cost center yet, one is initialized from the transaction itself.
6. FastAPI exposes `/alerts` to list flagged transactions and `/resolutions` to mark an alert as reviewed; a legitimate resolution updates the Redis baseline so future transactions are compared against an expanded history.
7. The Streamlit dashboard polls `/alerts`, renders each anomaly with a visual threshold chart, and lets operators classify each transaction as legitimate or fraud.

## Running Locally

**Prerequisites**
- Docker and Docker Compose
- A GCP service account key with BigQuery read access at `./gcp-credentials.json`
- `.env` populated from `.env.example`

```bash
# 1. Configure environment
cp .env.example .env
# Fill in KAFKA_TOPIC, BIGQUERY_PROJECT, BIGQUERY_DATASET, GOOGLE_APPLICATION_CREDENTIALS

# 2. Start all services
docker compose up -d

# 3. Seed Redis with historical cost center baselines from BigQuery
#    REDIS_HOST=localhost overrides the Docker service name for local script execution
REDIS_HOST=localhost python processing/seed_redis.py

# 4. Publish a batch of transactions to Kafka
docker compose run --rm producer

# 5. Open the dashboard at http://localhost:8501
```

## Live Demo

[transaction-monitor.albuqr.com](https://transaction-monitor.albuqr.com)

## Part of a Larger Platform

This repository is the second of three interconnected systems built for the same client. The [Factory Lakehouse](https://github.com/Albuqr/Factory_Lakehouse) (Repo 1) ingests raw Excel exports from all 28 machines into BigQuery via dbt bronze/silver/gold transformations orchestrated by Airflow — the cost center tables this pipeline reads from are produced there.

---

[🇺🇸 English](#transaction-monitor) | [🇧🇷 Português](#monitor-de-transações)

# Monitor de Transações

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Kafka](https://img.shields.io/badge/Apache_Kafka-KRaft-black)
![Redis](https://img.shields.io/badge/Redis-7-red)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B)
![License](https://img.shields.io/badge/License-MIT-green)

Pipeline de detecção de anomalias financeiras em tempo real para um fabricante brasileiro de confeitos: transmite transações por centro de custo através do Kafka, compara cada uma com uma média móvel por centro, e expõe desvios acima de ±20% para revisão humana via dashboard Streamlit.

## O Problema

Um fabricante brasileiro de confeitos com 28 máquinas de produção registra todas as transações financeiras manualmente. A fábrica precisava de uma forma de detectar transações financeiras anômalas em tempo real — pagamentos que desviam significativamente das linhas de base históricas por centro de custo — para que a equipe pudesse investigar antes que o dinheiro fosse perdido.

Os dados de origem não continham descrições em nível de fornecedor; a fábrica nunca registrou qual fornecedor recebeu cada pagamento. O sistema opera na granularidade de centro de custo, o nível mais detalhado que os dados realmente suportam. Fabricar mapeamentos de fornecedores foi rejeitado: isso tornaria a detecção de anomalias enganosa em vez de útil.

## Arquitetura

```
Produtor ──► Kafka (KRaft) ──► Consumidor ──► Redis ──► SQLite ──► FastAPI ──► Streamlit
```

- **Produtor** — lê dados de orçamento por centro de custo do BigQuery e publica eventos de transação no tópico `transactions` do Kafka
- **Kafka (KRaft)** — stream de eventos durável; offsets do grupo consumidor garantem que cada transação seja processada e confirmada exatamente uma vez
- **Consumidor** — lê eventos, compara cada transação com a linha de base no Redis, grava anomalias no SQLite e atualiza a linha de base para transações normais
- **Redis** — armazena estatísticas móveis por centro de custo (contagem, soma, média) para consultas de linha de base em O(1)
- **SQLite** — persiste alertas sinalizados e seus status de revisão; escolhido pela simplicidade operacional nessa escala
- **FastAPI** — camada REST expondo `/alerts` e `/resolutions`; o dashboard nunca acessa o banco de dados diretamente
- **Streamlit** — dashboard de revisão onde operadores classificam cada alerta como legítimo ou fraude, com resoluções realimentadas na linha de base do Redis

## Decisões de Design

**1. Detecção de anomalias por regras, não por ML**

Zero histórico de anomalias rotuladas torna o treinamento supervisionado impossível — não há nada com que treinar. Um modelo seria uma suposição disfarçada de ciência. Um limiar estatístico que sinaliza transações além de ±20% da média móvel por centro de custo é determinístico, auditável e implantável desde o primeiro dia, sem necessidade de rótulos históricos de anomalias.

**2. Granularidade de centro de custo**

Os dados de origem não contêm descrições de fornecedores; a fábrica nunca registrou qual fornecedor recebeu cada pagamento. Fabricar mapeamentos foi rejeitado porque tornaria a detecção de anomalias enganosa em vez de útil. Centros de custo são o nível mais granular que os dados realmente suportam, e o sistema é projetado em torno dessa restrição em vez de encobri-la.

**3. Kafka no modo KRaft**

Elimina o ZooKeeper completamente, reduzindo a superfície operacional da stack. O modo KRaft demonstra consumo durável baseado em offsets e rebalanceamento de grupos consumidores sem a sobrecarga de coordenação que o ZooKeeper introduz — conceitos que importam em ambientes de streaming em produção. A complexidade adicional em relação ao Redis Streams é deliberada: ela expõe as primitivas de streaming distribuído que alternativas mais simples abstraem.

## Stack Tecnológica

| Tecnologia | Função |
|---|---|
| Python 3.11 | Linguagem principal |
| Apache Kafka (KRaft) | Streaming de eventos — sem dependência de ZooKeeper |
| Redis | Armazenamento em memória de linhas de base móveis por centro de custo |
| SQLite | Persistência leve de alertas |
| FastAPI | API REST — `/alerts`, `/resolutions` |
| Streamlit | Dashboard de revisão de anomalias |
| BigQuery | Data warehouse histórico |
| dbt | Transformações bronze/silver/gold |

## Como Funciona

1. O produtor consulta o BigQuery para obter dados de orçamento por centro de custo e publica eventos de transação no tópico `transactions` do Kafka.
2. O consumidor lê cada evento e busca a linha de base móvel do centro de custo no Redis.
3. Se a linha de base existir e a transação estiver dentro de ±20% da média, a linha de base é atualizada incrementalmente (contagem, soma, média) e a mensagem é confirmada.
4. Se a transação desviar além de ±20%, ela é gravada no SQLite como um alerta com seu percentual de desvio e então confirmada.
5. Se ainda não existir linha de base para um centro de custo, uma é inicializada a partir da própria transação.
6. O FastAPI expõe `/alerts` para listar transações sinalizadas e `/resolutions` para marcar um alerta como revisado; uma resolução legítima atualiza a linha de base no Redis para que transações futuras sejam comparadas com um histórico expandido.
7. O dashboard Streamlit consulta `/alerts`, renderiza cada anomalia com um gráfico de limiar visual e permite que operadores classifiquem cada transação como legítima ou fraude.

## Executando Localmente

**Pré-requisitos**
- Docker e Docker Compose
- Uma chave de conta de serviço GCP com acesso de leitura ao BigQuery em `./gcp-credentials.json`
- `.env` preenchido a partir de `.env.example`

```bash
# 1. Configurar ambiente
cp .env.example .env
# Defina KAFKA_TOPIC, BIGQUERY_PROJECT, BIGQUERY_DATASET, GOOGLE_APPLICATION_CREDENTIALS

# 2. Iniciar todos os serviços
docker compose up -d

# 3. Popular o Redis com linhas de base históricas do BigQuery
#    REDIS_HOST=localhost sobrescreve o nome do serviço Docker para execução local do script
REDIS_HOST=localhost python processing/seed_redis.py

# 4. Publicar um lote de transações no Kafka
docker compose run --rm producer

# 5. Abrir o dashboard em http://localhost:8501
```

## Demo ao Vivo

[transaction-monitor.albuqr.com](https://transaction-monitor.albuqr.com)

## Parte de uma Plataforma Maior

Este repositório é o segundo de três sistemas interconectados desenvolvidos para o mesmo cliente. O [Factory Lakehouse](https://github.com/Albuqr/Factory_Lakehouse) (Repositório 1) ingere exportações brutas em Excel de todas as 28 máquinas no BigQuery via transformações dbt bronze/silver/gold orquestradas pelo Airflow — as tabelas de centro de custo que este pipeline lê são produzidas lá.
