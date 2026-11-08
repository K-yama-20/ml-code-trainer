"""Run with: python pipeline.py --output ./output"""

import argparse
from pathlib import Path
from data_io import load_csv, save_array, make_sample
from features import make_features, fit_stats, transform, summarize


def run(source, output, split=16):
    raw = load_csv(source)
    if not 0 < split < len(raw):
        raise ValueError("Split must leave train and test rows")
    features = make_features(raw)
    train, test = features[:split], features[split:]
    stats = fit_stats(train)
    train_scaled = transform(train, stats)
    test_scaled = transform(test, stats)
    save_array(output / "train.npy", train_scaled)
    save_array(output / "test.npy", test_scaled)
    save_array(output / "mean.npy", stats["mean"])
    save_array(output / "std.npy", stats["std"])
    return summarize(train_scaled), summarize(test_scaled)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.output / "input.csv"
    make_sample(source)
    print(run(source, args.output))


if __name__ == "__main__":
    main()
