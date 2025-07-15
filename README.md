# Airflow Docker Example

This repository contains a small Docker based setup for running Apache Airflow. The project demonstrates how to use Airflow's TaskFlow API together with the `openai` and `ccxt` libraries to fetch cryptocurrency prices and automatically build reports.

## Structure

```
config/                 Airflow configuration files
  airflow.cfg           - main Airflow configuration

dags/                   DAG definitions
  example_dag.py        - example workflow that uses OpenAI and CCXT

docker-compose.yaml     Docker Compose file that starts the Airflow stack

mdfiles/                Generated markdown artifacts (tables, reports, analysis)
.gitignore              Standard ignore rules
README.md               This file
```

### DAG Overview

The `example_dag.py` workflow retrieves recent ETH/USDT candle data from several exchanges (Binance, Kucoin and OKX) and asks an OpenAI assistant to:

1. Build a comparison table of the best prices.
2. Perform a short analytical summary of the data.
3. Generate a final report using the produced table and analysis.

Results from each task are saved in the `mdfiles/` directory as separate Markdown files: `table.md`, `analysis.md` and `report.md`.

To run this DAG you must supply an OpenAI API key inside `example_dag.py` (the placeholder `API_KEY` variable should be replaced).

### Running the stack

The project uses the official Airflow Docker images (see `docker-compose.yaml`). To start a local environment:

```bash
docker compose up
```

The web UI will be available at `http://localhost:8080` using the default credentials (`airflow`/`airflow`).

Logs are stored in the `logs/` directory which is ignored by Git.

## Notes

All temporary files (`__pycache__`, `.DS_Store`, logs) are ignored via `.gitignore`.
