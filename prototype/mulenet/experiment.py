"""Training + evaluation as pure in-memory functions (no model files).

Everything returns plain dicts/objects so run_experiment.py can print a
metrics table and demo_app.py can visualize with Streamlit caching.
"""
from __future__ import annotations

import numpy as np
import torch

from mulenet import metrics as M
from mulenet.graph import local_graph
from mulenet.model import SageNet, class_weights


def split_masks(n_nodes: int, seed: int = 0,
                train: float = 0.7, val: float = 0.15) -> dict:
    g = torch.Generator().manual_seed(seed)
    perm = torch.randperm(n_nodes, generator=g)
    n_tr, n_va = int(train * n_nodes), int(val * n_nodes)
    masks = {}
    for name, sl in (("train", slice(0, n_tr)),
                     ("val", slice(n_tr, n_tr + n_va)),
                     ("test", slice(n_tr + n_va, None))):
        m = torch.zeros(n_nodes, dtype=torch.bool)
        m[perm[sl]] = True
        masks[name] = m
    return masks


def train_gnn(data, train_mask, epochs: int = 30, lr: float = 0.01,
              seed: int = 0, log_every: int | None = None) -> SageNet:
    torch.manual_seed(seed)
    model = SageNet(data.num_features)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)
    weights = class_weights(data.y[train_mask])
    for epoch in range(epochs):
        model.train()
        opt.zero_grad()
        out = model(data.x, data.edge_index)
        loss = torch.nn.functional.cross_entropy(
            out[train_mask], data.y[train_mask], weight=weights)
        loss.backward()
        opt.step()
        if log_every and (epoch + 1) % max(epochs // log_every, 1) == 0:
            print(f"    epoch {epoch + 1:3d}  loss={loss.item():.4f}")
    return model


def predict(model, data) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        return torch.softmax(model(data.x, data.edge_index), dim=1)[:, 1].numpy()


def train_xgb(data, train_mask) -> object:
    from xgboost import XGBClassifier
    pos = int((data.y[train_mask] == 1).sum())
    neg = int((data.y[train_mask] == 0).sum())
    model = XGBClassifier(n_estimators=200, max_depth=5,
                          scale_pos_weight=neg / max(pos, 1),
                          eval_metric="logloss", verbosity=0)
    model.fit(data.x[train_mask].numpy(), data.y[train_mask].numpy())
    return model


def evaluate(y_true: np.ndarray, scores: np.ndarray,
             account_ids: list[str], rings: dict, mules: set) -> dict:
    thr = M.threshold_at_precision(y_true, scores, target=0.5)
    per_account = {a: float(s) for a, s in zip(account_ids, scores)}
    ring_r, n_rings = M.ring_recall(rings, mules, per_account, thr)
    return {
        "pr_auc": round(M.pr_auc(y_true, scores), 4),
        "recall_at_precision_0.5": round(
            M.recall_at_precision(y_true, scores, 0.5), 4),
        "fp_per_1000": round(M.false_positives_per_1000(y_true, scores, thr), 2),
        "ring_recall": round(ring_r, 4),
        "rings_evaluated": n_rings,
        "threshold": round(thr, 4),
    }


def evaluate_single_bank(dataset: dict, bank: int, epochs: int = 30,
                         seed: int = 0) -> dict:
    """Single-bank baselines: GNN on one bank's local graph + XGBoost flat."""
    data, accounts = local_graph(dataset, bank, dataset["banks"])
    masks = split_masks(data.num_nodes, seed=seed)
    model = train_gnn(data, masks["train"], epochs=epochs, seed=seed)
    gnn_p = predict(model, data)[masks["test"].numpy()]
    xgb = train_xgb(data, masks["train"])
    xgb_p = xgb.predict_proba(data.x[masks["test"].numpy()])[:, 1]
    test_accounts = [accounts[i] for i in masks["test"].nonzero().flatten().tolist()]
    y = data.y[masks["test"]].numpy()
    return {
        "gnn": {"metrics": evaluate(y, gnn_p, test_accounts,
                                    dataset["rings"], dataset["mules"]),
                "scores": {a: float(s) for a, s in zip(test_accounts, gnn_p)},
                "model": model},
        "xgb": {"metrics": evaluate(y, xgb_p, test_accounts,
                                    dataset["rings"], dataset["mules"]),
                "scores": {a: float(s) for a, s in zip(test_accounts, xgb_p)}},
        "y_test": y,
        "test_accounts": test_accounts,
    }


def evaluate_federated(dataset: dict, rounds: int = 5, local_epochs: int = 5,
                       seed: int = 0) -> dict:
    """Federated GNN: FedAvg over all banks' local graphs.

    Each round, every bank trains a copy of the global model on its own local
    graph only; the server averages the weight updates (weighted by node
    counts). Only state dicts travel - no customer data.
    """
    graphs, accounts = {}, {}
    for bank in range(dataset["n_banks"]):
        graphs[bank], accounts[bank] = local_graph(dataset, bank,
                                                   dataset["banks"])
    masks = {b: split_masks(graphs[b].num_nodes, seed=seed) for b in graphs}
    in_dim = next(iter(graphs.values())).num_features
    torch.manual_seed(seed)
    global_model = SageNet(in_dim)

    for rnd in range(rounds):
        state_dicts, node_counts = [], []
        for bank, g in graphs.items():
            g_model = SageNet(in_dim)
            g_model.load_state_dict(global_model.state_dict())
            g_model = train_gnn(g, masks[bank]["train"],
                                epochs=local_epochs, seed=seed + rnd)
            state_dicts.append(g_model.state_dict())
            node_counts.append(int(masks[bank]["train"].sum()))
        avg = fedavg_state_dicts(state_dicts, node_counts)
        global_model.load_state_dict(avg)
        print(f"    round {rnd + 1}/{rounds} done")

    # evaluate the global model on each bank's test slice, pooled
    y_all, p_all, acc_all = [], [], []
    for bank, g in graphs.items():
        p = predict(global_model, g)
        test_mask = masks[bank]["test"]
        idxs = test_mask.nonzero().flatten().tolist()
        y_all.append(g.y[test_mask].numpy())
        p_all.append(p[test_mask.numpy()])
        acc_all += [accounts[bank][i] for i in idxs]
    y = np.concatenate(y_all)
    p = np.concatenate(p_all)
    metrics = evaluate(y, p, acc_all, dataset["rings"], dataset["mules"])
    scores = dict(zip(acc_all, map(float, p)))
    return {"metrics": metrics, "scores": scores, "model": global_model,
            "y_test": y, "test_accounts": acc_all}


def fedavg_state_dicts(state_dicts: list[dict], weights: list[float]) -> dict:
    """FedAvg: weighted parameter average. Only state dicts travel."""
    total = float(sum(weights))
    avg = {}
    for key in state_dicts[0]:
        acc = torch.zeros_like(state_dicts[0][key], dtype=torch.float64)
        for sd, w in zip(state_dicts, weights):
            acc += sd[key].to(torch.float64) * (w / total)
        avg[key] = acc.to(state_dicts[0][key].dtype)
    return avg
