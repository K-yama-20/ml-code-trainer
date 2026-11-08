"""Synthetic features and a deterministic classification target."""

import torch
from torch.utils.data import DataLoader, TensorDataset, random_split


def make_dataset(config):
    generator = torch.Generator().manual_seed(config.seed)
    features = torch.randn(config.samples, config.features, generator=generator)
    # This fixed rule defines a target; it is not a learned model.
    score = features[:, 0] + features[:, 1] * 0.5
    labels = (score > 0).long()
    return TensorDataset(features, labels)


def make_loaders(config):
    dataset = make_dataset(config)
    test_count = round(len(dataset) * config.test_fraction)
    train_count = len(dataset) - test_count
    generator = torch.Generator().manual_seed(config.seed)
    train, test = random_split(dataset, [train_count, test_count], generator=generator)
    train_loader = DataLoader(
        train,
        batch_size=config.batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(config.seed),
        num_workers=0,
        drop_last=False,
    )
    test_loader = DataLoader(
        test,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=0,
    )
    return train_loader, test_loader
