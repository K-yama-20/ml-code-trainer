"""The scaler belongs inside the fitted pipeline."""

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


def build_pipeline(seed=42):
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    max_iter=300,
                    random_state=seed,
                    C=1.0,
                ),
            ),
        ]
    )


def train_model(features, labels, seed=42):
    pipeline = build_pipeline(seed)
    pipeline.fit(features, labels)
    return pipeline


def feature_statistics(pipeline):
    scaler = pipeline.named_steps["scale"]
    return {
        "mean": scaler.mean_.tolist(),
        "variance": scaler.var_.tolist(),
        "seen": int(scaler.n_samples_seen_),
    }
