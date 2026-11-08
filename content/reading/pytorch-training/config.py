"""Small reproducible CPU-only experiment."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    seed: int = 42
    samples: int = 160
    features: int = 4
    hidden: int = 16
    classes: int = 2
    batch_size: int = 16
    epochs: int = 3
    learning_rate: float = 0.05
    test_fraction: float = 0.2
    device: str = "cpu"


def validate(config):
    if config.batch_size < 1 or config.epochs < 1:
        raise ValueError("Positive batch size and epochs required")
    if config.device != "cpu":
        raise ValueError("This teaching project runs on CPU")
