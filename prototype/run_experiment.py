"""Run the Phase-1 experiment end to end and print the metrics table.

Usage:
    python run_experiment.py --tiny
    python run_experiment.py
    python run_experiment.py --csv data/PS_20174392719_1491204439457_log.csv
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mulenet.data import build_dataset
from mulenet.experiment import evaluate_federated, evaluate_single_bank


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=None, help="path to the PaySim CSV")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--local-epochs", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tiny", action="store_true",
                    help="small fallback data for a fast smoke run")
    args = ap.parse_args()

    ds = build_dataset(csv_path=args.csv, tiny=args.tiny, seed=args.seed)
    print(f"dataset source : {ds['source_name']}")
    print(f"accounts/mules : {len(ds['accounts'])} / {len(ds['mules'])}")
    print(f"injected rings : {len(ds['rings'])} (synthetic, cross-bank)")

    print("\n[1/2] single-bank baselines (Bank 0)...")
    single = evaluate_single_bank(ds, bank=0, epochs=args.epochs, seed=args.seed)

    print(f"[2/2] federated GNN ({args.rounds} rounds x "
          f"{args.local_epochs} local epochs)...")
    fed = evaluate_federated(ds, rounds=args.rounds,
                             local_epochs=args.local_epochs, seed=args.seed)

    rows = [
        ("Single-bank XGBoost", single["xgb"]["metrics"]),
        ("Single-bank GraphSAGE", single["gnn"]["metrics"]),
        ("Federated GraphSAGE (ours)", fed["metrics"]),
    ]
    print("\n=== test metrics (simulated data - not real-world results) ===")
    header = f"{'model':32s} {'PR-AUC':>7s} {'R@P.5':>7s} {'ring R':>7s} {'FP/1k':>7s}"
    print(header)
    print("-" * len(header))
    for name, m in rows:
        print(f"{name:32s} {m['pr_auc']:>7.3f} "
              f"{m['recall_at_precision_0.5']:>7.3f} "
              f"{m['ring_recall']:>7.3f} {m['fp_per_1000']:>7.2f}")

    results = {
        "source": ds["source_name"],
        "n_accounts": len(ds["accounts"]),
        "n_mules": len(ds["mules"]),
        "n_rings": len(ds["rings"]),
        "single_bank_xgb": single["xgb"]["metrics"],
        "single_bank_gnn": single["gnn"]["metrics"],
        "federated_gnn": fed["metrics"],
    }
    out = Path("metrics")
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=2),
                                      encoding="utf-8")
    print("\nwrote metrics/results.json")


if __name__ == "__main__":
    main()
