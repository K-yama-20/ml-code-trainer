"""Pure feature transforms with explicit fit/transform separation."""

import numpy as np


def make_features(values):
    """Two raw features, their product, and their sum."""
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError("Expected shape (N, 2)")
    product = values[:, 0:1] * values[:, 1:2]
    total = values.sum(axis=1, keepdims=True)
    return np.concatenate([values, product, total], axis=1)


def fit_stats(train):
    """Statistics are computed on training data only."""
    if len(train) == 0:
        raise ValueError("Empty training set")
    mean = train.mean(axis=0, keepdims=True)
    std = train.std(axis=0, keepdims=True)
    return {"mean": mean, "std": std}


def transform(values, stats):
    """Broadcast (1,D) statistics over all rows."""
    denominator = np.maximum(stats["std"], 1e-8)
    return (values - stats["mean"]) / denominator


def summarize(values):
    """Return small diagnostics without changing the input."""
    return {
        "rows": len(values),
        "columns": values.shape[1],
        "mean": values.mean(axis=0).tolist(),
        "finite": bool(np.isfinite(values).all()),
    }
