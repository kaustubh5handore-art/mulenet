"""Data layer: PaySim loader with a synthetic fallback, bank split, ring injection.

Accounts are assigned to simulated banks by hashing the account id. Synthetic
multi-hop mule rings are injected across banks because public data contains
few real rings (as the deck says: injected rings are a stand-in, not real
fraud). Every account carries an ``is_mule`` label: 1 for injected ring
accounts, 0 otherwise.
"""
from __future__ import annotations

import hashlib
import os

import numpy as np
import pandas as pd

PAYSIM_DEFAULT = os.path.join("data", "PS_20174392719_1491204439457_log.csv")


def bank_of(account: str, n_banks: int) -> int:
    """Deterministic bank assignment from the account id."""
    return int(hashlib.sha256(account.encode("utf-8")).hexdigest(), 16) % n_banks


def load_transactions(csv_path: str | None = None, max_rows: int | None = None,
                      seed: int = 0) -> tuple[pd.DataFrame, str]:
    """Return (txns, source_name).

    ``txns`` columns: step (int), amount (float), src (str), dst (str),
    paysim_is_fraud (int, PaySim's own label - kept for reference only).
    """
    rng = np.random.default_rng(seed)
    if csv_path and os.path.exists(csv_path):
        df = pd.read_csv(csv_path, nrows=max_rows)
        df = df[df["type"].isin(["TRANSFER", "CASH_OUT", "PAYMENT"])]
        txns = pd.DataFrame({
            "step": df["step"].astype(int),
            "amount": df["amount"].astype(float),
            "src": df["nameOrig"].astype(str),
            "dst": df["nameDest"].astype(str),
            "paysim_is_fraud": df["isFraud"].astype(int),
        }).reset_index(drop=True)
        return txns, f"PaySim CSV ({os.path.basename(csv_path)})"

    # ---- synthetic fallback (same schema, so every downstream step runs) ----
    n_accounts, n_txns = 3_000, 9_000
    accounts = np.array([f"ACCT{i:06d}" for i in range(n_accounts)])
    banks = np.array([bank_of(a, 4) for a in accounts])
    src_idx = rng.integers(0, n_accounts, n_txns)
    # 75% of ordinary transactions stay within a bank, 20% cross banks
    same_bank = rng.random(n_txns) < 0.75
    dst_idx = np.empty(n_txns, dtype=int)
    for i in range(n_txns):
        cand = np.where(banks == banks[src_idx[i]])[0] if same_bank[i] \
            else np.where(banks != banks[src_idx[i]])[0]
        dst_idx[i] = rng.choice(cand)
    txns = pd.DataFrame({
        "step": rng.integers(1, 31, n_txns),
        "amount": np.round(np.exp(rng.normal(8.0, 1.0, n_txns)), 2),
        "src": accounts[src_idx],
        "dst": accounts[dst_idx],
        "paysim_is_fraud": 0,
    })
    return txns, "synthetic fallback (no PaySim CSV found)"


def inject_rings(txns: pd.DataFrame, n_banks: int, n_rings: int,
                 seed: int = 0) -> tuple[pd.DataFrame, set[str], dict]:
    """Inject synthetic multi-hop mule rings that cross banks.

    Each ring: victim -> mule_1 -> ... -> mule_L -> cash-out. Banks are
    assigned by hashing the account id, so a chain's members land in
    different banks with high probability (rings are rejected if they end
    up single-bank). Every mule also gets one small decoy transaction so
    ring membership is not trivially "only ring txns".

    Returns (txns_with_rings, mule_accounts, rings) where ``rings`` maps
    ring_id -> ordered list of account ids (victim first, cash-out last).
    """
    rng = np.random.default_rng(seed + 1)
    extra, mules, rings = [], set(), {}
    rejected = 0
    for r in range(n_rings):
        n_hops = int(rng.integers(3, 6))
        chain = [f"VICTIM{r}"] + [f"MULE{r}_{h}" for h in range(n_hops)] \
            + [f"CASHOUT{r}"]
        if len({bank_of(a, n_banks) for a in chain}) < 2:
            rejected += 1
            continue
        rings[r] = chain
        mules |= set(chain[1:])
        amounts = np.exp(rng.normal(9.5, 0.3)) * \
            np.cumprod(rng.uniform(0.7, 0.95, len(chain)))
        steps = np.sort(rng.integers(1, 31, len(chain) - 1))
        for h in range(len(chain) - 1):
            extra.append({"step": int(steps[h]),
                          "amount": round(float(amounts[h]), 2),
                          "src": chain[h], "dst": chain[h + 1],
                          "paysim_is_fraud": 0})
        # one decoy transaction per mule
        for h, mule in enumerate(chain[1:-1]):
            buddy = f"BUDDY{r}_{h}"
            extra.append({"step": int(rng.integers(1, 31)),
                          "amount": round(float(np.exp(rng.normal(7.0, 0.5))), 2),
                          "src": buddy, "dst": mule, "paysim_is_fraud": 0})
    txns = pd.concat([txns, pd.DataFrame(extra)], ignore_index=True)
    return txns, mules, rings


def build_dataset(csv_path: str | None = None, n_banks: int = 4,
                  n_rings: int = 200, max_rows: int | None = None,
                  seed: int = 0, tiny: bool = False) -> dict:
    """Full Phase-1 dataset used by every script."""
    if tiny:
        n_rings, max_rows = 60, 3_000
    txns, source_name = load_transactions(csv_path, max_rows=max_rows,
                                          seed=seed)
    txns, mules, rings = inject_rings(txns, n_banks, n_rings, seed=seed)
    accounts = sorted(set(txns["src"]) | set(txns["dst"]))
    banks = {a: bank_of(a, n_banks) for a in accounts}
    return {
        "txns": txns,
        "accounts": accounts,
        "banks": banks,
        "mules": mules,
        "rings": rings,
        "n_banks": n_banks,
        "source_name": source_name,
    }
