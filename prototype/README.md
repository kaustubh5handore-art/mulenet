# MuleNet prototype - Phase 1 scaffold (Citi x NPCI Drunix Hackathon 2026)

Minimal, honest, runnable Phase-1 code for the MuleNet pitch:

- **Data**: PaySim loader (drop the Kaggle CSV in `data/`) with a synthetic
  fallback so everything runs before the download; accounts are split across
  3-4 simulated banks; synthetic multi-hop mule rings are injected across
  banks (public data has few real rings).
- **Baselines** (single bank, flat): XGBoost on account features.
- **Single-bank GNN**: 2-layer GraphSAGE trained on one bank's local graph.
- **Federated GNN**: the same GNN trained across all banks with FedAvg -
  only model weights travel; no customer data leaves a bank.
- **Metrics** (reported honestly, whatever they turn out to be): PR-AUC,
  recall at fixed precision, ring-level recall, false positives per 1,000
  accounts.
- **Demo**: `demo_app.py` (Streamlit) shows one test ring the way each model
  sees it - Bank A's local slice vs the federated view.

## Setup

```bash
pip install -r requirements.txt
```

## Data

By default the code runs on the built-in synthetic fallback (small, fast).
To use the real dataset, download PaySim from Kaggle
(https://www.kaggle.com/datasets/ntnu-testimon/paysim1) and place the CSV at:

```
data/PS_20174392719_1491204439457_log.csv
```

Then pass `--csv data/PS_20174392719_1491204439457_log.csv` to the scripts.
Verify the transaction count and fraud rate against the file before quoting
them anywhere (the deck marks this as [VERIFY]).

## Run

```bash
# full experiment: single-bank baselines (GraphSAGE + XGBoost) and the
# federated GNN (manual FedAvg loop), printed as a metrics table
python run_experiment.py --tiny          # quick smoke run on fallback data
python run_experiment.py                 # fuller run
python run_experiment.py --csv data/PS_20174392719_1491204439457_log.csv

# federated training with the Flower framework (real server + bank clients)
python federated_flower.py --tiny --rounds 2
python federated_flower.py --csv data/PS_20174392719_1491204439457_log.csv

# demo (trains cached models in memory, then shows a ring in two views)
streamlit run demo_app.py
```

Outputs: `metrics/results.json` and `metrics/flower_federated.json` (all
model metrics). Models stay in memory - there is deliberately no model-file
persistence in this scaffold.

## Repository QR (slide 11 of the deck)

```bash
python make_qr.py https://github.com/<user>/<repo>
```

writes `assets/qr_repo.png`; rebuilding the deck then embeds it on slide 11
automatically.

## Honest boundaries (mirrors the deck)

- Simulated data is a stand-in; nothing here is a real-world result.
- The Flower run uses the deprecated in-process server/client transport
  (chosen because it needs no ray on Windows); moving to the modern
  SuperLink/SuperNode deployment is future work.
- Cross-bank context currently comes from each bank training on rings that
  span banks; boundary-node embedding exchange is Phase 2.
