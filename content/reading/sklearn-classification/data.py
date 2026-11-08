"""Offline Iris data; no downloads are required."""

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import numpy as np


def load_data():
    bundle = load_iris()
    features = bundle.data.astype(np.float64)
    labels = bundle.target.astype(np.int64)
    if features.shape[0] != labels.shape[0]:
        raise ValueError("Features and labels must align")
    return features, labels


def split_data(features, labels, seed=42):
    """Preserve class ratios and feature/label correspondence."""
    return train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=seed,
        stratify=labels,
    )


def describe_split(train, test):
    return {
        "train_rows": len(train),
        "test_rows": len(test),
        "features": train.shape[1],
    }
