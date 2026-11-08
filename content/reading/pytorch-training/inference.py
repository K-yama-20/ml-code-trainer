"""Load a trusted checkpoint and predict on CPU."""

import argparse
from pathlib import Path
import torch
from model import Classifier


def load_model(path):
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    model = Classifier(
        features=checkpoint["features"],
        hidden=checkpoint["hidden"],
        classes=checkpoint["classes"],
    )
    model.load_state_dict(checkpoint["model"], strict=True)
    model.eval()
    return model


def predict(model, features):
    if features.shape[1] != model.features:
        raise ValueError("Feature count does not match the model")
    model.eval()
    with torch.inference_mode():
        logits = model(features.float().cpu())
        probabilities = logits.softmax(dim=1)
        labels = logits.argmax(dim=1)
    return labels, probabilities


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    model = load_model(args.checkpoint)
    sample = torch.zeros(2, model.features)
    labels, probabilities = predict(model, sample)
    print({"labels": labels.tolist(), "probabilities": probabilities.tolist()})


if __name__ == "__main__":
    main()
