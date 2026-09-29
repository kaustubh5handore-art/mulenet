"""MuleNet demo (Streamlit): how two models see the same money-laundering ring.

Run:  streamlit run demo_app.py

The demo retrains on the in-memory dataset at startup (cached) - it is a
prototype view, not a production scoring service. On the built-in fallback
data it runs in seconds; with a PaySim CSV it takes longer.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st

from mulenet.data import build_dataset
from mulenet.experiment import evaluate_federated, evaluate_single_bank

NAVY, BLUE, ORANGE, GREY = "#0B2545", "#1F5FBF", "#E8590C", "#C9D2DE"


@st.cache_resource(show_spinner="Training the models on fallback data...")
def run() -> dict:
    ds = build_dataset(tiny=True, seed=0)
    single = evaluate_single_bank(ds, bank=0, epochs=10, seed=0)
    fed = evaluate_federated(ds, rounds=2, local_epochs=2, seed=0)
    return {"ds": ds, "single": single, "fed": fed}


def ring_figure(ds, chain, single_scores, fed_scores, banks) -> "plt.Figure":
    """One figure, two panels: Bank A's local slice vs the federated view."""
    fig, (ax_local, ax_fed) = plt.subplots(1, 2, figsize=(11, 4.4), dpi=110)
    ring_nodes = chain[1:]                      # mule + cash-out accounts
    victim = chain[0]

    # ---- Bank A's local view: only what bank 0 can see ----
    local_nodes = [a for a in chain if banks.get(a, 0) == 0] or [victim]
    g_local = nx.Graph()
    for a, b in zip(chain, chain[1:]):
        if banks.get(a, 0) == 0 and banks.get(b, 0) == 0:
            g_local.add_edge(a, b)
    for a in local_nodes:
        g_local.add_node(a)
    pos = nx.spring_layout(g_local, seed=1)
    nx.draw_networkx_edges(g_local, pos, ax=ax_local, edge_color=GREY)
    for a in g_local.nodes:
        color = ORANGE if a in ds["mules"] else BLUE
        ax_local.scatter(*pos[a], s=320, c=color, zorder=3,
                         edgecolors="white", linewidths=1.5)
        score = single_scores.get(a)
        label = f"{a}\n{score:.2f}" if score is not None else a
        ax_local.annotate(label, pos[a], textcoords="offset points",
                          xytext=(0, -26), ha="center", fontsize=8,
                          color=NAVY)
    ax_local.set_title("Bank A's local view\n(its slice of the graph only)",
                       fontsize=11, color=NAVY)
    ax_local.axis("off")

    # ---- federated view: the whole chain across banks ----
    g_fed = nx.Graph()
    g_fed.add_edges_from(zip(chain, chain[1:]))
    for m in ds["mules"]:
        pass  # membership only; decoy txns are not drawn
    pos = nx.spring_layout(g_fed, seed=1)
    nx.draw_networkx_edges(g_fed, pos, ax=ax_fed, edge_color=GREY)
    for a in g_fed.nodes:
        color = ORANGE if a in ds["mules"] else BLUE
        ax_fed.scatter(*pos[a], s=320, c=color, zorder=3,
                       edgecolors="white", linewidths=1.5)
        score = fed_scores.get(a)
        label = f"{a}\n{score:.2f}" if score is not None else a
        ax_fed.annotate(label, pos[a], textcoords="offset points",
                        xytext=(0, -26), ha="center", fontsize=8,
                        color=NAVY)
    ax_fed.set_title("Federated view\n(the same chain, seen across banks)",
                     fontsize=11, color=NAVY)
    ax_fed.axis("off")
    fig.tight_layout()
    return fig


def main() -> None:
    st.set_page_config(page_title="MuleNet prototype", page_icon="🕸",
                       layout="wide")
    st.title("MuleNet prototype — single bank vs federated")
    st.caption("Prototype on simulated data (PaySim-style fallback). Scores "
               "are illustrative until trained on the full dataset. Orange = "
               "injected mule accounts.")

    state = run()
    ds, single, fed = state["ds"], state["single"], state["fed"]

    st.subheader("Metrics (test slice, simulated data)")
    rows = [
        ("Single-bank XGBoost", single["xgb"]["metrics"]),
        ("Single-bank GraphSAGE", single["gnn"]["metrics"]),
        ("Federated GraphSAGE", fed["metrics"]),
    ]
    st.table({
        "model": [r[0] for r in rows],
        "PR-AUC": [r[1]["pr_auc"] for r in rows],
        "recall @ precision 0.5": [r[1]["recall_at_precision_0.5"] for r in rows],
        "ring recall": [r[1]["ring_recall"] for r in rows],
        "false positives / 1,000": [r[1]["fp_per_1000"] for r in rows],
    })

    st.subheader("One test ring, two views")
    cross = [r for r in ds["rings"].values()
             if len({ds["banks"].get(a, 0) for a in r}) >= 2]
    if not cross:
        st.info("No cross-bank ring in the test slice."); return
    chain = cross[0]
    banks = ds["banks"]
    fig = ring_figure(ds, chain, single["gnn"]["scores"], fed["scores"],
                      banks)
    st.pyplot(fig)

    st.markdown("**Per-account scores on this ring**")
    st.table({
        "account": chain,
        "role": ["victim"] + ["mule"] * (len(chain) - 2) + ["cash-out"],
        "bank": [banks.get(a, "?") for a in chain],
        "single-bank score": [round(single["gnn"]["scores"].get(a,
                              float("nan")), 3) for a in chain],
        "federated score": [round(fed["scores"].get(a, float("nan")), 3)
                            for a in chain],
    })
    st.caption("The federated model has seen the same ring pattern from every "
               "bank's training data; Bank A's model only ever saw its slice.")


main()
