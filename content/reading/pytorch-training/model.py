"""A two-layer classifier returns logits, not probabilities."""

import torch
from torch import nn


class Classifier(nn.Module):
    def __init__(self, features=4, hidden=16, classes=2):
        super().__init__()
        self.features = features
        self.layers = nn.Sequential(
            nn.Linear(features, hidden),
            nn.ReLU(),
            nn.Dropout(p=0.1),
            nn.Linear(hidden, classes),
        )

    def forward(self, x):
        if x.ndim != 2 or x.shape[1] != self.features:
            raise ValueError("Expected a batch of feature vectors")
        return self.layers(x)


def build_model(config):
    torch.manual_seed(config.seed)
    model = Classifier(
        features=config.features,
        hidden=config.hidden,
        classes=config.classes,
    )
    return model.to(config.device)


def parameter_count(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
