<div align="center">

# 🕵️‍♂️ On-Chain Intel Suite

**A modular extraction and analysis engine for Solana institutional data**

Architecture and data pipeline specification for tracking smart money, identifying
novel contracts, and parsing complex DeFi transactions at scale.

![Status](https://img.shields.io/badge/Status-Spec_&_Architecture-blue?style=flat-square)
![Solana](https://img.shields.io/badge/Solana-9945FF?style=flat-square&logo=solana&logoColor=white)

</div>

---

## Why Solarized?

Most retail traders rely on laggy dashboards and aggregated metrics. By the time it's on
a dashboard, the alpha is gone. Solarized follows the money in real-time.

I needed a system that reads raw RPC data, parses custom program instructions, and spots
anomalous flows *before* they make the charts. Solarized provides the forensic tools to
trace funds through complex multi-hop transfers.

---

## System design

See [`docs/architecture.md`](docs/architecture.md) for the high-level infrastructure design.

**Core Pipeline:**
```
[Helius Geyser/RPC] → [Kafka Ingestion] → [Custom Parsers]
                                                ↓
[ClickHouse (Analytics & Fast Queries)] ← [PostgreSQL (State)]
                                                ↓
                                    [Alerting Engine / Agent API]
```

**Key Capabilities:**
- **Forensic Tracing:** Trace fund flows across multiple hops with interactive graph visualizations.
- **Smart Account Labeling:** Automated detection of CEXs, DEXs, and known protocols.
- **Token Analysis:** Real-time balance and transfer tracking for any SPL token.
- **Unified API:** REST endpoints for programmatic access to forensic data.

---

## What's in this repo

- `backend/`: FastAPI backend for data processing and API.
- `frontend/`: React/Vite frontend for the user dashboard.
- `docker-compose.yml`: For easy deployment and development.
- `docs/`: High-level system design and specifications.
- `prototype/`: Notes on tech stack selection.
- `roadmap.md`: Planned implementation phases.

---

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Kowalskk/onchain-intel-suite.git
   ```
2. **Configure Environment:**
   Copy `.env.example` to `.env` and fill in your Helius API keys and other credentials.
3. **Run with Docker:**
   ```bash
   docker-compose up
   ```

---

## Roadmap

- [x] Initial architecture design
- [x] Data pipeline specification
- [x] Wallet clustering heuristics drafted
- [ ] Implement Rust-based Geyser plugin (POC)
- [ ] ClickHouse schema deployment
- [ ] API layer construction
- [ ] Dashboard integration

---

## Built with

Designed by Saulo Torrado. Because knowing *how* data flows is the
first step to capturing it.

---

## License

MIT
