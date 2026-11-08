"""Run the complete offline classification experiment."""

import argparse
import json
from pathlib import Path
import joblib
from data import load_data, split_data, describe_split
from model import train_model, feature_statistics
from evaluate import evaluate, mistakes


def run(output, seed=42):
    features, labels = load_data()
    train_x, test_x, train_y, test_y = split_data(features, labels, seed)
    model = train_model(train_x, train_y, seed)
    report = {
        "split": describe_split(train_x, test_x),
        "statistics": feature_statistics(model),
        "evaluation": evaluate(model, test_x, test_y),
        "mistakes": mistakes(model, test_x, test_y),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    joblib.dump(model, output / "model.joblib")
    # Only load joblib files from a trusted source.
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.seed), indent=2))


if __name__ == "__main__":
    main()
