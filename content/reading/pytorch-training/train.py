"""Training, evaluation, and state_dict checkpointing."""

import argparse
from pathlib import Path
import torch
from torch import nn
from config import Config, validate
from dataset import make_loaders
from model import build_model, parameter_count


def train_epoch(model, loader, optimizer, loss_fn, device):
    model.train()
    total_loss = 0.0
    total_rows = 0
    for features, labels in loader:
        features = features.to(device)
        labels = labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(features)
        loss = loss_fn(logits, labels)
        loss.backward()
        optimizer.step()
        rows = features.shape[0]
        total_loss += loss.item() * rows
        total_rows += rows
    return total_loss / max(total_rows, 1)


def evaluate(model, loader, device):
    model.eval()
    correct = 0
    count = 0
    with torch.inference_mode():
        for features, labels in loader:
            logits = model(features.to(device))
            predictions = logits.argmax(dim=1).cpu()
            correct += int((predictions == labels).sum())
            count += len(labels)
    return correct / max(count, 1)


def save_checkpoint(model, config, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": model.state_dict(),
            "features": config.features,
            "hidden": config.hidden,
            "classes": config.classes,
        },
        path,
    )


def run(output, config=None):
    config = config or Config()
    validate(config)
    torch.set_num_threads(1)
    train_loader, test_loader = make_loaders(config)
    model = build_model(config)
    optimizer = torch.optim.SGD(model.parameters(), lr=config.learning_rate)
    loss_fn = nn.CrossEntropyLoss()
    report = []
    for epoch in range(config.epochs):
        loss = train_epoch(model, train_loader, optimizer, loss_fn, config.device)
        accuracy = evaluate(model, test_loader, config.device)
        report.append({"epoch": epoch + 1, "loss": loss, "accuracy": accuracy})
    save_checkpoint(model, config, output / "model.pt")
    return {"parameters": parameter_count(model), "epochs": report}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    print(run(args.output))


if __name__ == "__main__":
    main()
