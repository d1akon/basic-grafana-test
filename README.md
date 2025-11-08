# basic-grafana-test
It’s been a while since I played around with Kafka, I don’t want to get rusty so I built this small project to simulate real-time transaction events, collect metrics with **Prometheus**, and visualize everything in **Grafana**.

<img width="1551" height="816" alt="image" src="https://github.com/user-attachments/assets/2b7bd80a-da4d-4b43-be57-ee2a1cd12d6e" />

This setup uses:
- **Kafka** + **Zookeeper** → real-time message streaming between a producer and a consumer
- **Prometheus** → to scrape custom app metrics exposed on port `8000`.
- **Grafana** → to visualize the metrics in a dashboard automatically provisioned at startup

The application (`app.py`) simulates users performing transactions — some succeed, some fail — and publishes them to a Kafka topic.  
The consumer processes the messages, simulates random latency, and updates Prometheus metrics accordingly.

When you start the stack, Grafana automatically loads:
- A **Prometheus datasource**
- A prebuilt dashboard located in `grafana/dashboards/basic_obs_dashboard.json`

---

## Metrics Exposed

| Metric name | Type | Description |
|--------------|------|-------------|
| `kafka_messages_sent` | Counter | Total number of messages successfully produced to Kafka |
| `kafka_messages_consumed` | Counter | Total number of messages consumed from Kafka |
| `successful_transactions` | Counter | Number of transactions processed successfully |
| `failed_transactions` | Counter | Number of transactions that failed |
| `transaction_latency_seconds` | Histogram | Simulated latency for processing a transaction (in **seconds**) |


## Dashboard Panels

| Panel Title | Expression | Description |
|--------------|-------------|-------------|
| **% Successful Transactions** | `successful_transactions / (successful_transactions + failed_transactions)` | Ratio of success over total |
| **% Failed Transactions** | `failed_transactions / (successful_transactions + failed_transactions)` | Ratio of failures |
| **Average Latency (Last Minute)** | `rate(transaction_latency_seconds_sum[1m]) / rate(transaction_latency_seconds_count[1m])` | Mean latency over the last minute |
| **p95 Latency [s]** | `histogram_quantile(0.95, sum(rate(transaction_latency_seconds_bucket[1m])) by (le))` | 95th percentile latency |
| **Total Transactions (5m window)** | `increase(successful_transactions_total[5m]) + increase(failed_transactions_total[5m])` | Total transactions processed in the last 5 minutes |

---

## Run the Project

```bash
#----- Build and start all containers
docker compose up --build
