"""MuleNet models: 2-layer GraphSAGE for node classification."""
from __future__ import annotations

import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv


class SageNet(torch.nn.Module):
    """Two-layer GraphSAGE, as described on the deck's data & model slide."""

    def __init__(self, in_dim: int, hidden: int = 64, n_classes: int = 2):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.lin = torch.nn.Linear(hidden, n_classes)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.conv1(x, edge_index))
        h = F.relu(self.conv2(h, edge_index))
        return self.lin(h)


def class_weights(y: torch.Tensor) -> torch.Tensor:
    """Inverse-frequency weights for the fraud-imbalance loss."""
    n_pos = max(int((y == 1).sum()), 1)
    n_neg = max(int((y == 0).sum()), 1)
    return torch.tensor([1.0, n_neg / n_pos])


def fedavg(state_dicts: list[dict], weights: list[float]) -> dict:
    """FedAvg: weighted parameter average across banks.

    Only these state dicts travel between "banks" - no customer data, which is
    the whole point of MuleNet. (Wiring this loop into the Flower framework is
    the phase-2 step; the aggregation math here is the same.)
    """
    total = float(sum(weights))
    avg = {}
    for key in state_dicts[0]:
        acc = torch.zeros_like(state_dicts[0][key], dtype=torch.float64)
        for sd, w in zip(state_dicts, weights):
            acc += sd[key].to(torch.float64) * (w / total)
        avg[key] = acc.to(state_dicts[0][key].dtype)
    return avg
