"""Metrics reported exactly as promised on the evaluation slide."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, precision_recall_curve


def pr_auc(y_true: np.ndarray, scores: np.ndarray) -> float:
    return float(average_precision_score(y_true, scores))


def threshold_at_precision(y_true: np.ndarray, scores: np.ndarray,
                           target: float = 0.5) -> float:
    """Highest-recall threshold whose precision >= target."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    precision, recall = precision[:-1], recall[:-1]
    ok = np.where(precision >= target)[0]
    if ok.size == 0:
        return float(np.quantile(scores, 0.99))  # fallback: top 1%
    return float(thresholds[ok[np.argmax(recall[ok])]])


def recall_at_precision(y_true: np.ndarray, scores: np.ndarray,
                        target: float = 0.5) -> float:
    t = threshold_at_precision(y_true, scores, target)
    y_pred = scores >= t
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    return tp / max(tp + fn, 1)


def false_positives_per_1000(y_true: np.ndarray, scores: np.ndarray,
                             threshold: float) -> float:
    y_pred = scores >= threshold
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    n_neg = max(int((y_true == 0).sum()), 1)
    return 1000.0 * fp / n_neg


def ring_recall(rings: dict, mules: set, account_scores: dict[str, float],
                threshold: float) -> tuple[float, int]:
    """A ring counts as detected if at least one of its mule accounts
    scores above the threshold."""
    detected = total = 0
    for chain in rings.values():
        members = [a for a in chain if a in mules and a in account_scores]
        if not members:
            continue
        total += 1
        detected += int(any(account_scores[a] >= threshold for a in members))
    return detected / max(total, 1), total
