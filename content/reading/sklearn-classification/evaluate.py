"""Evaluation does not modify or refit the model."""

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix


def evaluate(model, features, labels):
    prediction = model.predict(features)
    probability = model.predict_proba(features)
    classes = model.classes_
    if probability.shape != (len(features), len(classes)):
        raise ValueError("Unexpected probability shape")
    if not np.allclose(probability.sum(axis=1), 1.0):
        raise ValueError("Invalid probability distribution")
    return {
        "accuracy": float(accuracy_score(labels, prediction)),
        "macro_f1": float(
            f1_score(labels, prediction, average="macro", zero_division=0)
        ),
        "confusion": confusion_matrix(labels, prediction, labels=classes).tolist(),
        "rows": len(features),
    }


def mistakes(model, features, labels):
    prediction = model.predict(features)
    indices = np.flatnonzero(prediction != labels)
    return {"indices": indices.tolist(), "count": int(len(indices))}
