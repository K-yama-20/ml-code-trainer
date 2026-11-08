"""CSV input and NumPy output; paths are passed explicitly."""

from pathlib import Path
import numpy as np


def load_csv(path):
    """Read two numeric columns with a header."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    values = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    if values.shape[1] != 2:
        raise ValueError("Expected two feature columns")
    if not np.isfinite(values).all():
        raise ValueError("Input must contain finite values")
    return values


def save_array(path, values):
    """Create parent directories and save without pickle."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, values, allow_pickle=False)
    return path


def make_sample(path, seed=42):
    rng = np.random.default_rng(seed)
    values = rng.normal(size=(20, 2))
    np.savetxt(path, values, delimiter=",", header="a,b", comments="")
    return values
