from __future__ import annotations

from pathlib import Path

import pandas as pd


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    if (current / "pyproject.toml").exists():
        return current
    if (current.parent / "pyproject.toml").exists():
        return current.parent
    return current


def rolling_mean(series: pd.Series, window: int = 7) -> pd.Series:
    min_periods = max(3, window // 2)
    return series.rolling(window, min_periods=min_periods).mean()


def maybe_savefig(
    fig,
    name: str,
    save_figs: bool,
    fig_dir: Path | str | None,
    dpi: int = 150,
    fmt: str = "png",
) -> None:
    if not save_figs:
        return
    if fig_dir is None:
        raise ValueError("fig_dir must be provided when save_figs=True")
    out_dir = Path(fig_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.{fmt}", dpi=dpi, bbox_inches="tight")
