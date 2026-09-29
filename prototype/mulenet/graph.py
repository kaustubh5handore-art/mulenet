"""Per-bank graph construction for PyTorch Geometric.

Each bank's local graph contains the transactions where at least one endpoint
belongs to that bank - the "one bank's slice" from the deck. Cross-bank hops
appear only as far endpoints (boundary nodes); a bank never sees another
bank's internal edges. Node labels: 1 for injected mule accounts.

Node features (computed from the local view only, so a Bank A account's
features cannot include hops that happened in Bank C):
    0 log1p total outgoing amount
    1 log1p total incoming amount
    2 outgoing transaction count
    3 incoming transaction count
    4 counterparty count
    5 log1p mean outgoing amount
    6 share of the account's txns that are cross-bank (boundary) txns
    7 recent-velocity share (txns in the last 7 steps / total)
"""
from __future__ import annotations

import numpy as np
import torch
from torch_geometric.data import Data

N_FEATURES = 8


def _account_features(group: dict, n_steps: int) -> list[float]:
    """group: {"direction": [...], "amount": [...], ...} arrays for one
    account's local-view transactions."""
    direction = group["direction"]
    out_amt = group["amount"][direction == "out"]
    in_amt = group["amount"][direction == "in"]
    steps = group["step"]
    n = group["amount"].size
    return [
        float(np.log1p(out_amt.sum())) if out_amt.size else 0.0,
        float(np.log1p(in_amt.sum())) if in_amt.size else 0.0,
        float(out_amt.size),
        float(in_amt.size),
        float(np.unique(group["counterparty"]).size),
        float(np.log1p(out_amt.mean())) if out_amt.size else 0.0,
        float(group["is_cross_bank"].mean()) if n else 0.0,
        float(np.mean(steps >= steps.max() - 7)) if n else 0.0,
    ]


def local_graph(dataset: dict, bank: int, bank_of) -> tuple[Data, list[str]]:
    """Build one bank's local graph as a PyG ``Data`` object.

    Returns (data, accounts) with ``accounts[i]`` the account for node i.
    """
    txns = dataset["txns"]
    src = txns["src"].to_numpy()
    dst = txns["dst"].to_numpy()
    banks_src = np.array([bank_of[a] for a in src])
    banks_dst = np.array([bank_of[a] for a in dst])
    is_local = (banks_src == bank) | (banks_dst == bank)
    view = txns[is_local].reset_index(drop=True)

    bs = banks_src[is_local]
    bd = banks_dst[is_local]
    bank_account = np.where(bs == bank, view["src"], view["dst"])
    direction = np.where(bs == bank, "out", "in")
    counterparty = np.where(bs == bank, view["dst"], view["src"])
    is_cross = (bs != bd).astype(float)

    bank_account = bank_account.to_numpy() if hasattr(bank_account, "to_numpy") \
        else np.asarray(bank_account)

    # all endpoints in the local view, including cross-bank boundary nodes
    accounts = sorted(set(view["src"]) | set(view["dst"]))
    idx = {a: i for i, a in enumerate(accounts)}

    grouped: dict[str, dict[str, np.ndarray]] = {}
    rows = np.arange(len(view))
    for r in rows:
        a = bank_account[r]
        slot = grouped.setdefault(a, {"direction": [], "amount": [],
                                      "step": [], "counterparty": [],
                                      "is_cross_bank": []})
        slot["direction"].append(direction[r])
        slot["amount"].append(float(view["amount"].iloc[r]))
        slot["step"].append(int(view["step"].iloc[r]))
        slot["counterparty"].append(counterparty[r])
        slot["is_cross_bank"].append(is_cross[r])

    feats = np.zeros((len(accounts), N_FEATURES), dtype=np.float32)
    for a, slot in grouped.items():
        g = {k: np.array(v) for k, v in slot.items()}
        feats[idx[a]] = _account_features(g, n_steps=int(view["step"].max()))

    x = torch.from_numpy(feats)
    y = torch.tensor([1 if a in dataset["mules"] else 0 for a in accounts],
                     dtype=torch.long)

    rows_idx, cols_idx = [], []
    for s, d in zip(view["src"], view["dst"]):
        rows_idx.append(idx[s]); cols_idx.append(idx[d])
    edge_index = torch.tensor([rows_idx + cols_idx, cols_idx + rows_idx],
                              dtype=torch.long)

    amt = torch.tensor(view["amount"].to_numpy(), dtype=torch.float32)
    edge_attr = torch.log1p(amt).unsqueeze(1).repeat(2, 1)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    data.account = accounts          # node -> account id
    data.ring_members = dataset["mules"]
    return data, accounts
