# Airflow Docker Example

This repository contains an example setup of [Apache Airflow](https://airflow.apache.org/) running inside Docker. It also includes a sample DAG that demonstrates how you can fetch cryptocurrency prices from several exchanges and use OpenAI to generate reports.

## Repository structure

- `docker-compose.yaml` – docker configuration that starts Airflow with PostgreSQL and Redis using the **CeleryExecutor**. It is intended for local development.
- `config/airflow.cfg` – base Airflow configuration file mounted into the containers.
- `dags/example_dag.py` – sample DAG that fetches minute OHLC data for `ETH/USDT` via `ccxt`, asks OpenAI to build comparison tables and analysis, and stores generated markdown files.
- `mdfiles/` – folder where the DAG stores generated markdown reports. The repository contains example outputs.
- `logs/` – (ignored) runtime logs produced by Airflow.

## Usage

1. Ensure Docker and Docker Compose are installed.
2. Launch the stack:
   ```bash
   docker compose up -d
   ```
3. Access the Airflow UI at [http://localhost:8080](http://localhost:8080) with default credentials `airflow/airflow`.
4. Trigger the `ethPrice` DAG to generate sample markdown reports in `mdfiles/`.

## Notes

- The DAG uses an OpenAI API key; specify it in `dags/example_dag.py` before running.
- Generated logs and additional markdown files are ignored via `.gitignore`.

