"""Federated training with the Flower framework (the deck's promised stack).

Runs a real Flower server + 4 bank clients in-process (localhost gRPC, no
ray needed on Windows). Each bank trains on its own local graph only and
sends nothing but model parameters; the server aggregates with FedAvg.
After the rounds, the aggregated global model is evaluated on every bank's
test slice.

Usage:
    python federated_flower.py --tiny --rounds 2      # smoke run
    python federated_flower.py
"""
from __future__ import annotations

import argparse
import json
import threading
from pathlib import Path

import flwr as fl
import numpy as np
import torch
from flwr.common import ndarrays_to_parameters, parameters_to_ndarrays

from mulenet import metrics as M
from mulenet.data import build_dataset
from mulenet.experiment import evaluate, split_masks
from mulenet.graph import local_graph
from mulenet.model import SageNet, class_weights

SERVER_ADDRESS = "127.0.0.1:8080"
FINAL_PARAMS = {}   # filled by the strategy after the last aggregate_fit


class SaveFedAvg(fl.server.strategy.FedAvg):
    """FedAvg that keeps the latest aggregated parameters."""

    def aggregate_fit(self, rnd, results, failures):
        agg = super().aggregate_fit(rnd, results, failures)
        if agg is not None:
            FINAL_PARAMS["parameters"] = agg[0]
        return agg


class MuleBankClient(fl.client.NumPyClient):
    """One simulated bank: trains the global model on its own local graph."""

    def __init__(self, bank: int, data, train_mask, test_mask, epochs: int):
        self.bank = bank
        self.data = data
        self.train_mask = train_mask
        self.test_mask = test_mask
        self.epochs = epochs
        self.model = SageNet(data.num_features)
        self.weights = class_weights(data.y[train_mask])

    # ---- NumPyClient interface ----
    def get_parameters(self, config):
        return [v.detach().cpu().numpy()
                for v in self.model.state_dict().values()]

    def set_parameters(self, parameters):
        keys = list(self.model.state_dict().keys())
        state = {k: torch.tensor(p) for k, p in zip(keys, parameters)}
        self.model.load_state_dict(state)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        opt = torch.optim.Adam(self.model.parameters(), lr=0.01,
                               weight_decay=5e-4)
        self.model.train()
        for _ in range(self.epochs):
            opt.zero_grad()
            out = self.model(self.data.x, self.data.edge_index)
            loss = torch.nn.functional.cross_entropy(
                out[self.train_mask], self.data.y[self.train_mask],
                weight=self.weights)
            loss.backward()
            opt.step()
        return self.get_parameters({}), int(self.train_mask.sum()), {}

    def evaluate(self, parameters, config):
        """Real local validation loss on this bank's test slice."""
        self.set_parameters(parameters)
        self.model.eval()
        with torch.no_grad():
            out = self.model(self.data.x, self.data.edge_index)
            loss = torch.nn.functional.cross_entropy(
                out[self.test_mask], self.data.y[self.test_mask])
        return float(loss), int(self.test_mask.sum()), {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=None, help="path to the PaySim CSV")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--local-epochs", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tiny", action="store_true", help="fast smoke run")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    ds = build_dataset(csv_path=args.csv, tiny=args.tiny, seed=args.seed)
    print(f"dataset source: {ds['source_name']}  "
          f"accounts={len(ds['accounts'])} mules={len(ds['mules'])} "
          f"rings={len(ds['rings'])}")

    n_banks = ds["n_banks"]
    graphs, accounts, masks = {}, {}, {}
    for bank in range(n_banks):
        graphs[bank], accounts[bank] = local_graph(ds, bank, ds["banks"])
        masks[bank] = split_masks(graphs[bank].num_nodes, seed=args.seed)

    in_dim = next(iter(graphs.values())).num_features
    dummy = SageNet(in_dim)
    strategy = SaveFedAvg(
        initial_parameters=ndarrays_to_parameters(
            [v.detach().cpu().numpy() for v in dummy.state_dict().values()]),
        min_fit_clients=n_banks,
        min_available_clients=n_banks,
        min_evaluate_clients=0,
        evaluate_fn=None,
    )

    def launch_client(bank: int) -> None:
        client = MuleBankClient(bank, graphs[bank], masks[bank]["train"],
                                masks[bank]["test"], args.local_epochs)
        fl.client.start_client(server_address=SERVER_ADDRESS,
                               client=client.to_client())

    threads = [threading.Thread(target=launch_client, args=(b,), daemon=True)
               for b in range(n_banks)]
    for t in threads:
        t.start()

    print(f"flower federation: {n_banks} bank clients, "
          f"{args.rounds} rounds x {args.local_epochs} local epochs")
    from flwr.server import ServerConfig
    fl.server.start_server(
        server_address=SERVER_ADDRESS,
        config=ServerConfig(num_rounds=args.rounds, round_timeout=600),
        strategy=strategy,
    )
    for t in threads:
        t.join(timeout=5)

    # ---- evaluate the aggregated global model on every bank's test slice ----
    global_model = SageNet(in_dim)
    global_model.load_state_dict(
        {k: torch.tensor(p) for k, p in
         zip(dummy.state_dict().keys(),
             parameters_to_ndarrays(FINAL_PARAMS["parameters"]))})
    y_all, p_all, acc_all = [], [], []
    for bank, g in graphs.items():
        g_model = SageNet(in_dim)
        g_model.load_state_dict(global_model.state_dict())
        g_model.eval()
        with torch.no_grad():
            probs = torch.softmax(g_model(g.x, g.edge_index), dim=1)[:, 1].numpy()
        test_mask = masks[bank]["test"]
        idxs = test_mask.nonzero().flatten().tolist()
        y_all.append(g.y[test_mask].numpy())
        p_all.append(probs[test_mask.numpy()])
        acc_all += [accounts[bank][i] for i in idxs]
    y = np.concatenate(y_all)
    p = np.concatenate(p_all)
    metrics = evaluate(y, p, acc_all, ds["rings"], ds["mules"])

    print("\n--- federated GraphSAGE via Flower (test slice) ---")
    print(json.dumps(metrics, indent=2))
    out = Path("metrics")
    out.mkdir(exist_ok=True)
    (out / "flower_federated.json").write_text(
        json.dumps({"framework": "flower", "rounds": args.rounds,
                    "local_epochs": args.local_epochs,
                    "metrics": metrics}, indent=2),
        encoding="utf-8")
    print("wrote metrics/flower_federated.json")


if __name__ == "__main__":
    main()
