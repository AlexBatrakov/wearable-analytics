from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from itertools import product
import math
from pathlib import Path
from typing import Any
import warnings

from joblib import Parallel, delayed, effective_n_jobs
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import BaseEstimator, RegressorMixin, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.cross_decomposition import PLSRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_selection import mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, HuberRegressor, Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .stage4 import (
    STAGE4_PRIMARY_TARGET,
    STAGE4_SLEEP_START_CONTEXT_FEATURE,
    STAGE4_SPLIT_COLUMN,
)


STAGE4_LINEAR_TUNING_METRICS: tuple[str, ...] = ("mae", "rmse", "r2", "pearson", "spearman")
STAGE4_LINEAR_MODEL_KINDS: tuple[str, ...] = (
    "linear",
    "ridge",
    "lasso",
    "elastic_net",
    "huber",
    "pls",
)
STAGE4_LINEAR_FEATURE_SELECTION_MODES: tuple[str, ...] = (
    "none",
    "top_spearman",
    "top_mutual_info",
    "correlation_prune",
    "spearman_then_correlation",
    "lasso_nonzero",
)
STAGE4_LINEAR_DUMMY_STRATEGIES: tuple[str, ...] = ("dummy_mean", "dummy_median", "dummy_last")
STAGE4_LINEAR_HOLDOUT_STRATEGIES: tuple[str, ...] = ("random", "mixed")


@dataclass(frozen=True)
class Stage4FeatureSelectionConfig:
    """Feature-selection candidate for Stage 4 linear-family tuning."""

    mode: str = "none"
    top_k: int = 40
    min_features: int = 8
    min_abs_spearman: float = 0.0
    min_mutual_info: float = 0.0
    correlation_threshold: float = 0.95
    lasso_alpha: float = 0.03
    lasso_max_iter: int = 50_000


@dataclass(frozen=True)
class Stage4LinearCandidate:
    """One linear-family candidate evaluated during repeated holdout tuning."""

    candidate_id: int
    model_kind: str
    feature_selection: Stage4FeatureSelectionConfig
    robust_clip: str = "none"
    calibration: str = "none"
    target_transform: str = "none"
    prediction_clip: str = "0_100"
    alpha: float | None = None
    l1_ratio: float | None = None
    epsilon: float | None = None
    n_components: int | None = None
    fit_intercept: bool = True
    max_iter: int = 50_000
    tol: float = 1e-4


@dataclass(frozen=True)
class Stage4LinearConfig:
    """Configuration for the Stage 4 sleep-stress linear modeling pass."""

    target_col: str = STAGE4_PRIMARY_TARGET
    feature_set: str = "monitoring_full_wake_pre_sleep"
    grid_source: str = "preset"
    grid_preset: str = "standard"
    split_col: str = STAGE4_SPLIT_COLUMN
    include_schedule_context: bool = True
    repeated_holdout_repeats: int = 5
    repeated_holdout_seed: int = 42
    repeated_holdout_seed_step: int = 1009
    validation_fraction_within_pretest: float | None = None
    holdout_strategy: str = "random"
    temporal_holdout_repeats: int = 3
    temporal_validation_rows: int = 45
    baseline_strategy: str = "dummy_median"
    shortlist_count: int = 150
    shortlist_global_top_n: int = 50
    shortlist_temporal_mean_top_n: int = 10
    shortlist_temporal_worst_top_n: int = 10
    shortlist_random_stability_top_n: int = 5
    shortlist_model_family_top_n: int = 5
    shortlist_selector_top_n: int = 1
    shortlist_target_transform_top_n: int = 5
    shortlist_calibration_top_n: int = 3
    shortlist_min_baseline_wins: int = 2
    shortlist_temporal_worst_relative_mae_max: float = 1.25
    combined_temporal_mean_weight: float = 0.65
    combined_temporal_worst_weight: float = 0.20
    combined_random_mean_weight: float = 0.10
    combined_random_stability_weight: float = 0.05
    tuning_metric: str = "mae"
    calibration_cv_folds: int = 3
    calibration_min_rows: int = 50
    missing_indicators: bool = False
    keep_categorical_features: bool = True
    mutual_info_neighbors: int = 5
    random_state: int = 42
    finalist_count: int = 5
    n_jobs: int = 1
    parallel_backend: str = "loky"
    parallel_batch_size: str | int = "auto"
    default_prediction_clip: str = "0_100"
    default_target_transform: str = "none"


@dataclass(frozen=True)
class Stage4LinearGridSpec:
    """Declarative candidate-grid settings for Stage 4 linear experiments."""

    preset: str = "standard"
    model_kinds: tuple[str, ...] = STAGE4_LINEAR_MODEL_KINDS
    feature_selection_modes: tuple[str, ...] = STAGE4_LINEAR_FEATURE_SELECTION_MODES
    top_k_values: tuple[int, ...] = (40,)
    min_features: int = 8
    min_abs_spearman_values: tuple[float, ...] = (0.0,)
    min_mutual_info_values: tuple[float, ...] = (0.0,)
    correlation_thresholds: tuple[float, ...] = (0.90, 0.95)
    lasso_selector_alphas: tuple[float, ...] = (0.03,)
    lasso_selector_max_iter: int = 50_000
    robust_clips: tuple[str, ...] = ("none", "z=4", "z=5")
    calibrations: tuple[str, ...] = ("none", "linear")
    target_transforms: tuple[str, ...] = ("none",)
    prediction_clips: tuple[str, ...] = ("0_100",)
    ridge_alphas: tuple[float, ...] = (1.0, 10.0, 100.0)
    lasso_alphas: tuple[float, ...] = (0.01, 0.03)
    elastic_net_alphas: tuple[float, ...] = (0.003, 0.01)
    elastic_net_l1_ratios: tuple[float, ...] = (0.20, 0.50)
    huber_alphas: tuple[float, ...] = (0.0001, 0.001)
    huber_epsilons: tuple[float, ...] = (1.35, 1.75)
    pls_components: tuple[int, ...] = (3, 8)
    fit_intercept: bool = True
    max_iter: int = 50_000
    tol: float = 1e-4


@dataclass
class FittedStage4LinearModel:
    """A fitted model plus feature-selection and calibration metadata."""

    pipeline: Pipeline
    selected_features: list[str]
    candidate: Stage4LinearCandidate
    calibration_record: dict[str, object]
    feature_selection_detail: pd.DataFrame


@dataclass
class Stage4LinearRunResult:
    """Artifacts returned by `run_stage4_linear_modeling`."""

    config: Stage4LinearConfig
    feature_columns: list[str]
    candidate_grid: pd.DataFrame
    tuning_repeats: pd.DataFrame
    tuning_summary: pd.DataFrame
    dummy_tuning_summary: pd.DataFrame
    shortlist_summary: pd.DataFrame
    model_selection_summary: pd.DataFrame
    final_metrics: pd.DataFrame
    dummy_metrics: pd.DataFrame
    leaderboard: pd.DataFrame
    leaderboard_slices: dict[str, pd.DataFrame]
    final_predictions: pd.DataFrame
    feature_selection_detail: pd.DataFrame


@dataclass
class Stage4LinearTuningResult:
    """Validation-only artifacts produced before finalist refit."""

    config: Stage4LinearConfig
    feature_columns: list[str]
    candidates: list[Stage4LinearCandidate]
    splits: dict[str, pd.DataFrame]
    candidate_grid: pd.DataFrame
    experiment_plan: dict[str, object]
    tuning_repeats: pd.DataFrame
    tuning_summary: pd.DataFrame
    dummy_tuning_summary: pd.DataFrame
    shortlist_summary: pd.DataFrame
    validation_slices: dict[str, pd.DataFrame]


class RobustZClipper(BaseEstimator, TransformerMixin):
    """Clip numeric columns to train-fitted mean +/- z standard deviations."""

    def __init__(self, z: float | None = None) -> None:
        self.z = z

    def fit(self, X: Any, y: Any = None) -> "RobustZClipper":
        array = self._to_array(X)
        self.center_ = np.nanmean(array, axis=0)
        scale = np.nanstd(array, axis=0)
        scale = np.where(np.isfinite(scale) & (scale > 0), scale, np.nan)
        if self.z is None:
            self.lower_ = np.full(array.shape[1], -np.inf, dtype=float)
            self.upper_ = np.full(array.shape[1], np.inf, dtype=float)
        else:
            self.lower_ = self.center_ - float(self.z) * scale
            self.upper_ = self.center_ + float(self.z) * scale
            self.lower_ = np.where(np.isfinite(self.lower_), self.lower_, -np.inf)
            self.upper_ = np.where(np.isfinite(self.upper_), self.upper_, np.inf)
        return self

    def transform(self, X: Any) -> np.ndarray:
        array = self._to_array(X)
        return np.clip(array, self.lower_, self.upper_)

    def get_feature_names_out(self, input_features: Any = None) -> np.ndarray:
        if input_features is None:
            count = len(getattr(self, "center_", []))
            return np.asarray([f"x{idx}" for idx in range(count)], dtype=object)
        return np.asarray(input_features, dtype=object)

    @staticmethod
    def _to_array(X: Any) -> np.ndarray:
        if isinstance(X, (pd.DataFrame, pd.Series)):
            return X.to_numpy(dtype=float)
        return np.asarray(X, dtype=float)


class SafePLSRegressor(BaseEstimator, RegressorMixin):
    """PLS regressor that clips requested components to the fitted design size."""

    def __init__(self, n_components: int = 5) -> None:
        self.n_components = n_components

    def fit(self, X: Any, y: Any) -> "SafePLSRegressor":
        array = np.asarray(X, dtype=float)
        y_array = np.asarray(y, dtype=float)
        max_components = max(1, min(array.shape[0] - 1, array.shape[1]))
        self.n_components_ = int(min(max(1, int(self.n_components)), max_components))
        self.model_ = PLSRegression(n_components=self.n_components_, scale=False)
        self.model_.fit(array, y_array)
        return self

    def predict(self, X: Any) -> np.ndarray:
        return np.ravel(self.model_.predict(np.asarray(X, dtype=float)))


def resolve_stage4_feature_columns(
    feature_catalog: pd.DataFrame,
    *,
    feature_set: str,
    include_schedule_context: bool = True,
) -> list[str]:
    """Resolve feature columns from the Stage 4 feature-set catalog."""
    required = {"feature_set", "feature"}
    missing = sorted(required - set(feature_catalog.columns))
    if missing:
        raise KeyError(f"feature_catalog missing required columns: {missing}")
    available_sets = set(feature_catalog["feature_set"].astype(str))
    if feature_set not in available_sets:
        raise KeyError(f"Unknown Stage 4 feature_set={feature_set!r}. Available: {sorted(available_sets)}")
    columns = (
        feature_catalog.loc[feature_catalog["feature_set"].astype(str).eq(feature_set), "feature"]
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    if not include_schedule_context:
        columns = [column for column in columns if column != STAGE4_SLEEP_START_CONTEXT_FEATURE]
    return columns


def prepare_stage4_linear_model_frame(
    frame: pd.DataFrame,
    feature_columns: Sequence[str],
    *,
    target_col: str = STAGE4_PRIMARY_TARGET,
    split_col: str = STAGE4_SPLIT_COLUMN,
) -> pd.DataFrame:
    """Keep train/valid/test rows with target and usable candidate columns."""
    required = {"analysis_window_id", "calendarDate", target_col, split_col}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(f"frame missing required columns: {missing}")
    existing_features = [column for column in feature_columns if column in frame.columns]
    if not existing_features:
        raise ValueError("No requested feature columns are present in the frame")

    keep = ["analysis_window_id", "calendarDate", split_col, target_col, *existing_features]
    out = frame.loc[frame[split_col].isin(["train", "valid", "test"]), keep].copy()
    out["calendarDate"] = pd.to_datetime(out["calendarDate"], errors="coerce")
    out[target_col] = pd.to_numeric(out[target_col], errors="coerce")
    out = out.dropna(subset=["calendarDate", target_col])
    out = out.sort_values(["calendarDate", "analysis_window_id"]).reset_index(drop=True)
    return out


def split_stage4_model_frame(
    model_frame: pd.DataFrame,
    *,
    split_col: str = STAGE4_SPLIT_COLUMN,
) -> dict[str, pd.DataFrame]:
    """Return train/valid/test frames using the existing Stage 4 split labels."""
    splits = {
        split: model_frame.loc[model_frame[split_col].eq(split)].copy().reset_index(drop=True)
        for split in ["train", "valid", "test"]
    }
    missing = [split for split, split_df in splits.items() if split_df.empty]
    if missing:
        raise ValueError(f"Stage 4 linear modeling requires non-empty splits: {missing}")
    return splits


def make_repeated_pretest_holdouts(
    splits: Mapping[str, pd.DataFrame],
    *,
    repeats: int,
    seed: int,
    seed_step: int = 1009,
    validation_fraction: float | None = None,
) -> list[dict[str, object]]:
    """Create random train/validation holdouts inside train+valid history only."""
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    pretest = (
        pd.concat([splits["train"], splits["valid"]], ignore_index=True)
        .sort_values(["calendarDate", "analysis_window_id"])
        .reset_index(drop=True)
    )
    valid_n = len(splits["valid"]) if validation_fraction is None else int(round(len(pretest) * validation_fraction))
    valid_n = min(max(1, valid_n), len(pretest) - 1)
    holdouts: list[dict[str, object]] = []
    for repeat_idx in range(repeats):
        random_state = int(seed + repeat_idx * seed_step)
        rng = np.random.default_rng(random_state)
        valid_positions = np.sort(rng.choice(len(pretest), size=valid_n, replace=False))
        valid_mask = np.zeros(len(pretest), dtype=bool)
        valid_mask[valid_positions] = True
        holdouts.append(
            {
                "holdout_type": "random",
                "repeat": repeat_idx,
                "random_state": random_state,
                "train": pretest.loc[~valid_mask].copy().reset_index(drop=True),
                "valid": pretest.loc[valid_mask].copy().reset_index(drop=True),
            }
        )
    return holdouts


def make_expanding_temporal_pretest_holdouts(
    splits: Mapping[str, pd.DataFrame],
    *,
    repeats: int,
    validation_rows: int,
) -> list[dict[str, object]]:
    """Create expanding-window temporal validation holdouts inside pre-test history."""
    if repeats < 1:
        raise ValueError("repeats must be at least 1")
    if validation_rows < 1:
        raise ValueError("validation_rows must be at least 1")
    pretest = (
        pd.concat([splits["train"], splits["valid"]], ignore_index=True)
        .sort_values(["calendarDate", "analysis_window_id"])
        .reset_index(drop=True)
    )
    max_validation_rows = max(1, (len(pretest) - 1) // repeats)
    valid_n = min(int(validation_rows), max_validation_rows)
    first_valid_start = len(pretest) - valid_n * repeats
    if first_valid_start < 1:
        raise ValueError(
            "Not enough pre-test rows to create temporal holdouts with a non-empty training window"
        )

    holdouts: list[dict[str, object]] = []
    for repeat_idx in range(repeats):
        valid_start = first_valid_start + repeat_idx * valid_n
        valid_end = valid_start + valid_n
        holdouts.append(
            {
                "holdout_type": "temporal",
                "repeat": repeat_idx,
                "random_state": -1,
                "train": pretest.iloc[:valid_start].copy().reset_index(drop=True),
                "valid": pretest.iloc[valid_start:valid_end].copy().reset_index(drop=True),
            }
        )
    return holdouts


def make_stage4_linear_tuning_holdouts(
    splits: Mapping[str, pd.DataFrame],
    *,
    config: Stage4LinearConfig | None = None,
) -> list[dict[str, object]]:
    """Create the configured validation holdouts inside pre-test history."""
    config = config or Stage4LinearConfig()
    strategy = config.holdout_strategy.lower().strip()
    if strategy not in STAGE4_LINEAR_HOLDOUT_STRATEGIES:
        raise ValueError(
            f"holdout_strategy must be one of: {', '.join(STAGE4_LINEAR_HOLDOUT_STRATEGIES)}"
        )
    random_holdouts = make_repeated_pretest_holdouts(
        splits,
        repeats=config.repeated_holdout_repeats,
        seed=config.repeated_holdout_seed,
        seed_step=config.repeated_holdout_seed_step,
        validation_fraction=config.validation_fraction_within_pretest,
    )
    if strategy == "random":
        return random_holdouts
    temporal_holdouts = make_expanding_temporal_pretest_holdouts(
        splits,
        repeats=config.temporal_holdout_repeats,
        validation_rows=config.temporal_validation_rows,
    )
    return [*random_holdouts, *temporal_holdouts]


def stage4_linear_grid_spec_from_preset(
    preset: str = "smoke",
    **overrides: object,
) -> Stage4LinearGridSpec:
    """Create an editable grid spec from a named runtime preset."""
    preset_key = preset.lower().strip()
    if preset_key == "smoke":
        spec = Stage4LinearGridSpec(
            preset="smoke",
            top_k_values=(40,),
            correlation_thresholds=(0.90,),
            lasso_selector_alphas=(0.03,),
            robust_clips=("none", "z=5"),
            calibrations=("none",),
            ridge_alphas=(10.0,),
            lasso_alphas=(0.03,),
            elastic_net_alphas=(0.01,),
            elastic_net_l1_ratios=(0.50,),
            huber_alphas=(0.001,),
            huber_epsilons=(1.35,),
            pls_components=(5,),
        )
    elif preset_key == "standard":
        spec = Stage4LinearGridSpec(
            preset="standard",
            top_k_values=(25, 40),
            correlation_thresholds=(0.90, 0.95),
            lasso_selector_alphas=(0.01, 0.03),
            robust_clips=("none", "z=5"),
            calibrations=("none",),
            ridge_alphas=(1.0, 10.0, 100.0),
            lasso_alphas=(0.01, 0.03),
            elastic_net_alphas=(0.003, 0.01),
            elastic_net_l1_ratios=(0.20, 0.50),
            huber_alphas=(0.0001, 0.001),
            huber_epsilons=(1.35, 1.75),
            pls_components=(3, 8),
        )
    elif preset_key == "heavy":
        spec = Stage4LinearGridSpec(
            preset="heavy",
            top_k_values=(20, 40, 60),
            correlation_thresholds=(0.85, 0.90, 0.95),
            lasso_selector_alphas=(0.003, 0.01, 0.03, 0.10),
            robust_clips=("none", "z=4", "z=5"),
            calibrations=("none", "linear"),
            target_transforms=("none",),
            prediction_clips=("0_100", "none"),
            ridge_alphas=(0.1, 1.0, 10.0, 100.0, 300.0),
            lasso_alphas=(0.003, 0.01, 0.03, 0.10),
            elastic_net_alphas=(0.003, 0.01, 0.03, 0.10),
            elastic_net_l1_ratios=(0.10, 0.50, 0.90),
            huber_alphas=(0.00001, 0.0001, 0.001, 0.01),
            huber_epsilons=(1.20, 1.35, 1.75),
            pls_components=(2, 3, 5, 8, 12),
        )
    else:
        raise ValueError("preset must be one of: smoke, standard, heavy")
    if overrides:
        spec = replace(spec, **_coerce_grid_spec_overrides(overrides))
    return replace(spec, preset=preset_key)


def build_stage4_linear_candidate_grid(
    config: Stage4LinearConfig | None = None,
    grid_spec: Stage4LinearGridSpec | None = None,
) -> list[Stage4LinearCandidate]:
    """Build a Cartesian candidate grid from a declarative grid spec."""
    config = config or Stage4LinearConfig()
    grid_spec = grid_spec or stage4_linear_grid_spec_from_preset(config.grid_preset)
    _validate_grid_spec(grid_spec)
    feature_configs = _feature_selection_configs_from_grid_spec(grid_spec)
    model_configs = _model_configs_from_grid_spec(grid_spec)
    candidates: list[Stage4LinearCandidate] = []
    for feature_config in feature_configs:
        for model_config in model_configs:
            for robust_clip, calibration, target_transform, prediction_clip in product(
                grid_spec.robust_clips,
                grid_spec.calibrations,
                grid_spec.target_transforms,
                grid_spec.prediction_clips,
            ):
                candidates.append(
                    Stage4LinearCandidate(
                        candidate_id=len(candidates),
                        feature_selection=feature_config,
                        robust_clip=robust_clip,
                        calibration=calibration,
                        target_transform=target_transform or config.default_target_transform,
                        prediction_clip=prediction_clip or config.default_prediction_clip,
                        fit_intercept=grid_spec.fit_intercept,
                        max_iter=grid_spec.max_iter,
                        tol=grid_spec.tol,
                        **model_config,
                    )
                )
    return candidates


def stage4_linear_candidate_grid(config: Stage4LinearConfig | None = None) -> list[Stage4LinearCandidate]:
    """Build the default tuning grid for linear-family Stage 4 models."""
    config = config or Stage4LinearConfig()
    grid_spec = stage4_linear_grid_spec_from_preset(config.grid_preset)
    return build_stage4_linear_candidate_grid(config, grid_spec)


def candidate_grid_frame(candidates: Sequence[Stage4LinearCandidate]) -> pd.DataFrame:
    rows = []
    for candidate in candidates:
        rows.append(_candidate_record(candidate))
    return pd.DataFrame(rows)


def build_stage4_linear_experiment_plan(
    config: Stage4LinearConfig,
    candidates: Sequence[Stage4LinearCandidate],
    *,
    feature_columns: Sequence[str] | None = None,
) -> dict[str, object]:
    """Summarize candidate-grid dimensions and approximate model-fit cost."""
    grid = candidate_grid_frame(candidates)
    if grid.empty:
        raise ValueError("Cannot build an experiment plan for an empty candidate grid")

    selector_cols = [
        "feature_selection_mode",
        "feature_selection_top_k",
        "feature_selection_min_features",
        "feature_selection_min_abs_spearman",
        "feature_selection_min_mutual_info",
        "feature_selection_correlation_threshold",
        "feature_selection_lasso_alpha",
    ]
    model_cols = [
        "model_kind",
        "alpha",
        "l1_ratio",
        "epsilon",
        "n_components",
        "fit_intercept",
        "max_iter",
        "tol",
    ]
    selector_configs = grid[selector_cols].drop_duplicates()
    selector_count_lookup = (
        selector_configs.groupby("feature_selection_mode", dropna=False).size().astype(int).to_dict()
    )
    selector_counts = {
        mode: int(selector_count_lookup[mode])
        for mode in STAGE4_LINEAR_FEATURE_SELECTION_MODES
        if mode in selector_count_lookup
    }
    model_configs = grid[model_cols].drop_duplicates()
    model_count_lookup = model_configs.groupby("model_kind", dropna=False).size().astype(int).to_dict()
    model_counts = {
        model_kind: int(model_count_lookup[model_kind])
        for model_kind in STAGE4_LINEAR_MODEL_KINDS
        if model_kind in model_count_lookup
    }
    robust_clips = grid["robust_clip"].dropna().astype(str).drop_duplicates().tolist()
    target_transforms = grid["target_transform"].dropna().astype(str).drop_duplicates().tolist()
    prediction_clips = grid["prediction_clip"].dropna().astype(str).drop_duplicates().tolist()
    calibrations = grid["calibration"].dropna().astype(str).drop_duplicates().tolist()
    preprocessing_multiplier = len(robust_clips) * len(target_transforms) * len(prediction_clips)
    factorized_candidate_count = (
        preprocessing_multiplier
        * len(selector_configs)
        * len(model_configs)
        * len(calibrations)
    )
    temporal_repeats = config.temporal_holdout_repeats if config.holdout_strategy == "mixed" else 0
    tuning_holdout_count = config.repeated_holdout_repeats + temporal_repeats
    repeated_evaluations = len(grid) * tuning_holdout_count
    linear_calibration_candidates = int(grid["calibration"].eq("linear").sum())
    calibration_inner_fits = (
        linear_calibration_candidates
        * tuning_holdout_count
        * config.calibration_cv_folds
    )
    lasso_selector_candidates = int(grid["feature_selection_mode"].eq("lasso_nonzero").sum())
    selector_main_fits = lasso_selector_candidates * tuning_holdout_count
    selector_calibration_inner_fits = int(
        (
            grid["feature_selection_mode"].eq("lasso_nonzero")
            & grid["calibration"].eq("linear")
        ).sum()
        * tuning_holdout_count
        * config.calibration_cv_folds
    )
    approximate_base_fits = repeated_evaluations + calibration_inner_fits
    approximate_tuning_fits = (
        approximate_base_fits
        + selector_main_fits
        + selector_calibration_inner_fits
    )
    resolved_n_jobs = int(effective_n_jobs(config.n_jobs))
    approximate_parallel_waves = (
        tuning_holdout_count
        * math.ceil(len(grid) / max(1, resolved_n_jobs))
    )
    effective_finalists = min(config.finalist_count, len(grid))
    if calibrations == ["none"]:
        finalist_base_fits_min = effective_finalists
        finalist_base_fits_max = effective_finalists
    elif calibrations == ["linear"]:
        finalist_base_fits_min = effective_finalists * (1 + config.calibration_cv_folds)
        finalist_base_fits_max = finalist_base_fits_min
    else:
        finalist_base_fits_min = effective_finalists
        finalist_base_fits_max = effective_finalists * (1 + config.calibration_cv_folds)

    return {
        "target_col": config.target_col,
        "feature_set": config.feature_set,
        "include_schedule_context": config.include_schedule_context,
        "candidate_feature_count": len(feature_columns) if feature_columns is not None else None,
        "grid_source": config.grid_source,
        "grid_preset": config.grid_preset if config.grid_source == "preset" else "not used",
        "tuning_metric": config.tuning_metric,
        "holdout_strategy": config.holdout_strategy,
        "repeated_holdout_repeats": config.repeated_holdout_repeats,
        "temporal_holdout_repeats": temporal_repeats,
        "tuning_holdout_count": tuning_holdout_count,
        "temporal_validation_rows": config.temporal_validation_rows,
        "baseline_strategy": config.baseline_strategy,
        "shortlist_count": config.shortlist_count,
        "repeated_holdout_seed": config.repeated_holdout_seed,
        "robust_clips": robust_clips,
        "target_transforms": target_transforms,
        "prediction_clips": prediction_clips,
        "calibrations": calibrations,
        "calibration_cv_folds": config.calibration_cv_folds,
        "feature_selector_counts": selector_counts,
        "feature_selector_config_count": len(selector_configs),
        "model_config_counts": model_counts,
        "model_config_count": len(model_configs),
        "preprocessing_multiplier": preprocessing_multiplier,
        "calibration_variant_count": len(calibrations),
        "factorized_candidate_count": factorized_candidate_count,
        "candidate_count": len(grid),
        "is_full_cartesian_grid": factorized_candidate_count == len(grid),
        "split_evaluations": repeated_evaluations,
        "linear_calibration_candidate_count": linear_calibration_candidates,
        "calibration_inner_fits": calibration_inner_fits,
        "feature_selector_main_fits": selector_main_fits,
        "feature_selector_calibration_inner_fits": selector_calibration_inner_fits,
        "approximate_base_fits": approximate_base_fits,
        "approximate_tuning_fits": approximate_tuning_fits,
        "n_jobs_requested": config.n_jobs,
        "n_jobs_resolved": resolved_n_jobs,
        "parallel_backend": config.parallel_backend,
        "parallel_batch_size": config.parallel_batch_size,
        "approximate_parallel_waves": approximate_parallel_waves,
        "finalist_count_requested": config.finalist_count,
        "finalist_count_effective": effective_finalists,
        "finalist_base_fits_min": finalist_base_fits_min,
        "finalist_base_fits_max": finalist_base_fits_max,
    }


def format_stage4_linear_experiment_plan(plan: Mapping[str, object]) -> str:
    """Format a reader-facing pre-fit experiment complexity summary."""
    selector_counts = plan["feature_selector_counts"]
    model_counts = plan["model_config_counts"]
    assert isinstance(selector_counts, Mapping)
    assert isinstance(model_counts, Mapping)
    finalist_fit_text = str(plan["finalist_base_fits_min"])
    if plan["finalist_base_fits_min"] != plan["finalist_base_fits_max"]:
        finalist_fit_text += f"..{plan['finalist_base_fits_max']}"

    lines = [
        "Experiment plan",
        "===============",
        "",
        "Target:",
        f"  target_col: {plan['target_col']}",
        "",
        "Feature set:",
        f"  feature_set: {plan['feature_set']}",
        f"  include_schedule_context: {plan['include_schedule_context']}",
    ]
    if plan.get("candidate_feature_count") is not None:
        lines.append(f"  candidate_features: {plan['candidate_feature_count']}")
    lines.extend(
        [
            "",
            "Grid source:",
            f"  grid_source: {plan['grid_source']}",
            f"  grid_preset: {plan['grid_preset']}",
            "",
            "Validation:",
            f"  metric: {plan['tuning_metric']}",
            f"  holdout_strategy: {plan['holdout_strategy']}",
            f"  repeated_holdout_repeats: {plan['repeated_holdout_repeats']}",
            f"  temporal_holdout_repeats: {plan['temporal_holdout_repeats']}",
            f"  tuning_holdout_count: {plan['tuning_holdout_count']}",
            f"  temporal_validation_rows: {plan['temporal_validation_rows']}",
            f"  baseline_strategy: {plan['baseline_strategy']}",
            f"  repeated_holdout_seed: {plan['repeated_holdout_seed']}",
            "",
            "Enabled preprocessing:",
            _plan_option_line("robust_clips", plan["robust_clips"]),
            _plan_option_line("target_transforms", plan["target_transforms"]),
            _plan_option_line("prediction_clips", plan["prediction_clips"]),
            _plan_option_line("calibrations", plan["calibrations"]),
            f"  calibration_cv_folds: {plan['calibration_cv_folds']}",
            "",
            "Feature selection:",
            "  enabled modes:",
        ]
    )
    lines.extend(f"    {mode}: {count}" for mode, count in selector_counts.items())
    lines.extend(
        [
            f"  total feature selector configs: {plan['feature_selector_config_count']}",
            "",
            "Model configs:",
        ]
    )
    lines.extend(f"  {model_kind}: {count}" for model_kind, count in model_counts.items())
    lines.extend(
        [
            f"  total model configs: {plan['model_config_count']}",
            "",
            "Candidate count:",
            f"  preprocessing multiplier: {plan['preprocessing_multiplier']}",
            f"  feature selectors: {plan['feature_selector_config_count']}",
            f"  model configs: {plan['model_config_count']}",
            f"  calibration variants: {plan['calibration_variant_count']}",
            f"  factorized candidate count: {plan['factorized_candidate_count']}",
            f"  actual candidates: {plan['candidate_count']}",
            f"  full Cartesian grid: {plan['is_full_cartesian_grid']}",
            "",
            "Evaluation cost:",
            f"  tuning holdouts: {plan['tuning_holdout_count']}",
            f"  candidate evaluation tasks: {plan['split_evaluations']}",
            f"  calibration model inner fits: {plan['calibration_inner_fits']}",
            f"  feature-selector main fits: {plan['feature_selector_main_fits']}",
            f"  feature-selector calibration inner fits: {plan['feature_selector_calibration_inner_fits']}",
            f"  approximate base fits: {plan['approximate_base_fits']}",
            f"  approximate total tuning fits: {plan['approximate_tuning_fits']}",
            "",
            "Parallel execution:",
            f"  n_jobs requested: {plan['n_jobs_requested']}",
            f"  n_jobs resolved: {plan['n_jobs_resolved']}",
            f"  backend: {plan['parallel_backend']}",
            f"  batch_size: {plan['parallel_batch_size']}",
            f"  approximate candidate-task waves: {plan['approximate_parallel_waves']}",
            "",
            "Automatic finalist fallback:",
            f"  shortlist_count: {plan['shortlist_count']}",
            f"  finalist_count requested: {plan['finalist_count_requested']}",
            f"  finalist_count effective: {plan['finalist_count_effective']}",
            f"  finalist base fits: {finalist_fit_text}",
        ]
    )
    return "\n".join(lines)


def stage4_linear_experiment_budget_issues(
    plan: Mapping[str, object],
    *,
    max_candidates: int | None = None,
    max_approximate_tuning_fits: int | None = None,
) -> list[str]:
    """Describe experiment-plan dimensions that exceed configured safety budgets."""
    issues: list[str] = []
    checks = [
        ("candidate_count", max_candidates, "candidates"),
        ("approximate_tuning_fits", max_approximate_tuning_fits, "approximate tuning fits"),
    ]
    for plan_key, limit, label in checks:
        if limit is None:
            continue
        if int(limit) < 1:
            raise ValueError(f"{plan_key} budget must be at least 1")
        actual = int(plan[plan_key])
        if actual > int(limit):
            issues.append(f"{label}: {actual:,} exceeds safety budget {int(limit):,}")
    return issues


def regression_metrics(y_true: Any, y_pred: Any) -> dict[str, float]:
    """Compute Stage 4 regression metrics on the original target scale."""
    y = np.asarray(y_true, dtype=float)
    pred = np.asarray(y_pred, dtype=float)
    valid = np.isfinite(y) & np.isfinite(pred)
    if not bool(valid.any()):
        return {
            "n_rows": 0,
            "mae": np.nan,
            "rmse": np.nan,
            "r2": np.nan,
            "pearson": np.nan,
            "spearman": np.nan,
            "bias_pred_minus_target": np.nan,
            "pred_mean": np.nan,
            "pred_min": np.nan,
            "pred_max": np.nan,
        }
    y = y[valid]
    pred = pred[valid]
    return {
        "n_rows": int(len(y)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
        "r2": float(r2_score(y, pred)) if len(y) > 1 and np.nanstd(y) > 0 else np.nan,
        "pearson": _safe_corr(y, pred, method="pearson"),
        "spearman": _safe_corr(y, pred, method="spearman"),
        "bias_pred_minus_target": float(np.mean(pred - y)),
        "pred_mean": float(np.mean(pred)),
        "pred_min": float(np.min(pred)),
        "pred_max": float(np.max(pred)),
    }


def tune_stage4_linear_candidates(
    splits: Mapping[str, pd.DataFrame],
    feature_columns: Sequence[str],
    candidates: Sequence[Stage4LinearCandidate],
    *,
    config: Stage4LinearConfig | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tune candidates using repeated train/validation holdouts inside pre-test history."""
    config = config or Stage4LinearConfig()
    holdouts = make_stage4_linear_tuning_holdouts(splits, config=config)
    repeat_rows: list[dict[str, object]] = []
    total_evaluations = len(holdouts) * len(candidates)
    completed_evaluations = 0
    if progress_callback is not None:
        progress_callback(completed_evaluations, total_evaluations)
    for holdout in holdouts:
        train_df = holdout["train"]
        valid_df = holdout["valid"]
        assert isinstance(train_df, pd.DataFrame)
        assert isinstance(valid_df, pd.DataFrame)
        holdout_type = str(holdout.get("holdout_type", "random"))
        baseline_value = dummy_baseline_value(
            train_df,
            config.baseline_strategy,
            target_col=config.target_col,
        )
        baseline_train_pred = np.full(len(train_df), baseline_value, dtype=float)
        baseline_valid_pred = np.full(len(valid_df), baseline_value, dtype=float)
        baseline_metrics = {
            "baseline_strategy": config.baseline_strategy,
            "baseline_value": baseline_value,
            **{
                f"baseline_train_{key}": value
                for key, value in regression_metrics(
                    train_df[config.target_col],
                    baseline_train_pred,
                ).items()
            },
            **{
                f"baseline_valid_{key}": value
                for key, value in regression_metrics(
                    valid_df[config.target_col],
                    baseline_valid_pred,
                ).items()
            },
        }
        task_args = [
            (
                train_df,
                valid_df,
                feature_columns,
                candidate,
                config,
                holdout_type,
                int(holdout["repeat"]),
                int(holdout["random_state"]),
                baseline_metrics,
            )
            for candidate in candidates
        ]
        holdout_rows: list[dict[str, object]] = []
        if config.n_jobs == 1:
            results = (_evaluate_stage4_linear_candidate_holdout(*args) for args in task_args)
        else:
            results = Parallel(
                n_jobs=config.n_jobs,
                backend=config.parallel_backend,
                batch_size=config.parallel_batch_size,
                return_as="generator",
            )(
                delayed(_evaluate_stage4_linear_candidate_holdout)(*args)
                for args in task_args
            )
        for row in results:
            holdout_rows.append(row)
            completed_evaluations += 1
            if progress_callback is not None:
                progress_callback(completed_evaluations, total_evaluations)
        repeat_rows.extend(holdout_rows)

    repeat_df = pd.DataFrame(repeat_rows)
    summary = aggregate_tuning_repeats(repeat_df, config=config)
    return repeat_df, summary


def _evaluate_stage4_linear_candidate_holdout(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    feature_columns: Sequence[str],
    candidate: Stage4LinearCandidate,
    config: Stage4LinearConfig,
    holdout_type: str,
    holdout_repeat: int,
    holdout_random_state: int,
    baseline_metrics: Mapping[str, object],
) -> dict[str, object]:
    fitted = fit_stage4_linear_candidate(
        train_df,
        feature_columns,
        candidate,
        config=config,
    )
    train_pred = predict_stage4_linear(fitted, train_df)
    valid_pred = predict_stage4_linear(fitted, valid_df)
    row = {
        "holdout_type": holdout_type,
        "holdout_repeat": holdout_repeat,
        "holdout_random_state": holdout_random_state,
        **_candidate_record(candidate),
        "selected_feature_count": len(fitted.selected_features),
        **baseline_metrics,
    }
    row.update(
        {
            f"train_{key}": value
            for key, value in regression_metrics(
                train_df[config.target_col],
                train_pred,
            ).items()
        }
    )
    row.update(
        {
            f"valid_{key}": value
            for key, value in regression_metrics(
                valid_df[config.target_col],
                valid_pred,
            ).items()
        }
    )
    baseline_valid_mae = float(row.get("baseline_valid_mae", np.nan))
    valid_mae = float(row.get("valid_mae", np.nan))
    if np.isfinite(baseline_valid_mae) and baseline_valid_mae > 0 and np.isfinite(valid_mae):
        relative_mae = valid_mae / baseline_valid_mae
        row["valid_mae_relative_to_baseline"] = relative_mae
        row["valid_mae_skill_vs_baseline"] = 1.0 - relative_mae
        row["valid_mae_delta_vs_baseline"] = baseline_valid_mae - valid_mae
        row["valid_mae_beats_baseline"] = int(valid_mae < baseline_valid_mae)
    else:
        row["valid_mae_relative_to_baseline"] = np.nan
        row["valid_mae_skill_vs_baseline"] = np.nan
        row["valid_mae_delta_vs_baseline"] = np.nan
        row["valid_mae_beats_baseline"] = 0
    row.update(_calibration_record_for_table(fitted.calibration_record))
    return row


def aggregate_tuning_repeats(
    repeat_df: pd.DataFrame,
    *,
    config: Stage4LinearConfig | None = None,
) -> pd.DataFrame:
    """Aggregate repeated holdout rows into a validation-ranked candidate table."""
    config = config or Stage4LinearConfig()
    if config.tuning_metric not in STAGE4_LINEAR_TUNING_METRICS:
        raise ValueError(f"Unsupported tuning metric: {config.tuning_metric}")
    candidate_cols = [
        "candidate_id",
        "model_kind",
        "feature_selection_mode",
        "feature_selection_top_k",
        "feature_selection_min_features",
        "feature_selection_min_abs_spearman",
        "feature_selection_min_mutual_info",
        "feature_selection_correlation_threshold",
        "feature_selection_lasso_alpha",
        "robust_clip",
        "calibration",
        "target_transform",
        "prediction_clip",
        "alpha",
        "l1_ratio",
        "epsilon",
        "n_components",
        "fit_intercept",
        "max_iter",
        "tol",
    ]
    metric_cols = [
        column
        for column in repeat_df.columns
        if column.startswith(("train_", "valid_", "baseline_"))
        and pd.api.types.is_numeric_dtype(repeat_df[column])
    ]
    extra_numeric = [
        column
        for column in ["selected_feature_count", "calibration_applied", "calibration_intercept", "calibration_slope"]
        if column in repeat_df.columns
    ]
    grouped = repeat_df.groupby(candidate_cols, dropna=False)
    summary = grouped[[*metric_cols, *extra_numeric]].agg(["mean", "std", "min", "max"])
    summary.columns = [
        column if stat == "mean" else f"{column}_{stat}"
        for column, stat in summary.columns.to_flat_index()
    ]
    summary = summary.reset_index()
    holdout_keys = ["holdout_repeat"]
    if "holdout_type" in repeat_df.columns:
        holdout_keys.insert(0, "holdout_type")
    summary["tuning_repeated_holdout_repeats"] = int(repeat_df[holdout_keys].drop_duplicates().shape[0])
    if "holdout_type" in repeat_df.columns:
        holdout_counts = (
            repeat_df[["holdout_type", "holdout_repeat"]]
            .drop_duplicates()
            .groupby("holdout_type")
            .size()
            .to_dict()
        )
        summary["tuning_random_holdout_repeats"] = int(holdout_counts.get("random", 0))
        summary["tuning_temporal_holdout_repeats"] = int(holdout_counts.get("temporal", 0))
    summary["tuning_repeated_holdout_random_states"] = ",".join(
        str(value) for value in sorted(repeat_df["holdout_random_state"].unique())
    )
    summary = _add_holdout_type_validation_summary(summary, repeat_df)
    metric_col = f"valid_{config.tuning_metric}"
    ascending = config.tuning_metric in {"mae", "rmse"}
    summary = summary.sort_values(metric_col, ascending=ascending, na_position="last").reset_index(drop=True)
    summary["selection_metric"] = config.tuning_metric
    summary["selection_metric_value"] = summary[metric_col]
    summary["selection_metric_std"] = summary.get(f"{metric_col}_std", np.nan)
    summary = enrich_stage4_linear_validation_summary(summary)
    summary = _add_mixed_holdout_ranking(summary, config=config)
    if config.holdout_strategy == "mixed" and "combined_rank_score" in summary.columns:
        summary = summary.sort_values("combined_rank_score", ascending=True, na_position="last").reset_index(drop=True)
        summary["selection_metric"] = "combined_rank_score"
        summary["selection_metric_value"] = summary["combined_rank_score"]
        summary["selection_metric_std"] = summary.get("temporal_relative_mae_std", np.nan)
    summary["selection_rank"] = np.arange(1, len(summary) + 1)
    return summary


def _add_holdout_type_validation_summary(
    summary: pd.DataFrame,
    repeat_df: pd.DataFrame,
) -> pd.DataFrame:
    if "holdout_type" not in repeat_df.columns:
        return summary
    metric_cols = [
        "train_mae",
        "train_rmse",
        "train_r2",
        "valid_mae",
        "valid_rmse",
        "valid_r2",
        "valid_spearman",
        "valid_mae_relative_to_baseline",
        "valid_mae_skill_vs_baseline",
        "valid_mae_delta_vs_baseline",
        "valid_mae_beats_baseline",
    ]
    available_metric_cols = [
        column
        for column in metric_cols
        if column in repeat_df.columns and pd.api.types.is_numeric_dtype(repeat_df[column])
    ]
    if not available_metric_cols:
        return summary

    pieces: list[pd.DataFrame] = []
    for holdout_type, type_df in repeat_df.groupby("holdout_type", dropna=False):
        label = str(holdout_type)
        grouped = type_df.groupby("candidate_id", dropna=False)
        type_summary = grouped[available_metric_cols].agg(["mean", "std", "min", "max"])
        type_summary.columns = [
            f"{label}_{column}" if stat == "mean" else f"{label}_{column}_{stat}"
            for column, stat in type_summary.columns.to_flat_index()
        ]
        type_summary = type_summary.reset_index()
        count_col = f"{label}_holdout_count"
        type_summary[count_col] = grouped.size().to_numpy(dtype=int)
        if "valid_mae_beats_baseline" in type_df.columns:
            wins = grouped["valid_mae_beats_baseline"].sum().rename(f"{label}_baseline_wins").reset_index()
            type_summary = type_summary.merge(wins, on="candidate_id", how="left")
        pieces.append(type_summary)

    out = summary.copy()
    for piece in pieces:
        out = out.merge(piece, on="candidate_id", how="left")

    for label in ("random", "temporal"):
        rename = {
            f"{label}_train_mae": f"{label}_mean_train_mae",
            f"{label}_train_mae_std": f"{label}_std_train_mae",
            f"{label}_train_rmse": f"{label}_mean_train_rmse",
            f"{label}_train_r2": f"{label}_mean_train_r2",
            f"{label}_valid_mae": f"{label}_mean_valid_mae",
            f"{label}_valid_mae_std": f"{label}_std_valid_mae",
            f"{label}_valid_rmse": f"{label}_mean_valid_rmse",
            f"{label}_valid_r2": f"{label}_mean_valid_r2",
            f"{label}_valid_mae_relative_to_baseline": f"{label}_mean_relative_mae",
            f"{label}_valid_mae_relative_to_baseline_std": f"{label}_relative_mae_std",
            f"{label}_valid_mae_relative_to_baseline_max": f"{label}_worst_relative_mae",
            f"{label}_valid_mae_skill_vs_baseline": f"{label}_mean_skill_vs_baseline",
            f"{label}_valid_mae_delta_vs_baseline": f"{label}_mean_delta_mae_vs_baseline",
        }
        out = out.rename(columns={source: target for source, target in rename.items() if source in out.columns})
    return out


def _percentile_rank(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.notna()
    ranks = pd.Series(np.nan, index=series.index, dtype="float64")
    if not bool(valid.any()):
        return ranks
    ranks.loc[valid] = numeric.loc[valid].rank(method="average", ascending=True, pct=True)
    return ranks


def _add_mixed_holdout_ranking(
    summary: pd.DataFrame,
    *,
    config: Stage4LinearConfig,
) -> pd.DataFrame:
    out = summary.copy()
    if config.holdout_strategy != "mixed":
        return out

    required = {
        "temporal_mean_relative_mae",
        "temporal_worst_relative_mae",
        "random_mean_relative_mae",
        "random_relative_mae_std",
    }
    for column in required:
        if column not in out.columns:
            out[column] = np.nan

    out["temporal_mean_relative_mae_percentile"] = _percentile_rank(out["temporal_mean_relative_mae"])
    out["temporal_worst_relative_mae_percentile"] = _percentile_rank(out["temporal_worst_relative_mae"])
    out["random_mean_relative_mae_percentile"] = _percentile_rank(out["random_mean_relative_mae"])
    out["random_relative_mae_std_percentile"] = _percentile_rank(out["random_relative_mae_std"])

    out["combined_rank_score"] = (
        config.combined_temporal_mean_weight * out["temporal_mean_relative_mae_percentile"]
        + config.combined_temporal_worst_weight * out["temporal_worst_relative_mae_percentile"]
        + config.combined_random_mean_weight * out["random_mean_relative_mae_percentile"]
        + config.combined_random_stability_weight * out["random_relative_mae_std_percentile"]
    )
    temporal_min_wins = min(config.shortlist_min_baseline_wins, max(1, config.temporal_holdout_repeats))
    random_min_wins = min(config.shortlist_min_baseline_wins, max(1, config.repeated_holdout_repeats))
    temporal_wins = pd.to_numeric(
        out.get("temporal_baseline_wins", pd.Series(0, index=out.index)),
        errors="coerce",
    ).fillna(0)
    random_wins = pd.to_numeric(
        out.get("random_baseline_wins", pd.Series(0, index=out.index)),
        errors="coerce",
    ).fillna(0)
    worst_temporal = pd.to_numeric(out["temporal_worst_relative_mae"], errors="coerce")
    out["baseline_gate_pass"] = (
        temporal_wins.ge(temporal_min_wins)
        & random_wins.ge(random_min_wins)
        & worst_temporal.le(config.shortlist_temporal_worst_relative_mae_max)
    )
    return out


def enrich_stage4_linear_validation_summary(summary: pd.DataFrame) -> pd.DataFrame:
    """Add explicit mean/std aliases and compact candidate parameter labels."""
    out = summary.copy()
    metric_aliases = {
        "train_mae": "mean_train_mae",
        "train_mae_std": "std_train_mae",
        "train_rmse": "mean_train_rmse",
        "train_rmse_std": "std_train_rmse",
        "train_r2": "mean_train_r2",
        "train_r2_std": "std_train_r2",
        "valid_mae": "mean_valid_mae",
        "valid_mae_std": "std_valid_mae",
        "valid_rmse": "mean_valid_rmse",
        "valid_rmse_std": "std_valid_rmse",
        "valid_r2": "mean_valid_r2",
        "valid_r2_std": "std_valid_r2",
        "valid_pearson": "mean_valid_pearson",
        "valid_pearson_std": "std_valid_pearson",
        "valid_spearman": "mean_valid_spearman",
        "valid_spearman_std": "std_valid_spearman",
        "selected_feature_count": "mean_selected_feature_count",
        "selected_feature_count_std": "std_selected_feature_count",
    }
    for source, alias in metric_aliases.items():
        if source in out.columns:
            out[alias] = out[source]
    parameter_records = out.apply(_validation_parameter_record, axis=1, result_type="expand")
    for column in parameter_records.columns:
        out[column] = parameter_records[column]
    if {"mean_valid_mae", "mean_train_mae"} <= set(out.columns):
        out["mean_mae_generalization_gap"] = out["mean_valid_mae"] - out["mean_train_mae"]
    return out


def fit_stage4_linear_candidate(
    train_df: pd.DataFrame,
    feature_columns: Sequence[str],
    candidate: Stage4LinearCandidate,
    *,
    config: Stage4LinearConfig | None = None,
) -> FittedStage4LinearModel:
    """Fit one candidate, including train-only feature selection and OOF calibration."""
    config = config or Stage4LinearConfig()
    scores = train_feature_scores(train_df, feature_columns, config=config)
    selected_features, detail = select_stage4_features(
        train_df,
        feature_columns,
        candidate.feature_selection,
        scores=scores,
        config=config,
    )
    pipeline = make_stage4_linear_pipeline(train_df, selected_features, candidate, config=config)
    y_fit = _transform_target(train_df[config.target_col], candidate.target_transform)
    _fit_estimator_suppressing_convergence_warnings(pipeline, train_df[selected_features], y_fit)
    calibration_record = fit_oof_calibration(
        train_df,
        feature_columns,
        candidate,
        config=config,
    )
    return FittedStage4LinearModel(
        pipeline=pipeline,
        selected_features=selected_features,
        candidate=candidate,
        calibration_record=calibration_record,
        feature_selection_detail=detail,
    )


def predict_stage4_linear(fitted: FittedStage4LinearModel, frame: pd.DataFrame) -> np.ndarray:
    raw = np.ravel(fitted.pipeline.predict(frame[fitted.selected_features]))
    pred = _inverse_transform_target(raw, fitted.candidate.target_transform)
    pred = apply_prediction_clip(pred, fitted.candidate.prediction_clip)
    pred = apply_calibration(pred, fitted.calibration_record)
    return apply_prediction_clip(pred, fitted.candidate.prediction_clip)


def evaluate_stage4_linear_contiguous_dev_diagnostic(
    splits: Mapping[str, pd.DataFrame],
    feature_columns: Sequence[str],
    candidate: Stage4LinearCandidate,
    *,
    config: Stage4LinearConfig | None = None,
    train_fraction: float = 0.70,
    valid_fraction: float = 0.15,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit one candidate on early dev history and evaluate three contiguous dev segments."""
    config = config or Stage4LinearConfig()
    if not 0.0 < train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0.0 < valid_fraction < 1.0:
        raise ValueError("valid_fraction must be between 0 and 1")
    if train_fraction + valid_fraction >= 1.0:
        raise ValueError("train_fraction + valid_fraction must be less than 1")
    dev = (
        pd.concat([splits["train"], splits["valid"]], ignore_index=True)
        .sort_values(["calendarDate", "analysis_window_id"])
        .reset_index(drop=True)
    )
    train_end = max(1, int(math.floor(len(dev) * train_fraction)))
    valid_end = max(train_end + 1, int(math.floor(len(dev) * (train_fraction + valid_fraction))))
    valid_end = min(valid_end, len(dev) - 1)
    diagnostic_splits = {
        "dev_train": dev.iloc[:train_end].copy().reset_index(drop=True),
        "dev_valid": dev.iloc[train_end:valid_end].copy().reset_index(drop=True),
        "dev_test": dev.iloc[valid_end:].copy().reset_index(drop=True),
    }
    if any(split.empty for split in diagnostic_splits.values()):
        raise ValueError("Not enough dev rows for the requested contiguous diagnostic split")

    fitted = fit_stage4_linear_candidate(
        diagnostic_splits["dev_train"],
        feature_columns,
        candidate,
        config=config,
    )
    metric_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    for split_name, split_df in diagnostic_splits.items():
        pred = predict_stage4_linear(fitted, split_df)
        metric_rows.append(
            {
                **_candidate_record(candidate),
                "split": split_name,
                "diagnostic_fit_rows": len(diagnostic_splits["dev_train"]),
                "diagnostic_dev_rows": len(dev),
                **regression_metrics(split_df[config.target_col], pred),
            }
        )
        prediction_frames.append(
            _prediction_frame(
                split_df,
                config.target_col,
                pred,
                model_name=f"candidate_{candidate.candidate_id}",
                model_kind=candidate.model_kind,
                split_name=split_name,
                candidate=candidate,
                validation_selection_rank=1,
                prediction_provenance="contiguous_dev_diagnostic",
            )
        )
    return pd.DataFrame(metric_rows), pd.concat(prediction_frames, ignore_index=True)


def evaluate_stage4_linear_finalists(
    splits: Mapping[str, pd.DataFrame],
    feature_columns: Sequence[str],
    tuning_summary: pd.DataFrame,
    candidates: Sequence[Stage4LinearCandidate],
    *,
    config: Stage4LinearConfig | None = None,
    finalist_candidate_ids: Sequence[int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Refit validation-selected finalists on all pre-test rows and evaluate the future test."""
    config = config or Stage4LinearConfig()
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    if finalist_candidate_ids is None:
        finalist_ids = tuning_summary.head(config.finalist_count)["candidate_id"].astype(int).tolist()
    else:
        requested_ids = list(dict.fromkeys(int(candidate_id) for candidate_id in finalist_candidate_ids))
        missing_ids = sorted(set(requested_ids) - set(candidate_by_id))
        if missing_ids:
            raise KeyError(f"Unknown finalist candidate ids: {missing_ids}")
        tuning_ids = set(tuning_summary["candidate_id"].astype(int))
        missing_summary_ids = sorted(set(requested_ids) - tuning_ids)
        if missing_summary_ids:
            raise KeyError(f"Finalist candidate ids missing from tuning summary: {missing_summary_ids}")
        finalist_ids = requested_ids
    pretest = (
        pd.concat([splits["train"], splits["valid"]], ignore_index=True)
        .sort_values(["calendarDate", "analysis_window_id"])
        .reset_index(drop=True)
    )
    eval_splits = {
        "dev": pretest,
        "test": splits["test"],
    }
    metric_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    selection_rows: list[dict[str, object]] = []
    detail_frames: list[pd.DataFrame] = []
    tuning_lookup = tuning_summary.set_index("candidate_id").to_dict("index")
    task_args = [
        (
            int(candidate_id),
            candidate_by_id[int(candidate_id)],
            tuning_lookup[int(candidate_id)],
            pretest,
            eval_splits,
            feature_columns,
            config,
        )
        for candidate_id in finalist_ids
    ]
    if config.n_jobs == 1:
        finalist_results = [
            _evaluate_stage4_linear_finalist(*args)
            for args in task_args
        ]
    else:
        finalist_results = Parallel(
            n_jobs=config.n_jobs,
            backend=config.parallel_backend,
            batch_size=config.parallel_batch_size,
        )(
            delayed(_evaluate_stage4_linear_finalist)(*args)
            for args in task_args
        )
    for selection_row, candidate_metric_rows, candidate_prediction_frames, detail in finalist_results:
        selection_rows.append(selection_row)
        metric_rows.extend(candidate_metric_rows)
        prediction_frames.extend(candidate_prediction_frames)
        detail_frames.append(detail)
    return (
        pd.DataFrame(selection_rows),
        pd.DataFrame(metric_rows),
        pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame(),
        pd.concat(detail_frames, ignore_index=True) if detail_frames else pd.DataFrame(),
    )


def _evaluate_stage4_linear_finalist(
    candidate_id: int,
    candidate: Stage4LinearCandidate,
    tuning_row: Mapping[str, object],
    pretest: pd.DataFrame,
    eval_splits: Mapping[str, pd.DataFrame],
    feature_columns: Sequence[str],
    config: Stage4LinearConfig,
) -> tuple[dict[str, object], list[dict[str, object]], list[pd.DataFrame], pd.DataFrame]:
    fitted = fit_stage4_linear_candidate(pretest, feature_columns, candidate, config=config)
    validation_rank = int(tuning_row["selection_rank"])
    selection_row = {
        **_candidate_record(candidate),
        "validation_selection_rank": validation_rank,
        "validation_selection_metric": tuning_row["selection_metric"],
        "validation_selection_metric_value": float(tuning_row["selection_metric_value"]),
        "validation_selection_metric_std": float(tuning_row.get("selection_metric_std", np.nan)),
        "final_refit_rows": len(pretest),
        "selected_feature_count_final_refit": len(fitted.selected_features),
        **_calibration_record_for_table(fitted.calibration_record),
    }
    detail = fitted.feature_selection_detail.copy()
    detail.insert(0, "candidate_id", candidate_id)
    detail.insert(1, "validation_selection_rank", validation_rank)
    metric_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    for split_name, split_df in eval_splits.items():
        pred = predict_stage4_linear(fitted, split_df)
        metric_rows.append(
            {
                **_candidate_record(candidate),
                "validation_selection_rank": validation_rank,
                "split": split_name,
                "final_refit_rows": len(pretest),
                "selected_feature_count_final_refit": len(fitted.selected_features),
                **regression_metrics(split_df[config.target_col], pred),
            }
        )
        prediction_frames.append(
            _prediction_frame(
                split_df,
                config.target_col,
                pred,
                model_name=f"candidate_{candidate_id}",
                model_kind=candidate.model_kind,
                split_name=split_name,
                candidate=candidate,
                validation_selection_rank=validation_rank,
                prediction_provenance=(
                    "final_refit_future_test"
                    if split_name == "test"
                    else "final_refit_in_sample_dev"
                ),
            )
        )
    return selection_row, metric_rows, prediction_frames, detail


def tune_dummy_baselines(
    splits: Mapping[str, pd.DataFrame],
    *,
    config: Stage4LinearConfig | None = None,
) -> pd.DataFrame:
    """Aggregate dummy-baseline validation metrics over the repeated pre-test holdouts."""
    config = config or Stage4LinearConfig()
    holdouts = make_stage4_linear_tuning_holdouts(splits, config=config)
    rows: list[dict[str, object]] = []
    for holdout in holdouts:
        train_df = holdout["train"]
        valid_df = holdout["valid"]
        assert isinstance(train_df, pd.DataFrame)
        assert isinstance(valid_df, pd.DataFrame)
        for strategy in STAGE4_LINEAR_DUMMY_STRATEGIES:
            value = dummy_baseline_value(train_df, strategy, target_col=config.target_col)
            pred = np.full(len(valid_df), value, dtype=float)
            row = {
                "candidate_type": "dummy",
                "model_kind": strategy,
                "holdout_type": str(holdout.get("holdout_type", "random")),
                "holdout_repeat": int(holdout["repeat"]),
                "holdout_random_state": int(holdout["random_state"]),
            }
            train_pred = np.full(len(train_df), value, dtype=float)
            row.update(
                {
                    f"train_{key}": metric
                    for key, metric in regression_metrics(
                        train_df[config.target_col],
                        train_pred,
                    ).items()
                }
            )
            row.update({f"valid_{key}": metric for key, metric in regression_metrics(valid_df[config.target_col], pred).items()})
            rows.append(row)
    repeat_df = pd.DataFrame(rows)
    metric_cols = [
        column
        for column in repeat_df.columns
        if column.startswith(("train_", "valid_")) and pd.api.types.is_numeric_dtype(repeat_df[column])
    ]
    summary = repeat_df.groupby(["candidate_type", "model_kind"], dropna=False)[metric_cols].agg(["mean", "std"])
    summary.columns = [column if stat == "mean" else f"{column}_{stat}" for column, stat in summary.columns.to_flat_index()]
    summary = summary.reset_index()
    if "holdout_type" in repeat_df.columns:
        for holdout_type, type_df in repeat_df.groupby("holdout_type", dropna=False):
            label = str(holdout_type)
            type_metrics = type_df.groupby("model_kind", dropna=False)[
                ["train_mae", "valid_mae"]
            ].agg(["mean", "std", "max"])
            type_metrics.columns = [
                f"{label}_{metric}_{stat}"
                for metric, stat in type_metrics.columns.to_flat_index()
            ]
            type_metrics = type_metrics.rename(
                columns={
                    f"{label}_train_mae_mean": f"{label}_mean_train_mae",
                    f"{label}_train_mae_std": f"{label}_std_train_mae",
                    f"{label}_valid_mae_mean": f"{label}_mean_valid_mae",
                    f"{label}_valid_mae_std": f"{label}_std_valid_mae",
                    f"{label}_valid_mae_max": f"{label}_worst_valid_mae",
                }
            ).reset_index()
            summary = summary.merge(type_metrics, on="model_kind", how="left")
    metric_col = f"valid_{config.tuning_metric}"
    ascending = config.tuning_metric in {"mae", "rmse"}
    summary = summary.sort_values(metric_col, ascending=ascending, na_position="last").reset_index(drop=True)
    summary["selection_metric"] = config.tuning_metric
    summary["selection_metric_value"] = summary[metric_col]
    summary["selection_metric_std"] = summary.get(f"{metric_col}_std", np.nan)
    for source, alias in {
        "valid_mae": "mean_valid_mae",
        "valid_mae_std": "std_valid_mae",
        "valid_rmse": "mean_valid_rmse",
        "valid_rmse_std": "std_valid_rmse",
        "valid_r2": "mean_valid_r2",
        "valid_r2_std": "std_valid_r2",
        "train_mae": "mean_train_mae",
        "train_mae_std": "std_train_mae",
        "train_rmse": "mean_train_rmse",
        "train_rmse_std": "std_train_rmse",
        "train_r2": "mean_train_r2",
        "train_r2_std": "std_train_r2",
    }.items():
        if source in summary.columns:
            summary[alias] = summary[source]
    return summary


def evaluate_dummy_baselines(
    splits: Mapping[str, pd.DataFrame],
    *,
    config: Stage4LinearConfig | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit dummy baselines on all pre-test rows and evaluate dev/test."""
    config = config or Stage4LinearConfig()
    pretest = (
        pd.concat([splits["train"], splits["valid"]], ignore_index=True)
        .sort_values(["calendarDate", "analysis_window_id"])
        .reset_index(drop=True)
    )
    eval_splits = {
        "dev": pretest,
        "test": splits["test"],
    }
    metric_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    for strategy in STAGE4_LINEAR_DUMMY_STRATEGIES:
        value = dummy_baseline_value(pretest, strategy, target_col=config.target_col)
        for split_name, split_df in eval_splits.items():
            pred = np.full(len(split_df), value, dtype=float)
            metric_rows.append(
                {
                    "candidate_type": "dummy",
                    "model_kind": strategy,
                    "baseline_value": value,
                    "split": split_name,
                    "final_refit_rows": len(pretest),
                    **regression_metrics(split_df[config.target_col], pred),
                }
            )
            prediction_frames.append(
                _prediction_frame(
                    split_df,
                    config.target_col,
                    pred,
                    model_name=strategy,
                    model_kind=strategy,
                    split_name=split_name,
                    candidate_type="dummy",
                    prediction_provenance=(
                        "dummy_future_test"
                        if split_name == "test"
                        else "dummy_pretest_baseline"
                    ),
                )
            )
    return pd.DataFrame(metric_rows), pd.concat(prediction_frames, ignore_index=True)


def build_stage4_linear_leaderboard(
    tuning_summary: pd.DataFrame,
    final_metrics: pd.DataFrame,
    dummy_tuning_summary: pd.DataFrame,
    dummy_metrics: pd.DataFrame,
    *,
    top_n_tuned: int = 25,
) -> pd.DataFrame:
    """Combine validation-ranked candidates with final metrics for selected finalists."""
    test_metrics = final_metrics.loc[final_metrics["split"].eq("test")].copy()
    finalist_cols = [
        "candidate_id",
        "mae",
        "rmse",
        "r2",
        "pearson",
        "spearman",
        "bias_pred_minus_target",
        "pred_mean",
        "pred_min",
        "pred_max",
        "selected_feature_count_final_refit",
    ]
    test_lookup = test_metrics[[column for column in finalist_cols if column in test_metrics.columns]].rename(
        columns={
            "mae": "test_mae",
            "rmse": "test_rmse",
            "r2": "test_r2",
            "pearson": "test_pearson",
            "spearman": "test_spearman",
            "bias_pred_minus_target": "test_bias_pred_minus_target",
            "pred_mean": "test_pred_mean",
            "pred_min": "test_pred_min",
            "pred_max": "test_pred_max",
        }
    )
    model_rows = tuning_summary.head(top_n_tuned).copy()
    model_rows.insert(0, "candidate_type", "linear_family")
    model_rows = model_rows.merge(test_lookup, on="candidate_id", how="left")

    dummy_test = dummy_metrics.loc[dummy_metrics["split"].eq("test")].copy()
    dummy_rows = dummy_tuning_summary.merge(
        dummy_test[
            [
                "model_kind",
                "baseline_value",
                "mae",
                "rmse",
                "r2",
                "pearson",
                "spearman",
                "bias_pred_minus_target",
                "pred_mean",
                "pred_min",
                "pred_max",
            ]
        ].rename(
            columns={
                "mae": "test_mae",
                "rmse": "test_rmse",
                "r2": "test_r2",
                "pearson": "test_pearson",
                "spearman": "test_spearman",
                "bias_pred_minus_target": "test_bias_pred_minus_target",
                "pred_mean": "test_pred_mean",
                "pred_min": "test_pred_min",
                "pred_max": "test_pred_max",
            }
        ),
        on="model_kind",
        how="left",
    )
    dummy_rows["candidate_id"] = np.nan
    dummy_rows["selection_rank"] = np.nan
    dummy_rows["feature_selection_mode"] = "none"
    dummy_rows["robust_clip"] = "none"
    dummy_rows["calibration"] = "none"
    dummy_rows["target_transform"] = "none"
    dummy_rows["prediction_clip"] = "none"
    common_cols = list(dict.fromkeys([*model_rows.columns, *dummy_rows.columns]))
    return pd.concat(
        [model_rows.reindex(columns=common_cols), dummy_rows.reindex(columns=common_cols)],
        ignore_index=True,
    )


def build_stage4_linear_leaderboard_slices(
    tuning_summary: pd.DataFrame,
    final_metrics: pd.DataFrame,
    dummy_tuning_summary: pd.DataFrame,
    dummy_metrics: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build compact validation-first leaderboard views for public reporting."""
    overall = tuning_summary.sort_values("selection_rank").reset_index(drop=True)
    best_by_model = overall.drop_duplicates(["model_kind"], keep="first").reset_index(drop=True)
    best_by_model_feature_selection = overall.drop_duplicates(
        ["model_kind", "feature_selection_mode"],
        keep="first",
    ).reset_index(drop=True)
    final_future_test = (
        final_metrics.loc[final_metrics["split"].eq("test")]
        .sort_values("validation_selection_rank")
        .reset_index(drop=True)
    )
    dummy_future = (
        dummy_metrics.loc[dummy_metrics["split"].eq("test")]
        .reset_index(drop=True)
    )
    dummy_cols = [
        "model_kind",
        "baseline_value",
        "mae",
        "rmse",
        "r2",
        "bias_pred_minus_target",
    ]
    dummy_baselines = dummy_tuning_summary.merge(
        dummy_future[[column for column in dummy_cols if column in dummy_future.columns]].rename(
            columns={
                "mae": "test_mae",
                "rmse": "test_rmse",
                "r2": "test_r2",
                "bias_pred_minus_target": "test_bias_pred_minus_target",
            }
        ),
        on="model_kind",
        how="left",
    )
    dummy_sort_col = (
        "selection_metric_value"
        if "selection_metric_value" in dummy_baselines.columns
        else "mean_valid_mae"
    )
    dummy_baselines = dummy_baselines.sort_values(dummy_sort_col).reset_index(drop=True)
    return {
        "overall_validation": overall,
        "best_by_model_kind": best_by_model,
        "best_by_model_kind_feature_selection": best_by_model_feature_selection,
        "dummy_baselines": dummy_baselines,
        "final_future_test": final_future_test,
    }


def build_stage4_linear_validation_slices(
    tuning_summary: pd.DataFrame,
    dummy_tuning_summary: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build validation-only tables that are safe to inspect before finalist refit."""
    overall = enrich_stage4_linear_validation_summary(tuning_summary)
    overall = overall.sort_values("selection_rank").reset_index(drop=True)
    best_by_model = overall.drop_duplicates(["model_kind"], keep="first").reset_index(drop=True)
    best_by_model_feature_selection = overall.drop_duplicates(
        ["model_kind", "feature_selection_mode"],
        keep="first",
    ).reset_index(drop=True)
    return {
        "overall_validation": overall,
        "best_by_model_kind": best_by_model,
        "best_by_model_kind_feature_selection": best_by_model_feature_selection,
        "dummy_validation": dummy_tuning_summary.sort_values("selection_metric_value").reset_index(drop=True),
    }


def select_stage4_linear_future_test_candidates(
    tuning_summary: pd.DataFrame,
    *,
    global_top_n: int = 1,
    model_family_top_n: int = 1,
) -> pd.DataFrame:
    """Select future-test candidates by validation rank before opening the future test."""
    if global_top_n < 0 or model_family_top_n < 0:
        raise ValueError("future-test selection counts must be non-negative")
    if tuning_summary.empty:
        return tuning_summary.copy()

    data = tuning_summary.sort_values(["selection_rank", "candidate_id"]).reset_index(drop=True)
    roles: dict[int, set[str]] = {}

    def add_rows(rows: pd.DataFrame, role: str) -> None:
        for candidate_id in rows["candidate_id"].astype(int).tolist():
            roles.setdefault(candidate_id, set()).add(role)

    add_rows(data.head(global_top_n), "global_validation_leader")
    for _, group in data.groupby("model_kind", dropna=False, sort=False):
        add_rows(group.head(model_family_top_n), "model_family_validation_leader")

    selected = data.loc[data["candidate_id"].astype(int).isin(roles)].copy()
    selected["future_test_selection_roles"] = selected["candidate_id"].astype(int).map(
        lambda candidate_id: "|".join(sorted(roles[candidate_id]))
    )
    selected.insert(0, "future_test_selection_order", np.arange(1, len(selected) + 1))
    return selected.reset_index(drop=True)


def build_stage4_linear_shortlist(
    tuning_summary: pd.DataFrame,
    *,
    config: Stage4LinearConfig | None = None,
) -> pd.DataFrame:
    """Build a bounded, model-family-representative shortlist from mixed validation."""
    config = config or Stage4LinearConfig()
    if tuning_summary.empty:
        return tuning_summary.copy()
    if config.shortlist_count < 1:
        raise ValueError("shortlist_count must be at least 1")

    data = tuning_summary.copy()
    score_col = "combined_rank_score" if "combined_rank_score" in data.columns else "selection_metric_value"
    data = data.sort_values([score_col, "candidate_id"], ascending=[True, True], na_position="last").reset_index(drop=True)
    eligible = (
        data.loc[data["baseline_gate_pass"].fillna(False)].copy()
        if "baseline_gate_pass" in data.columns
        else data.copy()
    )
    if eligible.empty:
        eligible = data.copy()

    roles: dict[int, set[str]] = {}

    def add_rows(rows: pd.DataFrame, role: str) -> None:
        for candidate_id in rows["candidate_id"].astype(int).tolist():
            roles.setdefault(candidate_id, set()).add(role)

    add_rows(data.head(config.shortlist_global_top_n), "global_top")
    if "temporal_mean_relative_mae" in data.columns:
        add_rows(
            data.nsmallest(config.shortlist_temporal_mean_top_n, "temporal_mean_relative_mae"),
            "temporal_mean_leader",
        )
    if "temporal_worst_relative_mae" in data.columns:
        add_rows(
            data.nsmallest(config.shortlist_temporal_worst_top_n, "temporal_worst_relative_mae"),
            "temporal_worst_leader",
        )
    if "random_relative_mae_std" in data.columns:
        add_rows(
            data.nsmallest(config.shortlist_random_stability_top_n, "random_relative_mae_std"),
            "random_stability_leader",
        )

    for _, group in data.groupby("model_kind", dropna=False, sort=False):
        add_rows(group.head(config.shortlist_model_family_top_n), "model_family_representative")
    for _, group in data.groupby("feature_selection_mode", dropna=False, sort=False):
        add_rows(group.head(config.shortlist_selector_top_n), "selector_representative")
    for _, group in data.groupby("target_transform", dropna=False, sort=False):
        add_rows(group.head(config.shortlist_target_transform_top_n), "target_transform_representative")
    for _, group in data.groupby("calibration", dropna=False, sort=False):
        add_rows(group.head(config.shortlist_calibration_top_n), "calibration_representative")

    protected_roles = {
        "global_top",
        "model_family_representative",
        "selector_representative",
    }
    protected_ids = {
        candidate_id
        for candidate_id, candidate_roles in roles.items()
        if candidate_roles & protected_roles
    }
    selected_ids = set(roles)
    if len(selected_ids) > config.shortlist_count:
        optional = data.loc[
            data["candidate_id"].astype(int).isin(selected_ids - protected_ids)
        ]["candidate_id"].astype(int).tolist()
        room = max(0, config.shortlist_count - len(protected_ids))
        selected_ids = {*protected_ids, *optional[:room]}
    elif len(selected_ids) < config.shortlist_count:
        ordered_fill = pd.concat([eligible, data], ignore_index=True).drop_duplicates("candidate_id")
        for candidate_id in ordered_fill["candidate_id"].astype(int):
            if len(selected_ids) >= config.shortlist_count:
                break
            if candidate_id in selected_ids:
                continue
            selected_ids.add(candidate_id)
            roles.setdefault(candidate_id, set()).add("combined_rank_fill")

    shortlist = data.loc[data["candidate_id"].astype(int).isin(selected_ids)].copy()
    shortlist["shortlist_roles"] = shortlist["candidate_id"].astype(int).map(
        lambda candidate_id: ",".join(sorted(roles.get(candidate_id, {"combined_rank_fill"})))
    )
    shortlist["shortlist_protected"] = shortlist["candidate_id"].astype(int).isin(protected_ids)
    shortlist = shortlist.sort_values([score_col, "candidate_id"], ascending=[True, True], na_position="last").reset_index(drop=True)
    shortlist.insert(0, "shortlist_rank", np.arange(1, len(shortlist) + 1))
    return shortlist


def build_stage4_linear_paired_deltas(
    tuning_summary: pd.DataFrame,
    *,
    factor: str,
    reference: str,
    metric_col: str = "mean_valid_mae",
) -> pd.DataFrame:
    """Pair otherwise-identical candidates and compute validation-MAE deltas."""
    data = enrich_stage4_linear_validation_summary(tuning_summary)
    if metric_col not in data.columns:
        raise KeyError(f"tuning_summary missing paired-delta metric: {metric_col}")
    factor_columns = {
        "calibration": ["calibration"],
        "robust_clip": ["robust_clip"],
        "target_transform": ["target_transform"],
        "prediction_clip": ["prediction_clip"],
        "feature_selection": [
            "feature_selection_mode",
            "feature_selection_top_k",
            "feature_selection_min_features",
            "feature_selection_min_abs_spearman",
            "feature_selection_min_mutual_info",
            "feature_selection_correlation_threshold",
            "feature_selection_lasso_alpha",
            "feature_selection_config_label",
        ],
    }
    if factor not in factor_columns:
        raise ValueError(f"Unsupported paired-delta factor: {factor}")
    if factor == "feature_selection":
        data["factor_value"] = data["feature_selection_config_label"]
        reference_value = "none"
    else:
        data["factor_value"] = data[factor].astype(str)
        reference_value = reference
    base_candidate_columns = [
        "model_kind",
        "alpha",
        "l1_ratio",
        "epsilon",
        "n_components",
        "fit_intercept",
        "max_iter",
        "tol",
        "robust_clip",
        "calibration",
        "target_transform",
        "prediction_clip",
        "feature_selection_mode",
        "feature_selection_top_k",
        "feature_selection_min_features",
        "feature_selection_min_abs_spearman",
        "feature_selection_min_mutual_info",
        "feature_selection_correlation_threshold",
        "feature_selection_lasso_alpha",
    ]
    ignored = set(factor_columns[factor])
    pair_columns = [column for column in base_candidate_columns if column not in ignored and column in data.columns]
    reference_rows = data.loc[data["factor_value"].eq(reference_value)].copy()
    variants = data.loc[~data["factor_value"].eq(reference_value)].copy()
    if reference_rows.empty or variants.empty:
        return pd.DataFrame()
    reference_rows = reference_rows[
        [*pair_columns, metric_col, "candidate_id"]
    ].rename(
        columns={
            metric_col: "reference_mean_valid_mae",
            "candidate_id": "reference_candidate_id",
        }
    )
    paired = variants.merge(reference_rows, on=pair_columns, how="inner")
    if paired.empty:
        return paired
    paired["reference_value"] = reference_value
    paired["delta_mean_valid_mae"] = (
        paired[metric_col] - paired["reference_mean_valid_mae"]
    )
    paired["paired_metric"] = metric_col
    paired["delta_direction"] = np.where(
        paired["delta_mean_valid_mae"].lt(0),
        "improved",
        "worsened_or_equal",
    )
    return paired.sort_values(["factor_value", "model_kind", "delta_mean_valid_mae"]).reset_index(drop=True)


def stage4_linear_candidate_from_record(record: Mapping[str, object]) -> Stage4LinearCandidate:
    """Rebuild a linear-family candidate from a leaderboard or grid row."""
    selection = Stage4FeatureSelectionConfig(
        mode=str(_record_value(record, "feature_selection_mode", "none")),
        top_k=int(float(_record_value(record, "feature_selection_top_k", 40))),
        min_features=int(float(_record_value(record, "feature_selection_min_features", 8))),
        min_abs_spearman=float(_record_value(record, "feature_selection_min_abs_spearman", 0.0)),
        min_mutual_info=float(_record_value(record, "feature_selection_min_mutual_info", 0.0)),
        correlation_threshold=float(_record_value(record, "feature_selection_correlation_threshold", 0.95)),
        lasso_alpha=float(_record_value(record, "feature_selection_lasso_alpha", 0.03)),
        lasso_max_iter=int(float(_record_value(record, "feature_selection_lasso_max_iter", 50_000))),
    )
    candidate_id = int(float(_record_value(record, "candidate_id", -1)))
    return Stage4LinearCandidate(
        candidate_id=candidate_id,
        model_kind=str(_record_value(record, "model_kind", "linear")),
        feature_selection=selection,
        robust_clip=str(_record_value(record, "robust_clip", "none")),
        calibration=str(_record_value(record, "calibration", "none")),
        target_transform=str(_record_value(record, "target_transform", "none")),
        prediction_clip=str(_record_value(record, "prediction_clip", "0_100")),
        alpha=_optional_record_float(record, "alpha"),
        l1_ratio=_optional_record_float(record, "l1_ratio"),
        epsilon=_optional_record_float(record, "epsilon"),
        n_components=_optional_record_int(record, "n_components"),
        fit_intercept=bool(_record_value(record, "fit_intercept", True)),
        max_iter=int(float(_record_value(record, "max_iter", 50_000))),
        tol=float(_record_value(record, "tol", 1e-4)),
    )


def extract_stage4_linear_coefficient_table(fitted: FittedStage4LinearModel) -> pd.DataFrame:
    """Return signed standardized coefficients aggregated back to source features."""
    model = fitted.pipeline.named_steps["model"]
    coefficients = _estimator_coefficients(model)
    empty = pd.DataFrame(
        {
            "feature": fitted.selected_features,
            "standardized_coefficient": np.nan,
            "abs_standardized_coefficient": np.nan,
            "transformed_feature_count": 0,
            "coefficient_available": False,
        }
    )
    if coefficients is None:
        return empty
    coef = np.ravel(np.asarray(coefficients, dtype=float))
    try:
        names = np.asarray(fitted.pipeline.named_steps["preprocess"].get_feature_names_out(), dtype=str)
    except Exception:
        names = np.asarray(fitted.selected_features, dtype=str)
    if len(coef) != len(names):
        return empty

    transformed = pd.DataFrame(
        {
            "transformed_feature": names,
            "coefficient": coef,
        }
    )
    transformed["feature"] = [
        _source_feature_from_transformed_name(name, fitted.selected_features)
        for name in transformed["transformed_feature"]
    ]
    transformed["abs_coefficient"] = transformed["coefficient"].abs()
    rows: list[dict[str, object]] = []
    for feature, group in transformed.groupby("feature", sort=False):
        max_abs_idx = group["abs_coefficient"].idxmax()
        rows.append(
            {
                "feature": feature,
                "standardized_coefficient": float(transformed.loc[max_abs_idx, "coefficient"]),
                "abs_standardized_coefficient": float(group["abs_coefficient"].sum()),
                "transformed_feature_count": int(len(group)),
                "coefficient_available": True,
            }
        )
    return pd.DataFrame(rows)


def compute_stage4_linear_feature_importance(
    splits: Mapping[str, pd.DataFrame],
    feature_columns: Sequence[str],
    candidate: Stage4LinearCandidate,
    *,
    config: Stage4LinearConfig | None = None,
    permutation_repeats: int = 10,
    random_state: int | None = None,
) -> pd.DataFrame:
    """Compute rank-1 coefficient and validation permutation-importance diagnostics.

    Coefficients are fit on train+valid pre-test history. Permutation importance
    is fit on the train split and evaluated on the validation split; the future
    test split is not read by this helper.
    """
    config = config or Stage4LinearConfig()
    if "train" not in splits or "valid" not in splits:
        raise KeyError("splits must include train and valid frames")
    repeats = max(1, int(permutation_repeats))
    rng = np.random.default_rng(config.random_state if random_state is None else random_state)
    pretest = (
        pd.concat([splits["train"], splits["valid"]], ignore_index=True)
        .sort_values(["calendarDate", "analysis_window_id"])
        .reset_index(drop=True)
    )
    final_fitted = fit_stage4_linear_candidate(pretest, feature_columns, candidate, config=config)
    validation_fitted = fit_stage4_linear_candidate(
        splits["train"],
        feature_columns,
        candidate,
        config=config,
    )

    coefficient_table = extract_stage4_linear_coefficient_table(final_fitted)
    valid_df = splits["valid"].copy().reset_index(drop=True)
    baseline_pred = predict_stage4_linear(validation_fitted, valid_df)
    baseline_mae = regression_metrics(valid_df[config.target_col], baseline_pred)["mae"]
    permutation_rows: list[dict[str, object]] = []
    for feature in validation_fitted.selected_features:
        if feature not in valid_df.columns:
            continue
        deltas: list[float] = []
        for _ in range(repeats):
            permuted = valid_df.copy()
            permuted[feature] = rng.permutation(permuted[feature].to_numpy(copy=True))
            permuted_pred = predict_stage4_linear(validation_fitted, permuted)
            permuted_mae = regression_metrics(valid_df[config.target_col], permuted_pred)["mae"]
            deltas.append(float(permuted_mae - baseline_mae))
        permutation_rows.append(
            {
                "feature": feature,
                "permutation_mae_increase_mean": float(np.mean(deltas)),
                "permutation_mae_increase_std": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
            }
        )
    permutation_table = pd.DataFrame(permutation_rows)
    all_features = pd.DataFrame(
        {
            "feature": list(
                dict.fromkeys(
                    [
                        *coefficient_table["feature"].astype(str).tolist(),
                        *permutation_table.get("feature", pd.Series(dtype=str)).astype(str).tolist(),
                    ]
                )
            )
        }
    )
    out = all_features.merge(coefficient_table, on="feature", how="left")
    out = out.merge(permutation_table, on="feature", how="left")
    out["final_refit_selected"] = out["feature"].isin(final_fitted.selected_features)
    out["validation_fit_selected"] = out["feature"].isin(validation_fitted.selected_features)
    out["coefficient_fit_source"] = "final_refit_pretest"
    out["permutation_fit_source"] = "train_split_model"
    out["permutation_eval_split"] = "valid"
    out["baseline_valid_mae"] = float(baseline_mae)
    out["permutation_repeats"] = repeats
    out["_permutation_sort"] = pd.to_numeric(
        out["permutation_mae_increase_mean"],
        errors="coerce",
    ).fillna(-np.inf)
    out["_coefficient_sort"] = pd.to_numeric(
        out["abs_standardized_coefficient"],
        errors="coerce",
    ).fillna(-np.inf)
    out = out.sort_values(
        ["_permutation_sort", "_coefficient_sort", "feature"],
        ascending=[False, False, True],
    ).drop(columns=["_permutation_sort", "_coefficient_sort"])
    out["rank"] = np.arange(1, len(out) + 1)
    return out.reset_index(drop=True)


def build_stage4_linear_best_by_model_family_artifact(
    validation_summary: pd.DataFrame,
    dummy_tuning_summary: pd.DataFrame | None = None,
    leaderboard: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build one validation-selected row per model family plus dummy baselines."""
    original_validation = validation_summary.reset_index(drop=True).copy()
    validation = enrich_stage4_linear_validation_summary(validation_summary)
    for column in [
        "candidate_short_label",
        "model_param_1",
        "model_param_2",
        "feature_selection_config_label",
        "feature_selection_param_1",
        "feature_selection_param_2",
        "model_parameter_label",
        "feature_selection_parameter_label",
    ]:
        if column in original_validation.columns:
            original_values = original_validation[column].replace("", np.nan)
            validation[column] = original_values.combine_first(validation.get(column, pd.Series(index=validation.index)))
    sort_col = "selection_rank" if "selection_rank" in validation.columns else "mean_valid_mae"
    validation = validation.sort_values(sort_col, na_position="last").reset_index(drop=True)
    family_rows = validation.drop_duplicates("model_kind", keep="first").copy()
    if "candidate_type" in family_rows.columns:
        family_rows["candidate_type"] = "linear_family"
    else:
        family_rows.insert(0, "candidate_type", "linear_family")

    if leaderboard is not None and not leaderboard.empty:
        family_rows = _attach_leaderboard_test_metrics(family_rows, leaderboard)

    frames = [family_rows]
    if dummy_tuning_summary is not None and not dummy_tuning_summary.empty:
        dummy_rows = _normalize_dummy_validation_summary(dummy_tuning_summary)
        if "candidate_type" in dummy_rows.columns:
            dummy_rows["candidate_type"] = "dummy"
        else:
            dummy_rows.insert(0, "candidate_type", "dummy")
        if leaderboard is not None and not leaderboard.empty:
            dummy_rows = _attach_dummy_test_metrics(dummy_rows, leaderboard)
        frames.append(dummy_rows)

    out = pd.concat(frames, ignore_index=True, sort=False)
    minimum_cols = [
        "candidate_type",
        "model_kind",
        "candidate_short_label",
        "feature_selection_mode",
        "robust_clip",
        "calibration",
        "mean_valid_mae",
        "std_valid_mae",
        "mean_valid_r2",
        "mean_valid_spearman",
        "test_mae",
        "test_r2",
    ]
    for column in minimum_cols:
        if column not in out.columns:
            out[column] = np.nan
    leading = [column for column in minimum_cols if column in out.columns]
    trailing = [column for column in out.columns if column not in leading]
    return out[leading + trailing]


def plot_stage4_linear_rank1_feature_importance(
    importance: pd.DataFrame,
    *,
    top_n: int = 20,
    save_path: str | Path | None = None,
) -> Any:
    """Plot independently ranked dev-refit coefficients and validation permutation importance."""
    import matplotlib.pyplot as plt

    required = {
        "feature",
        "standardized_coefficient",
        "abs_standardized_coefficient",
        "permutation_mae_increase_mean",
        "permutation_mae_increase_std",
        "rank",
    }
    missing = sorted(required - set(importance.columns))
    if missing:
        raise KeyError(f"importance missing required columns: {missing}")
    top_n = max(1, int(top_n))
    coefficient_available = (
        importance["coefficient_available"].fillna(False)
        if "coefficient_available" in importance.columns
        else importance["standardized_coefficient"].notna()
    )
    coefficient_data = (
        importance.loc[coefficient_available]
        .dropna(subset=["abs_standardized_coefficient"])
        .nlargest(top_n, "abs_standardized_coefficient")
        .sort_values("abs_standardized_coefficient")
    )
    permutation_data = (
        importance.dropna(subset=["permutation_mae_increase_mean"])
        .nlargest(top_n, "permutation_mae_increase_mean")
        .sort_values("permutation_mae_increase_mean")
    )
    fig_height = max(5.8, 0.34 * max(len(coefficient_data), len(permutation_data)) + 1.8)
    fig, axes = plt.subplots(1, 2, figsize=(14, fig_height), constrained_layout=True)
    coef_values = pd.to_numeric(coefficient_data["standardized_coefficient"], errors="coerce").to_numpy(dtype=float)
    coef_colors = np.where(coef_values >= 0, "#4C78A8", "#F58518")
    axes[0].barh(coefficient_data["feature"], coef_values, color=coef_colors, alpha=0.88)
    axes[0].axvline(0.0, color="#333333", linewidth=1.0)
    axes[0].set_title("Dev-Refit Coefficients: Top Absolute Effects")
    axes[0].set_xlabel("Signed coefficient on standardized/preprocessed scale")
    axes[0].set_ylabel("")
    axes[0].grid(True, axis="x", color="#E6E6E6")

    permutation_values = pd.to_numeric(
        permutation_data["permutation_mae_increase_mean"],
        errors="coerce",
    ).to_numpy(dtype=float)
    permutation_error = pd.to_numeric(
        permutation_data["permutation_mae_increase_std"],
        errors="coerce",
    ).fillna(0.0).to_numpy(dtype=float)
    axes[1].barh(
        permutation_data["feature"],
        permutation_values,
        xerr=permutation_error,
        color="#C89B4B",
        alpha=0.88,
        error_kw={"ecolor": "#333333", "elinewidth": 1.0, "capsize": 2},
    )
    axes[1].axvline(0.0, color="#333333", linewidth=1.0)
    axes[1].set_title("Contiguous Validation Permutation Importance")
    axes[1].set_xlabel("Validation MAE increase when permuted")
    axes[1].set_ylabel("")
    axes[1].grid(True, axis="x", color="#E6E6E6")
    fig.suptitle("Rank-1 Feature Diagnostics: Independent Top-N Lists And Scales")
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=170, bbox_inches="tight")
    return fig


def tune_stage4_linear_modeling(
    frame: pd.DataFrame,
    feature_catalog: pd.DataFrame,
    *,
    config: Stage4LinearConfig | None = None,
    candidates: Sequence[Stage4LinearCandidate] | None = None,
    grid_spec: Stage4LinearGridSpec | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Stage4LinearTuningResult:
    """Run candidate tuning and validation diagnostics without evaluating future test."""
    config = config or Stage4LinearConfig()
    feature_columns = resolve_stage4_feature_columns(
        feature_catalog,
        feature_set=config.feature_set,
        include_schedule_context=config.include_schedule_context,
    )
    model_frame = prepare_stage4_linear_model_frame(
        frame,
        feature_columns,
        target_col=config.target_col,
        split_col=config.split_col,
    )
    splits = split_stage4_model_frame(model_frame, split_col=config.split_col)
    if candidates is None and grid_spec is None and config.grid_source != "preset":
        raise ValueError(
            "Explicit candidates or grid_spec are required when config.grid_source is not 'preset'"
        )
    candidate_list = (
        list(candidates)
        if candidates is not None
        else build_stage4_linear_candidate_grid(config, grid_spec)
    )
    candidate_df = candidate_grid_frame(candidate_list)
    experiment_plan = build_stage4_linear_experiment_plan(
        config,
        candidate_list,
        feature_columns=feature_columns,
    )
    tuning_repeats, tuning_summary = tune_stage4_linear_candidates(
        splits,
        feature_columns,
        candidate_list,
        config=config,
        progress_callback=progress_callback,
    )
    dummy_tuning_summary = tune_dummy_baselines(splits, config=config)
    shortlist_summary = (
        build_stage4_linear_shortlist(tuning_summary, config=config)
        if config.holdout_strategy == "mixed"
        else pd.DataFrame()
    )
    validation_slices = build_stage4_linear_validation_slices(
        tuning_summary,
        dummy_tuning_summary,
    )
    if not shortlist_summary.empty:
        validation_slices["shortlist"] = shortlist_summary
    return Stage4LinearTuningResult(
        config=config,
        feature_columns=feature_columns,
        candidates=candidate_list,
        splits=dict(splits),
        candidate_grid=candidate_df,
        experiment_plan=experiment_plan,
        tuning_repeats=tuning_repeats,
        tuning_summary=tuning_summary,
        dummy_tuning_summary=dummy_tuning_summary,
        shortlist_summary=shortlist_summary,
        validation_slices=validation_slices,
    )


def refresh_stage4_linear_tuning_result_summaries(
    tuning_result: Stage4LinearTuningResult,
) -> Stage4LinearTuningResult:
    """Reaggregate stored holdout evaluations without refitting candidate models."""
    config = tuning_result.config
    tuning_summary = aggregate_tuning_repeats(tuning_result.tuning_repeats, config=config)
    dummy_tuning_summary = tune_dummy_baselines(tuning_result.splits, config=config)
    shortlist_summary = (
        build_stage4_linear_shortlist(tuning_summary, config=config)
        if config.holdout_strategy == "mixed"
        else pd.DataFrame()
    )
    validation_slices = build_stage4_linear_validation_slices(
        tuning_summary,
        dummy_tuning_summary,
    )
    if not shortlist_summary.empty:
        validation_slices["shortlist"] = shortlist_summary
    return Stage4LinearTuningResult(
        config=config,
        feature_columns=tuning_result.feature_columns,
        candidates=tuning_result.candidates,
        splits=tuning_result.splits,
        candidate_grid=tuning_result.candidate_grid,
        experiment_plan=tuning_result.experiment_plan,
        tuning_repeats=tuning_result.tuning_repeats,
        tuning_summary=tuning_summary,
        dummy_tuning_summary=dummy_tuning_summary,
        shortlist_summary=shortlist_summary,
        validation_slices=validation_slices,
    )


def finalize_stage4_linear_modeling(
    tuning_result: Stage4LinearTuningResult,
    *,
    finalist_candidate_ids: Sequence[int] | None = None,
) -> Stage4LinearRunResult:
    """Refit validation-selected finalists and evaluate the reserved future test."""
    config = tuning_result.config
    model_selection_summary, final_metrics, final_predictions, feature_selection_detail = evaluate_stage4_linear_finalists(
        tuning_result.splits,
        tuning_result.feature_columns,
        tuning_result.tuning_summary,
        tuning_result.candidates,
        config=config,
        finalist_candidate_ids=finalist_candidate_ids,
    )
    dummy_metrics, dummy_predictions = evaluate_dummy_baselines(tuning_result.splits, config=config)
    leaderboard = build_stage4_linear_leaderboard(
        tuning_result.tuning_summary,
        final_metrics,
        tuning_result.dummy_tuning_summary,
        dummy_metrics,
    )
    leaderboard_slices = build_stage4_linear_leaderboard_slices(
        tuning_result.tuning_summary,
        final_metrics,
        tuning_result.dummy_tuning_summary,
        dummy_metrics,
    )
    all_predictions = pd.concat([final_predictions, dummy_predictions], ignore_index=True)
    return Stage4LinearRunResult(
        config=config,
        feature_columns=tuning_result.feature_columns,
        candidate_grid=tuning_result.candidate_grid,
        tuning_repeats=tuning_result.tuning_repeats,
        tuning_summary=tuning_result.tuning_summary,
        dummy_tuning_summary=tuning_result.dummy_tuning_summary,
        shortlist_summary=tuning_result.shortlist_summary,
        model_selection_summary=model_selection_summary,
        final_metrics=final_metrics,
        dummy_metrics=dummy_metrics,
        leaderboard=leaderboard,
        leaderboard_slices=leaderboard_slices,
        final_predictions=all_predictions,
        feature_selection_detail=feature_selection_detail,
    )


def run_stage4_linear_modeling(
    frame: pd.DataFrame,
    feature_catalog: pd.DataFrame,
    *,
    config: Stage4LinearConfig | None = None,
    candidates: Sequence[Stage4LinearCandidate] | None = None,
    grid_spec: Stage4LinearGridSpec | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Stage4LinearRunResult:
    """Run the Stage 4 linear-family modeling pass from frame to leaderboard."""
    tuning_result = tune_stage4_linear_modeling(
        frame,
        feature_catalog,
        config=config,
        candidates=candidates,
        grid_spec=grid_spec,
        progress_callback=progress_callback,
    )
    return finalize_stage4_linear_modeling(tuning_result)


def build_stage4_linear_summary_markdown(result: Stage4LinearRunResult) -> str:
    """Build the public markdown summary for the Stage 4 linear modeling pass."""
    cfg = result.config
    slices = result.leaderboard_slices or build_stage4_linear_leaderboard_slices(
        result.tuning_summary,
        result.final_metrics,
        result.dummy_tuning_summary,
        result.dummy_metrics,
    )
    best_validation = slices["overall_validation"].head(10).copy()
    best_by_model = slices["best_by_model_kind"].copy()
    best_by_model_feature_selection = slices["best_by_model_kind_feature_selection"].head(24).copy()
    finalist_test = slices["final_future_test"].copy()
    dummy_test = result.dummy_metrics.loc[result.dummy_metrics["split"].eq("test")].copy()
    dummy_baselines = slices["dummy_baselines"].copy()
    selected_dummy_test = dummy_test.loc[dummy_test["model_kind"].eq(cfg.baseline_strategy)].copy()
    selected_dummy_test_mae = (
        float(selected_dummy_test.iloc[0]["mae"])
        if not selected_dummy_test.empty
        else np.nan
    )
    best_model_test_mae = float(finalist_test.sort_values("validation_selection_rank").iloc[0]["mae"]) if not finalist_test.empty else np.nan
    best_model_validation_rank = int(finalist_test.sort_values("validation_selection_rank").iloc[0]["validation_selection_rank"]) if not finalist_test.empty else 0
    improvement = selected_dummy_test_mae - best_model_test_mae
    improvement_pct = 100.0 * improvement / selected_dummy_test_mae if np.isfinite(selected_dummy_test_mae) and selected_dummy_test_mae else np.nan

    validation_cols = [
        "selection_rank",
        "candidate_short_label",
        "model_kind",
        "model_param_1",
        "model_param_2",
        "feature_selection_mode",
        "feature_selection_param_1",
        "feature_selection_param_2",
        "robust_clip",
        "calibration",
        "mean_train_mae",
        "mean_train_rmse",
        "mean_train_r2",
        "mean_valid_mae",
        "std_valid_mae",
        "mean_valid_rmse",
        "mean_valid_r2",
        "mean_valid_spearman",
        "mean_selected_feature_count",
    ]
    test_cols = [
        "validation_selection_rank",
        "model_kind",
        "feature_selection_mode",
        "robust_clip",
        "calibration",
        "mae",
        "rmse",
        "r2",
        "pearson",
        "spearman",
        "bias_pred_minus_target",
        "selected_feature_count_final_refit",
    ]
    dummy_cols = [
        "model_kind",
        "baseline_value",
        "valid_mae",
        "valid_mae_std",
        "test_mae",
        "test_rmse",
        "test_r2",
        "test_bias_pred_minus_target",
    ]
    dummy_test_cols = [
        "model_kind",
        "preselected_for_comparison",
        "baseline_value",
        "mae",
        "rmse",
        "r2",
        "bias_pred_minus_target",
    ]

    if cfg.holdout_strategy == "mixed":
        tuning_description = (
            f"`{cfg.repeated_holdout_repeats}` random holdouts plus "
            f"`{cfg.temporal_holdout_repeats}` expanding temporal holdouts inside the pre-test history"
        )
        selection_description = (
            "Model selection uses a combined rank led by temporal mean relative MAE, with temporal worst-fold "
            "performance and random-holdout performance/stability as secondary criteria. Relative MAE is measured "
            f"against `{cfg.baseline_strategy}` fit on each holdout's training rows."
        )
    else:
        tuning_description = (
            f"`{cfg.repeated_holdout_repeats}` repeated train/validation holdouts inside the pre-test history"
        )
        selection_description = "Model selection is based on repeated-holdout validation only."
    dummy_test["preselected_for_comparison"] = dummy_test["model_kind"].eq(cfg.baseline_strategy)
    dummy_test = dummy_test.sort_values(
        ["preselected_for_comparison", "model_kind"],
        ascending=[False, True],
    )

    lines = [
        "# Stage 4 Sleep Stress Linear Models",
        "",
        "This report evaluates linear-family regression models for next-sleep average stress using the Stage 4 `day D -> next sleep` modeling frame. It is an exploratory single-subject modeling pass, not a production predictor or health recommendation.",
        "",
        "## Modeling Setup",
        "",
        f"- Target: `{cfg.target_col}`",
        f"- Feature set: `{cfg.feature_set}`",
        f"- Candidate features: `{len(result.feature_columns)}`",
        f"- Grid source: `{cfg.grid_source}`",
        f"- Grid preset: `{cfg.grid_preset}`" if cfg.grid_source == "preset" else "- Grid preset: not used",
        f"- Split strategy: `{cfg.split_col}` with a fixed future holdout excluded from model selection",
        f"- Tuning: {tuning_description}",
        f"- Tuning metric: `{cfg.tuning_metric}`",
        f"- Parallel candidate jobs: `{cfg.n_jobs}` with `{cfg.parallel_backend}` backend",
        f"- Definitive rerank candidates: `{len(result.candidate_grid)}` linear-family configurations",
        f"- Representative validation shortlist: `{len(result.shortlist_summary)}` candidates",
        f"- Validation-selected finalists refit on all dev rows before fixed-future-holdout evaluation: `{len(result.model_selection_summary)}`",
        f"- Dummy baselines: `{', '.join(STAGE4_LINEAR_DUMMY_STRATEGIES)}`",
        f"- Comparison baseline selected before fixed-future-holdout evaluation: `{cfg.baseline_strategy}`",
        "",
        "Preprocessing is fit inside each training split: numeric median imputation, optional train-fitted z clipping, standardization, and categorical one-hot encoding when categorical predictors are present. Feature selection and optional linear calibration are also fit without using validation or test target values; calibration uses out-of-fold pre-test predictions.",
        "",
        f"{selection_description} The fixed future holdout is evaluated only after validation-selected finalists are frozen and refit on all development rows. Any future-holdout ordering among finalists is diagnostic only, not a tuning rule.",
        "",
        "## Validation Leaders",
        "",
        _markdown_table(best_validation, validation_cols),
        "",
        "## Best Validation Candidate By Model",
        "",
        _markdown_table(best_by_model, validation_cols),
        "",
        "## Best Validation Candidate By Model And Feature Selection",
        "",
        _markdown_table(best_by_model_feature_selection, validation_cols),
        "",
        "## Fixed Future Holdout For Validation-Selected Finalists",
        "",
        _markdown_table(finalist_test.sort_values("validation_selection_rank"), test_cols),
        "",
        "## Dummy Baselines",
        "",
        _markdown_table(dummy_baselines, dummy_cols),
        "",
        "## Dummy Baselines On Fixed Future Holdout",
        "",
        _markdown_table(dummy_test, dummy_test_cols),
        "",
        "## Conservative Read",
        "",
    ]
    if np.isfinite(improvement):
        lines.append(
            f"The validation-selected rank `{best_model_validation_rank}` finalist improved fixed-future-holdout MAE by `{improvement:.3f}` points versus the preselected `{cfg.baseline_strategy}` baseline (`{improvement_pct:.1f}%`)."
        )
    lines.extend(
        [
            "The result should be read as evidence of modest wearable-signal association, not reliable night-level prediction. The fixed future holdout is one contiguous period, so performance can still be sensitive to nonstationarity and the single-person data context.",
            "",
        ]
    )
    return "\n".join(lines)


def plot_stage4_linear_prediction_diagnostics(
    predictions: pd.DataFrame,
    *,
    target_col: str = STAGE4_PRIMARY_TARGET,
    validation_selection_rank: int = 1,
    splits: Sequence[str] = ("dev", "test"),
    normalize_histogram: bool = True,
    save_path: str | Path | None = None,
    title: str | None = None,
) -> Any:
    """Plot actual/predicted and residual diagnostics for one finalist."""
    import matplotlib.pyplot as plt

    required = {"calendarDate", "split", target_col, "prediction", "residual"}
    missing = sorted(required - set(predictions.columns))
    if missing:
        raise KeyError(f"predictions missing required columns: {missing}")
    data = predictions.copy()
    if "validation_selection_rank" in data.columns:
        data = data.loc[data["validation_selection_rank"].eq(validation_selection_rank)].copy()
    if "candidate_type" in data.columns:
        data = data.loc[data["candidate_type"].eq("linear_family")].copy()
    data = data.loc[data["split"].isin(splits)].copy()
    data["calendarDate"] = pd.to_datetime(data["calendarDate"], errors="coerce")
    for column in [target_col, "prediction", "residual"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=["calendarDate", target_col, "prediction", "residual"])
    if data.empty:
        raise ValueError("No prediction rows available for diagnostics")

    model_kind = _first_non_null(data, "model_kind", "model")
    feature_selection_mode = _first_non_null(data, "feature_selection_mode", "unknown_selector")
    provenance = _prediction_provenance_label(data["prediction_provenance"])
    plot_title = title or (
        "Stage 4 prediction diagnostics: "
        f"{model_kind} + {feature_selection_mode} ({provenance})"
    )
    split_colors = {
        "train": "#4C78A8",
        "valid": "#F58518",
        "test": "#54A24B",
        "pre_test": "#B279A2",
        "dev": "#4C78A8",
        "dev_train": "#4C78A8",
        "dev_valid": "#F58518",
        "dev_test": "#54A24B",
    }
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    ax_actual, ax_resid_pred, ax_resid_time, ax_hist = axes.ravel()

    for split_name in splits:
        split_data = data.loc[data["split"].eq(split_name)]
        if split_data.empty:
            continue
        color = split_colors.get(split_name, "#666666")
        ax_actual.scatter(
            split_data[target_col],
            split_data["prediction"],
            s=28,
            alpha=0.75,
            color=color,
            label=split_name,
        )
        ax_resid_pred.scatter(
            split_data["prediction"],
            split_data["residual"],
            s=28,
            alpha=0.75,
            color=color,
            label=split_name,
        )
        ax_resid_time.scatter(
            split_data["calendarDate"],
            split_data["residual"],
            s=28,
            alpha=0.75,
            color=color,
            label=split_name,
        )
        ax_hist.hist(
            split_data["residual"],
            bins=14,
            density=normalize_histogram,
            alpha=0.45,
            color=color,
            label=split_name,
        )

    observed_min = float(np.nanmin([data[target_col].min(), data["prediction"].min()]))
    observed_max = float(np.nanmax([data[target_col].max(), data["prediction"].max()]))
    padding = max(1.0, 0.03 * (observed_max - observed_min))
    lims = (observed_min - padding, observed_max + padding)
    ax_actual.plot(lims, lims, color="#333333", linewidth=1.2, linestyle="--", label="identity")
    ax_actual.set_xlim(lims)
    ax_actual.set_ylim(lims)
    ax_actual.set_xlabel("Actual")
    ax_actual.set_ylabel("Predicted")
    ax_actual.set_title("Actual vs Predicted")

    ax_resid_pred.axhline(0.0, color="#333333", linewidth=1.1, linestyle="--")
    ax_resid_pred.set_xlabel("Predicted")
    ax_resid_pred.set_ylabel("Residual")
    ax_resid_pred.set_title("Residual vs Prediction")

    ax_resid_time.axhline(0.0, color="#333333", linewidth=1.1, linestyle="--")
    ax_resid_time.set_xlabel("Date")
    ax_resid_time.set_ylabel("Residual")
    ax_resid_time.set_title("Residual Over Time")

    ax_hist.axvline(0.0, color="#333333", linewidth=1.1, linestyle="--")
    ax_hist.set_xlabel("Residual")
    ax_hist.set_ylabel("Density" if normalize_histogram else "Rows")
    ax_hist.set_title("Normalized Residual Distribution" if normalize_histogram else "Residual Distribution")

    for ax in axes.ravel():
        ax.grid(True, color="#E6E6E6", linewidth=0.8)
    ax_actual.legend(loc="best", frameon=False)
    ax_resid_time.legend(loc="best", frameon=False)
    fig.suptitle(plot_title, fontsize=13)
    fig.autofmt_xdate()

    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=160, bbox_inches="tight")
    return fig


def plot_stage4_linear_finalist_metric_comparison(
    final_metrics: pd.DataFrame,
    dummy_metrics: pd.DataFrame,
    *,
    baseline_strategy: str = "dummy_median",
) -> Any:
    """Plot post-refit dev/test metrics for validation-selected finalists."""
    import matplotlib.pyplot as plt

    required = {"model_kind", "split", "mae", "rmse", "r2", "validation_selection_rank"}
    missing = sorted(required - set(final_metrics.columns))
    if missing:
        raise KeyError(f"final_metrics missing required columns: {missing}")
    selected = (
        final_metrics.loc[final_metrics["split"].isin(["dev", "test"])]
        .sort_values("validation_selection_rank")
        .drop_duplicates(["model_kind", "split"], keep="first")
        .copy()
    )
    dummy = dummy_metrics.loc[dummy_metrics["split"].isin(["dev", "test"])].copy()
    if not dummy.empty:
        if baseline_strategy not in set(dummy["model_kind"]):
            raise KeyError(f"Unknown baseline_strategy: {baseline_strategy}")
        selected = pd.concat(
            [dummy.loc[dummy["model_kind"].eq(baseline_strategy)], selected],
            ignore_index=True,
            sort=False,
        )
    if selected.empty:
        raise ValueError("No finalist metrics available for comparison")

    model_order = selected.loc[selected["split"].eq("dev"), "model_kind"].drop_duplicates().tolist()
    split_colors = {"dev": "#3C6E71", "test": "#B54F59"}
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.8), constrained_layout=True)
    x_positions = np.arange(len(model_order))
    bar_width = 0.36
    for ax, metric, title in [
        (axes[0], "mae", "MAE (lower is better)"),
        (axes[1], "rmse", "RMSE (lower is better)"),
        (axes[2], "r2", "R2 (higher is better)"),
    ]:
        for split_idx, split_name in enumerate(["dev", "test"]):
            values = (
                selected.loc[selected["split"].eq(split_name)]
                .set_index("model_kind")
                .reindex(model_order)[metric]
                .to_numpy(dtype=float)
            )
            ax.bar(
                x_positions + (split_idx - 0.5) * bar_width,
                values,
                width=bar_width,
                color=split_colors[split_name],
                label=split_name,
            )
        ax.set_xticks(x_positions, labels=model_order, rotation=25, ha="right")
        ax.set_title(title)
        ax.grid(True, axis="y", color="#E6E6E6")
        if metric == "r2":
            ax.axhline(0.0, color="#333333", linewidth=1.0)
    axes[1].legend(frameon=False, loc="upper center", ncols=2)
    axes[0].set_ylabel("Metric value")
    fig.suptitle(
        f"Post-Refit Dev/Test Diagnostic vs Preselected {baseline_strategy} "
        "(future test is evaluation only)"
    )
    return fig


def plot_stage4_linear_mixed_validation_family_comparison(
    tuning_summary: pd.DataFrame,
    dummy_tuning_summary: pd.DataFrame,
    *,
    baseline_strategy: str = "dummy_median",
) -> Any:
    """Compare validation-selected model-family representatives across mixed holdouts."""
    import matplotlib.pyplot as plt

    required = {
        "model_kind",
        "selection_rank",
        "random_mean_train_mae",
        "random_mean_valid_mae",
        "temporal_mean_train_mae",
        "temporal_mean_valid_mae",
    }
    missing = sorted(required - set(tuning_summary.columns))
    if missing:
        raise KeyError(f"tuning_summary missing mixed-validation columns: {missing}")
    selected = (
        tuning_summary.sort_values("selection_rank")
        .drop_duplicates("model_kind", keep="first")
        .copy()
    )
    baseline = dummy_tuning_summary.loc[dummy_tuning_summary["model_kind"].eq(baseline_strategy)].copy()
    if baseline.empty:
        raise KeyError(f"Unknown baseline_strategy: {baseline_strategy}")
    baseline_row = baseline.iloc[0].to_dict()
    selected = pd.concat([pd.DataFrame([baseline_row]), selected], ignore_index=True, sort=False)

    model_order = selected["model_kind"].astype(str).tolist()
    x_positions = np.arange(len(model_order))
    bar_width = 0.36
    colors = {"train": "#A3BEFA", "valid": "#F0986E"}
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.8), constrained_layout=True)
    for ax, holdout_type, title in [
        (axes[0], "temporal", "Temporal Holdouts"),
        (axes[1], "random", "Random Holdouts"),
    ]:
        for split_idx, split_name in enumerate(["train", "valid"]):
            column = f"{holdout_type}_mean_{split_name}_mae"
            ax.bar(
                x_positions + (split_idx - 0.5) * bar_width,
                pd.to_numeric(selected[column], errors="coerce"),
                width=bar_width,
                color=colors[split_name],
                edgecolor="#464C55",
                linewidth=0.7,
                label=split_name,
            )
        ax.set_xticks(x_positions, labels=model_order, rotation=25, ha="right")
        ax.set_title(title)
        ax.set_ylabel("Mean MAE across holdouts")
        ax.grid(True, axis="y", color="#E6E6E6")
    axes[1].legend(frameon=False, loc="upper center", ncols=2)
    fig.suptitle(
        f"Rerank-Selected Model-Family Representatives vs Preselected {baseline_strategy}"
    )
    return fig


def plot_stage4_linear_validation_diagnostics(
    tuning_summary: pd.DataFrame,
    dummy_tuning_summary: pd.DataFrame,
    *,
    top_n: int = 25,
    top_per_model_family: int = 5,
    baseline_strategy: str = "dummy_median",
) -> dict[str, Any]:
    """Build temporal-first validation diagnostics with targeted random-holdout context."""
    import matplotlib.pyplot as plt

    data = enrich_stage4_linear_validation_summary(tuning_summary)
    mixed = {
        "temporal_mean_train_mae",
        "temporal_mean_valid_mae",
        "temporal_std_valid_mae",
        "random_mean_train_mae",
        "random_mean_valid_mae",
        "random_std_valid_mae",
    } <= set(data.columns)
    primary_metric = "temporal_mean_valid_mae" if mixed else "mean_valid_mae"
    primary_std = "temporal_std_valid_mae" if mixed else "std_valid_mae"
    primary_train = "temporal_mean_train_mae" if mixed else "mean_train_mae"
    primary_label = "temporal mean validation MAE" if mixed else "mean validation MAE"
    data = data.loc[np.isfinite(pd.to_numeric(data[primary_metric], errors="coerce"))].copy()
    if data.empty:
        raise ValueError("No finite validation MAE rows available for diagnostics")
    figures: dict[str, Any] = {}
    family_colors = _model_family_colors(data["model_kind"].unique())
    selected_dummy = dummy_tuning_summary.loc[
        dummy_tuning_summary["model_kind"].astype(str).eq(baseline_strategy)
    ]

    def dummy_metric(column: str) -> float:
        if selected_dummy.empty or column not in selected_dummy.columns:
            return np.nan
        value = pd.to_numeric(selected_dummy[column], errors="coerce").iloc[0]
        return float(value) if pd.notna(value) else np.nan

    distribution_specs = (
        [
            ("temporal_mean_valid_mae", "Temporal holdouts", "#F0986E"),
            ("random_mean_valid_mae", "Random holdouts", "#A3BEFA"),
        ]
        if mixed
        else [("mean_valid_mae", "Repeated holdouts", "#A3BEFA")]
    )
    fig, axes = plt.subplots(
        len(distribution_specs),
        1,
        figsize=(9, 4.2 * len(distribution_specs)),
        constrained_layout=True,
        squeeze=False,
    )
    for ax, (metric_col, title, color) in zip(axes.ravel(), distribution_specs):
        values = pd.to_numeric(data[metric_col], errors="coerce").dropna().to_numpy(dtype=float)
        bins = min(30, max(8, int(np.sqrt(len(values)))))
        ax.hist(values, bins=bins, color=color, edgecolor="#464C55", linewidth=0.6, alpha=0.78)
        ax.axvline(values.min(), color="#386411", linewidth=1.6, label=f"best candidate {values.min():.3f}")
        ax.axvline(np.median(values), color="#8A3A6F", linewidth=1.6, label=f"candidate median {np.median(values):.3f}")
        baseline = dummy_metric(metric_col)
        if np.isfinite(baseline):
            ax.axvline(baseline, color="#464C55", linewidth=1.5, linestyle="--", label=f"{baseline_strategy} {baseline:.3f}")
        ax.set_title(title)
        ax.set_xlabel("Mean validation MAE")
        ax.set_ylabel("Candidates")
        ax.legend(frameon=False)
        ax.grid(True, axis="y", color="#E6E6E6")
    fig.suptitle("Validation MAE Distribution Across Candidates")
    figures["validation_mae_distribution"] = fig

    top = data.nsmallest(min(top_n, len(data)), primary_metric).copy()
    fig_height = max(6.5, 0.34 * len(top) + 2.0)
    fig, ax = plt.subplots(figsize=(12, fig_height), constrained_layout=True)
    colors = [family_colors[value] for value in top["model_kind"]]
    ax.barh(
        top["candidate_short_label"],
        top[primary_metric],
        xerr=top.get(primary_std),
        color=colors,
        alpha=0.85,
        error_kw={"ecolor": "#333333", "elinewidth": 1, "capsize": 2},
    )
    ax.invert_yaxis()
    ax.set_title(f"Top {len(top)} Candidates By {primary_label.title()}")
    ax.set_xlabel(primary_label)
    ax.set_ylabel("")
    primary_dummy = dummy_metric(primary_metric)
    if np.isfinite(primary_dummy):
        ax.axvline(
            primary_dummy,
            color="#464C55",
            linewidth=1.5,
            linestyle="--",
            label=f"{baseline_strategy} {primary_dummy:.3f}",
        )
        ax.legend(frameon=False)
    ax.grid(True, axis="x", color="#E6E6E6")
    figures["top_candidates"] = fig

    family_order = (
        data.groupby("model_kind")[primary_metric].min().sort_values().index.tolist()
    )
    family_top_parts = [
        data.loc[data["model_kind"].eq(model_kind)]
        .nsmallest(max(1, int(top_per_model_family)), primary_metric)
        .copy()
        for model_kind in family_order
    ]
    family_top = pd.concat(family_top_parts, ignore_index=True)
    fig_height = max(7.0, 0.30 * len(family_top) + 2.0)
    family_specs = (
        [
            ("temporal_mean_valid_mae", "temporal_std_valid_mae", "Temporal mean validation MAE"),
            ("random_mean_valid_mae", "random_std_valid_mae", "Random mean validation MAE"),
        ]
        if mixed
        else [("mean_valid_mae", "std_valid_mae", "Mean validation MAE")]
    )
    fig, axes = plt.subplots(
        1,
        len(family_specs),
        figsize=(8.5 + 6.0 * (len(family_specs) - 1), fig_height),
        constrained_layout=True,
        squeeze=False,
        sharey=True,
    )
    family_axes = axes.ravel()
    family_sizes = family_top.groupby("model_kind", sort=False).size().to_numpy(dtype=int)
    for axis_idx, (ax, (metric_col, std_col, title)) in enumerate(zip(family_axes, family_specs)):
        ax.barh(
            family_top["candidate_short_label"],
            family_top[metric_col],
            xerr=family_top.get(std_col),
            color=[family_colors[value] for value in family_top["model_kind"]],
            alpha=0.85,
            error_kw={"ecolor": "#464C55", "elinewidth": 1.0, "capsize": 2},
        )
        for boundary in np.cumsum(family_sizes)[:-1] - 0.5:
            ax.axhline(boundary, color="#C9CDD3", linewidth=1.0)
        ax.set_title(title)
        ax.set_xlabel("MAE")
        ax.grid(True, axis="x", color="#E6E6E6")
        if axis_idx > 0:
            ax.tick_params(axis="y", labelleft=False)
            ax.set_ylabel("")
    family_axes[0].invert_yaxis()
    fig.suptitle(f"Top {max(1, int(top_per_model_family))} Temporal-Ranked Candidates Per Model Family")
    figures["top_candidates_by_model_family"] = fig

    best_by_family = (
        data.sort_values(primary_metric)
        .drop_duplicates("model_kind")
        .sort_values(primary_metric)
        .copy()
    )
    if not selected_dummy.empty:
        best_by_family = pd.concat([selected_dummy, best_by_family], ignore_index=True, sort=False)
    comparison_specs = (
        [
            ("temporal", "Temporal holdouts"),
            ("random", "Random holdouts"),
        ]
        if mixed
        else [("", "Repeated holdouts")]
    )
    fig, axes = plt.subplots(1, len(comparison_specs), figsize=(8.5 * len(comparison_specs), 5.8), constrained_layout=True, squeeze=False)
    x_positions = np.arange(len(best_by_family))
    bar_width = 0.36
    for ax, (prefix, title) in zip(axes.ravel(), comparison_specs):
        train_col = f"{prefix}_mean_train_mae" if prefix else "mean_train_mae"
        valid_col = f"{prefix}_mean_valid_mae" if prefix else "mean_valid_mae"
        ax.bar(
            x_positions - bar_width / 2,
            best_by_family[train_col],
            width=bar_width,
            label="train",
            color="#A3BEFA",
            edgecolor="#464C55",
            linewidth=0.7,
        )
        ax.bar(
            x_positions + bar_width / 2,
            best_by_family[valid_col],
            width=bar_width,
            label="valid",
            color="#F0986E",
            edgecolor="#464C55",
            linewidth=0.7,
        )
        ax.set_xticks(x_positions, labels=best_by_family["model_kind"], rotation=25, ha="right")
        ax.set_title(title)
        ax.set_ylabel("Mean MAE")
        ax.grid(True, axis="y", color="#E6E6E6")
    axes.ravel()[-1].legend(frameon=False, loc="upper center", ncols=2)
    fig.suptitle(f"Temporal-Ranked Best Candidate Per Model Family vs {baseline_strategy}")
    figures["best_by_model_family"] = fig

    fig, ax = plt.subplots(figsize=(12, 5.8), constrained_layout=True)
    positions = np.arange(len(family_order), dtype=float)
    if mixed:
        temporal_values = [data.loc[data["model_kind"].eq(model_kind), "temporal_mean_valid_mae"].to_numpy(dtype=float) for model_kind in family_order]
        random_values = [data.loc[data["model_kind"].eq(model_kind), "random_mean_valid_mae"].to_numpy(dtype=float) for model_kind in family_order]
        temporal_box = ax.boxplot(temporal_values, positions=positions - 0.18, widths=0.30, patch_artist=True, showfliers=False)
        random_box = ax.boxplot(random_values, positions=positions + 0.18, widths=0.30, patch_artist=True, showfliers=False)
        for patch in temporal_box["boxes"]:
            patch.set_facecolor("#F0986E")
        for patch in random_box["boxes"]:
            patch.set_facecolor("#A3BEFA")
        ax.plot([], [], color="#F0986E", linewidth=8, label="temporal")
        ax.plot([], [], color="#A3BEFA", linewidth=8, label="random")
        ax.legend(frameon=False)
    else:
        family_values = [data.loc[data["model_kind"].eq(model_kind), "mean_valid_mae"].to_numpy(dtype=float) for model_kind in family_order]
        box = ax.boxplot(family_values, positions=positions, widths=0.55, patch_artist=True, showfliers=True)
        for patch, model_kind in zip(box["boxes"], family_order):
            patch.set_facecolor(family_colors[model_kind])
    ax.set_xticks(positions, labels=family_order)
    ax.set_title("Validation MAE Distribution By Model Family And Holdout Type")
    ax.set_xlabel("Model family")
    ax.set_ylabel("Mean validation MAE across holdouts")
    ax.grid(True, axis="y", color="#E6E6E6")
    figures["model_family_distribution"] = fig

    fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
    for model_kind, family_data in data.groupby("model_kind"):
        ax.scatter(
            family_data[primary_train],
            family_data[primary_metric],
            alpha=0.65,
            s=32,
            label=model_kind,
            color=family_colors[model_kind],
        )
    low = float(np.nanmin([data[primary_train].min(), data[primary_metric].min()]))
    high = float(np.nanmax([data[primary_train].max(), data[primary_metric].max()]))
    ax.plot([low, high], [low, high], linestyle="--", color="#333333", linewidth=1.2)
    ax.set_title("Temporal Train vs Validation MAE" if mixed else "Train vs Validation MAE")
    ax.set_xlabel("Temporal mean train MAE" if mixed else "Mean train MAE")
    ax.set_ylabel(primary_label)
    ax.legend(frameon=False, ncols=2)
    ax.grid(True, color="#E6E6E6")
    figures["train_validation_gap"] = fig

    stability_specs = (
        [
            ("temporal_mean_valid_mae", "temporal_std_valid_mae", "Temporal holdout stability"),
            ("random_mean_valid_mae", "random_std_valid_mae", "Random holdout stability"),
        ]
        if mixed
        else [("mean_valid_mae", "std_valid_mae", "Repeated-holdout stability")]
    )
    fig, axes = plt.subplots(1, len(stability_specs), figsize=(8.5 * len(stability_specs), 5.5), constrained_layout=True, squeeze=False)
    for ax, (mean_col, std_col, title) in zip(axes.ravel(), stability_specs):
        for model_kind, family_data in data.groupby("model_kind"):
            ax.scatter(family_data[mean_col], family_data[std_col], alpha=0.65, s=32, label=model_kind, color=family_colors[model_kind])
        ax.set_title(title)
        ax.set_xlabel("Mean validation MAE")
        ax.set_ylabel("Validation MAE standard deviation")
        ax.grid(True, color="#E6E6E6")
    axes.ravel()[-1].legend(frameon=False, ncols=2)
    figures["performance_stability"] = fig

    if mixed:
        fig, ax = plt.subplots(figsize=(9, 5.8), constrained_layout=True)
        for model_kind, family_data in data.groupby("model_kind"):
            ax.scatter(
                family_data["random_mean_valid_mae"],
                family_data["temporal_mean_valid_mae"],
                alpha=0.65,
                s=32,
                label=model_kind,
                color=family_colors[model_kind],
            )
        low = float(np.nanmin([data["random_mean_valid_mae"].min(), data["temporal_mean_valid_mae"].min()]))
        high = float(np.nanmax([data["random_mean_valid_mae"].max(), data["temporal_mean_valid_mae"].max()]))
        ax.plot([low, high], [low, high], linestyle="--", color="#333333", linewidth=1.2)
        ax.set_title("Random vs Temporal Validation MAE")
        ax.set_xlabel("Random mean validation MAE")
        ax.set_ylabel("Temporal mean validation MAE")
        ax.legend(frameon=False, ncols=2)
        ax.grid(True, color="#E6E6E6")
        figures["random_vs_temporal"] = fig

    if (
        "mean_selected_feature_count" in data.columns
        and pd.to_numeric(data["mean_selected_feature_count"], errors="coerce").nunique() > 1
    ):
        fig, ax = plt.subplots(figsize=(9, 5.5), constrained_layout=True)
        for model_kind, family_data in data.groupby("model_kind"):
            ax.scatter(
                family_data["mean_selected_feature_count"],
                family_data[primary_metric],
                alpha=0.65,
                s=34,
                label=model_kind,
                color=family_colors[model_kind],
            )
        ax.set_title(f"{primary_label.title()} vs Selected Feature Count")
        ax.set_xlabel("Mean selected feature count")
        ax.set_ylabel(primary_label)
        ax.legend(frameon=False, ncols=2)
        ax.grid(True, color="#E6E6E6")
        figures["feature_count_tradeoff"] = fig

    return figures


def plot_stage4_linear_hyperparameter_diagnostics(
    tuning_summary: pd.DataFrame,
    dummy_tuning_summary: pd.DataFrame | None = None,
    *,
    baseline_strategy: str = "dummy_median",
) -> dict[str, Any]:
    """Plot temporal-first hyperparameter curves and temporal heatmaps."""
    import matplotlib.pyplot as plt

    data = enrich_stage4_linear_validation_summary(tuning_summary)
    mixed = {"temporal_mean_valid_mae", "random_mean_valid_mae"} <= set(data.columns)
    primary_metric = "temporal_mean_valid_mae" if mixed else "mean_valid_mae"
    data = data.loc[np.isfinite(data[primary_metric])].copy()
    figures: dict[str, Any] = {}
    selected_dummy = (
        dummy_tuning_summary.loc[dummy_tuning_summary["model_kind"].astype(str).eq(baseline_strategy)]
        if dummy_tuning_summary is not None and not dummy_tuning_summary.empty
        else pd.DataFrame()
    )
    parameter_curves = [
        ("ridge", "alpha"),
        ("lasso", "alpha"),
        ("pls", "n_components"),
        ("elastic_net", "alpha"),
        ("elastic_net", "l1_ratio"),
        ("huber", "alpha"),
        ("huber", "epsilon"),
    ]
    for model_kind, parameter in parameter_curves:
        model_data = data.loc[data["model_kind"].eq(model_kind)].dropna(subset=[parameter])
        if model_data.empty:
            continue
        fig, ax = plt.subplots(figsize=(8.5, 5), constrained_layout=True)
        metric_specs = (
            [
                ("temporal_mean_valid_mae", "temporal", "-"),
                ("random_mean_valid_mae", "random", "--"),
            ]
            if mixed
            else [("mean_valid_mae", "repeated holdouts", "-")]
        )
        for metric_col, holdout_label, linestyle in metric_specs:
            grouped = model_data.groupby(parameter)[metric_col].agg(best="min", median="median").reset_index()
            ax.plot(
                grouped[parameter],
                grouped["median"],
                marker="o",
                color="#5477C4",
                linestyle=linestyle,
                label=f"{holdout_label} median",
            )
            ax.plot(
                grouped[parameter],
                grouped["best"],
                marker="o",
                color="#CC6F47",
                linestyle=linestyle,
                label=f"{holdout_label} best",
            )
            if not selected_dummy.empty and metric_col in selected_dummy.columns:
                baseline = float(selected_dummy.iloc[0][metric_col])
                ax.axhline(
                    baseline,
                    color="#464C55",
                    linestyle=linestyle,
                    linewidth=1.0,
                    alpha=0.65,
                    label=f"{baseline_strategy} {holdout_label}",
                )
        if parameter == "alpha" and bool((grouped[parameter] > 0).all()):
            ax.set_xscale("log")
        ax.set_title(
            f"{model_kind.replace('_', ' ').title()} {parameter} Validation Curves"
        )
        ax.set_xlabel(parameter)
        ax.set_ylabel("Mean validation MAE")
        ax.legend(frameon=False)
        ax.grid(True, color="#E6E6E6")
        figure_key = (
            model_kind
            if model_kind in {"ridge", "lasso", "pls"}
            else f"{model_kind}_{parameter}"
        )
        figures[figure_key] = fig

    for model_kind, x_col, y_col in [
        ("elastic_net", "alpha", "l1_ratio"),
        ("huber", "alpha", "epsilon"),
    ]:
        model_data = data.loc[data["model_kind"].eq(model_kind)].dropna(subset=[x_col, y_col])
        if model_data.empty:
            continue
        pivot = model_data.pivot_table(
            index=y_col,
            columns=x_col,
            values=primary_metric,
            aggfunc="min",
        ).sort_index().sort_index(axis=1)
        fig_width = min(10.0, max(6.5, 0.62 * len(pivot.columns) + 3.0))
        fig_height = min(7.0, max(4.5, 0.42 * len(pivot.index) + 2.5))
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
        image = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap="viridis_r")
        ax.set_xticks(np.arange(len(pivot.columns)), labels=[_compact_number(value) for value in pivot.columns])
        ax.set_yticks(np.arange(len(pivot.index)), labels=[_compact_number(value) for value in pivot.index])
        ax.tick_params(axis="x", labelrotation=35)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        metric_title = "Temporal Mean Validation MAE" if mixed else "Mean Validation MAE"
        ax.set_title(f"{model_kind.replace('_', ' ').title()} Best {metric_title} Heatmap")
        annotation_font_size = 7 if max(pivot.shape) >= 8 else 8
        for row_idx in range(len(pivot.index)):
            for col_idx in range(len(pivot.columns)):
                value = pivot.iloc[row_idx, col_idx]
                if np.isfinite(value):
                    text_color = "#FFFFFF" if image.norm(value) > 0.62 else "#1F2430"
                    ax.text(
                        col_idx,
                        row_idx,
                        f"{value:.2f}",
                        ha="center",
                        va="center",
                        fontsize=annotation_font_size,
                        color=text_color,
                    )
        fig.colorbar(image, ax=ax, label=f"Best {metric_title.lower()}")
        figures[model_kind] = fig
    return figures


def plot_stage4_linear_factor_comparisons(
    tuning_summary: pd.DataFrame,
) -> dict[str, Any]:
    """Plot paired temporal-validation-MAE effects for optional grid dimensions."""
    import matplotlib.pyplot as plt

    data = enrich_stage4_linear_validation_summary(tuning_summary)
    primary_metric = (
        "temporal_mean_valid_mae"
        if "temporal_mean_valid_mae" in data.columns
        else "mean_valid_mae"
    )
    metric_label = (
        "temporal mean validation MAE"
        if primary_metric == "temporal_mean_valid_mae"
        else "mean validation MAE"
    )
    title_scope = "Temporal " if primary_metric == "temporal_mean_valid_mae" else ""
    data = data.loc[np.isfinite(data[primary_metric])].copy()
    figures: dict[str, Any] = {}

    if {"none", "linear"} <= set(data["calibration"].astype(str)):
        deltas = build_stage4_linear_paired_deltas(
            data,
            factor="calibration",
            reference="none",
            metric_col=primary_metric,
        )
        if not deltas.empty:
            fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), constrained_layout=True)
            axes[0].hist(deltas["delta_mean_valid_mae"], bins=min(24, max(6, int(np.sqrt(len(deltas))))), color="#6B8EAD", alpha=0.75)
            axes[0].axvline(0.0, color="#333333", linestyle="--", linewidth=1.2)
            axes[0].set_title(f"{title_scope}Linear Calibration Paired Delta")
            axes[0].set_xlabel(f"Delta {metric_label}: linear - none")
            axes[0].set_ylabel("Matched candidates")
            _boxplot_by_group(
                axes[1],
                deltas,
                group_col="model_kind",
                value_col="delta_mean_valid_mae",
                title=f"{title_scope}Calibration Delta By Model Family",
                group_label="Model family",
                value_label=f"Delta {metric_label}",
            )
            figures["calibration_comparison"] = fig

    if "none" in set(data["feature_selection_config_label"]) and data["feature_selection_config_label"].nunique() > 1:
        deltas = build_stage4_linear_paired_deltas(
            data,
            factor="feature_selection",
            reference="none",
            metric_col=primary_metric,
        )
        if not deltas.empty:
            selector_count = max(
                int(data["feature_selection_config_label"].nunique()),
                int(deltas["factor_value"].nunique()),
            )
            fig, ax = plt.subplots(
                figsize=(12, max(6.0, 0.48 * selector_count + 2.5)),
                constrained_layout=True,
            )
            _boxplot_by_group(
                ax,
                data,
                group_col="feature_selection_config_label",
                value_col=primary_metric,
                title=f"{metric_label.title()} By Feature Selector",
                group_label="Feature selector",
                value_label=metric_label,
                zero_reference=False,
                group_color_map=_feature_selector_color_map(
                    data["feature_selection_config_label"].unique()
                ),
                group_family_map=_feature_selector_family_map(
                    data["feature_selection_config_label"].unique()
                ),
                legend_title="Selector family",
            )
            figures["feature_selection_distribution"] = fig

            fig, ax = plt.subplots(
                figsize=(12, max(6.0, 0.48 * selector_count + 2.5)),
                constrained_layout=True,
            )
            _boxplot_by_group(
                ax,
                deltas,
                group_col="factor_value",
                value_col="delta_mean_valid_mae",
                title=f"{title_scope}Feature Selector Paired Delta vs none",
                group_label="Feature selector",
                value_label=f"Delta {metric_label}",
                group_color_map=_feature_selector_color_map(
                    deltas["factor_value"].unique()
                ),
                group_family_map=_feature_selector_family_map(
                    deltas["factor_value"].unique()
                ),
                legend_title="Selector family",
            )
            figures["feature_selection_paired_delta"] = fig

    if "none" in set(data["robust_clip"].astype(str)) and data["robust_clip"].astype(str).nunique() > 1:
        deltas = build_stage4_linear_paired_deltas(
            data,
            factor="robust_clip",
            reference="none",
            metric_col=primary_metric,
        )
        if not deltas.empty:
            deltas = deltas.copy()
            deltas["family_and_clip"] = deltas["model_kind"].astype(str) + " | " + deltas["factor_value"].astype(str)
            family_clip_count = int(deltas["family_and_clip"].nunique())
            fig, axes = plt.subplots(
                1,
                2,
                figsize=(17, max(6.0, 0.42 * family_clip_count + 2.5)),
                constrained_layout=True,
            )
            clip_values = (
                deltas.groupby("factor_value")["delta_mean_valid_mae"]
                .median()
                .sort_values()
                .index.tolist()
            )
            all_delta_values = pd.to_numeric(
                deltas["delta_mean_valid_mae"],
                errors="coerce",
            ).dropna().to_numpy(dtype=float)
            bin_count = min(24, max(6, int(np.sqrt(len(all_delta_values)))))
            shared_bins = np.histogram_bin_edges(all_delta_values, bins=bin_count)
            clip_colors = _model_family_colors(clip_values)
            for clip_value in clip_values:
                values = pd.to_numeric(
                    deltas.loc[deltas["factor_value"].eq(clip_value), "delta_mean_valid_mae"],
                    errors="coerce",
                ).dropna().to_numpy(dtype=float)
                axes[0].hist(
                    values,
                    bins=shared_bins,
                    density=True,
                    alpha=0.35,
                    color=clip_colors[str(clip_value)],
                    edgecolor=clip_colors[str(clip_value)],
                    linewidth=1.1,
                    label=f"{clip_value} (n={len(values)})",
                )
                axes[0].axvline(
                    np.median(values),
                    color=clip_colors[str(clip_value)],
                    linewidth=1.4,
                    linestyle=":",
                )
            axes[0].axvline(0.0, color="#333333", linestyle="--", linewidth=1.2)
            axes[0].set_title(f"{title_scope}Robust Clipping Paired Delta Distributions")
            axes[0].set_xlabel(f"Delta {metric_label} vs none")
            axes[0].set_ylabel("Density")
            axes[0].legend(frameon=False)
            axes[0].grid(True, axis="y", color="#E6E6E6")
            _boxplot_by_group(
                axes[1],
                deltas,
                group_col="family_and_clip",
                value_col="delta_mean_valid_mae",
                title=f"{title_scope}Robust Clipping Delta By Model Family",
                group_label="Model family and clipping",
                value_label=f"Delta {metric_label}",
            )
            figures["robust_clipping_comparison"] = fig

    for factor, reference, title in [
        ("target_transform", "none", f"{title_scope}Target Transform Paired Delta vs none"),
        ("prediction_clip", "none", f"{title_scope}Prediction Clipping Paired Delta vs none"),
    ]:
        values = set(data[factor].astype(str))
        if reference not in values or len(values) <= 1:
            continue
        deltas = build_stage4_linear_paired_deltas(
            data,
            factor=factor,
            reference=reference,
            metric_col=primary_metric,
        )
        if deltas.empty:
            continue
        fig, axes = plt.subplots(1, 2, figsize=(15, 5.2), constrained_layout=True)
        _boxplot_by_group(
            axes[0],
            deltas,
            group_col="factor_value",
            value_col="delta_mean_valid_mae",
            title=title,
            group_label=factor,
            value_label=f"Delta {metric_label}",
        )
        _boxplot_by_group(
            axes[1],
            deltas,
            group_col="model_kind",
            value_col="delta_mean_valid_mae",
            title=f"{title} By Model Family",
            group_label="Model family",
            value_label=f"Delta {metric_label}",
        )
        figures[f"{factor}_comparison"] = fig
    return figures


def train_feature_scores(
    train_df: pd.DataFrame,
    feature_columns: Sequence[str],
    *,
    config: Stage4LinearConfig,
) -> pd.DataFrame:
    y = pd.to_numeric(train_df[config.target_col], errors="coerce")
    numeric_cols, categorical_cols = _feature_blocks(train_df, feature_columns)
    rows: list[dict[str, object]] = []
    for feature in feature_columns:
        if feature in numeric_cols:
            x = pd.to_numeric(train_df[feature], errors="coerce").replace([np.inf, -np.inf], np.nan)
            pearson = _safe_corr_pair(x, y, method="pearson")
            spearman = _safe_corr_pair(x, y, method="spearman")
            rows.append(
                {
                    "feature": feature,
                    "feature_type": "numeric",
                    "train_non_null": int(x.notna().sum()),
                    "train_missing_pct": float(x.isna().mean() * 100.0),
                    "train_nunique": int(x.nunique(dropna=True)),
                    "pearson_train": pearson,
                    "spearman_train": spearman,
                    "abs_pearson_train": abs(pearson) if np.isfinite(pearson) else np.nan,
                    "abs_spearman_train": abs(spearman) if np.isfinite(spearman) else np.nan,
                }
            )
        elif feature in categorical_cols:
            values = train_df[feature]
            rows.append(
                {
                    "feature": feature,
                    "feature_type": "categorical",
                    "train_non_null": int(values.notna().sum()),
                    "train_missing_pct": float(values.isna().mean() * 100.0),
                    "train_nunique": int(values.nunique(dropna=True)),
                    "pearson_train": np.nan,
                    "spearman_train": np.nan,
                    "abs_pearson_train": np.nan,
                    "abs_spearman_train": np.nan,
                }
            )
    scores = pd.DataFrame(rows)
    scores["mutual_info_train"] = 0.0
    if numeric_cols:
        X_mi = _numeric_imputed_frame(train_df, numeric_cols)
        valid = y.notna()
        usable_cols = [
            column
            for column in X_mi.columns
            if X_mi.loc[valid, column].nunique(dropna=True) > 1
        ]
        if len(usable_cols) > 0 and int(valid.sum()) >= 5:
            neighbors = min(max(1, int(config.mutual_info_neighbors)), max(1, int(valid.sum()) - 1))
            mi = mutual_info_regression(
                X_mi.loc[valid, usable_cols],
                y.loc[valid].to_numpy(dtype=float),
                n_neighbors=neighbors,
                random_state=config.random_state,
            )
            mi_lookup = dict(zip(usable_cols, mi))
            scores["mutual_info_train"] = scores["feature"].map(mi_lookup).fillna(0.0)
    scores["selection_score"] = scores["abs_spearman_train"].fillna(0.0)
    scores["spearman_rank"] = scores["selection_score"].rank(ascending=False, method="first")
    scores["mutual_info_rank"] = scores["mutual_info_train"].rank(ascending=False, method="first")
    return scores


def select_stage4_features(
    train_df: pd.DataFrame,
    feature_columns: Sequence[str],
    selection: Stage4FeatureSelectionConfig,
    *,
    scores: pd.DataFrame | None = None,
    config: Stage4LinearConfig,
) -> tuple[list[str], pd.DataFrame]:
    """Apply one feature selector using train rows only."""
    if selection.mode not in STAGE4_LINEAR_FEATURE_SELECTION_MODES:
        raise ValueError(f"Unknown feature-selection mode: {selection.mode}")
    scores = scores if scores is not None else train_feature_scores(train_df, feature_columns, config=config)
    candidate_cols = [column for column in feature_columns if column in train_df.columns]
    numeric_cols, categorical_cols = _feature_blocks(train_df, candidate_cols)
    categorical_keep = categorical_cols if config.keep_categorical_features else []
    numeric_scores = scores.loc[scores["feature"].isin(numeric_cols)].copy()
    ranked_fallback = (
        numeric_scores.sort_values(["selection_score", "feature"], ascending=[False, True])["feature"].tolist()
    )
    dropped_reasons: dict[str, str] = {}
    lasso_detail = pd.DataFrame(columns=["feature", "feature_selection_lasso_coef"])

    if selection.mode == "none":
        selected = candidate_cols
    elif selection.mode == "top_spearman":
        selected = _top_ranked_features(
            numeric_scores,
            score_col="selection_score",
            top_k=selection.top_k,
            min_score=selection.min_abs_spearman,
        )
    elif selection.mode == "top_mutual_info":
        selected = _top_ranked_features(
            numeric_scores,
            score_col="mutual_info_train",
            top_k=selection.top_k,
            min_score=selection.min_mutual_info,
        )
    elif selection.mode == "correlation_prune":
        selected, dropped_reasons = _correlation_pruned_features(
            train_df,
            numeric_cols,
            numeric_scores,
            threshold=selection.correlation_threshold,
        )
    elif selection.mode == "spearman_then_correlation":
        first_pass = _top_ranked_features(
            numeric_scores,
            score_col="selection_score",
            top_k=selection.top_k,
            min_score=selection.min_abs_spearman,
        )
        selected, dropped_reasons = _correlation_pruned_features(
            train_df,
            first_pass,
            numeric_scores,
            threshold=selection.correlation_threshold,
        )
    elif selection.mode == "lasso_nonzero":
        selected, lasso_detail = _lasso_nonzero_features(
            train_df,
            numeric_cols,
            config.target_col,
            alpha=selection.lasso_alpha,
            max_iter=selection.lasso_max_iter,
            tol=1e-4,
            random_state=config.random_state,
        )
    else:
        raise ValueError(selection.mode)

    if selection.mode != "none":
        selected = [*selected, *categorical_keep]
    min_features = min(selection.min_features, len(candidate_cols))
    selected = _ensure_minimum_features(selected, ranked_fallback, min_features)
    selected_set = set(selected)
    selected = [feature for feature in candidate_cols if feature in selected_set]
    if not selected:
        raise ValueError("Feature selection selected no features")

    detail = scores.merge(lasso_detail, on="feature", how="left")
    detail["selected"] = detail["feature"].isin(selected)
    selected_rank = {feature: idx + 1 for idx, feature in enumerate(selected)}
    detail["selected_rank"] = detail["feature"].map(selected_rank)
    detail["excluded_reason"] = np.where(
        detail["selected"],
        "",
        detail["feature"].map(dropped_reasons).fillna(f"excluded_by_{selection.mode}"),
    )
    detail = detail.sort_values(
        ["selected", "selected_rank", "selection_score", "mutual_info_train", "feature"],
        ascending=[False, True, False, False, True],
        na_position="last",
    ).reset_index(drop=True)
    return selected, detail


def make_stage4_linear_pipeline(
    train_df: pd.DataFrame,
    feature_columns: Sequence[str],
    candidate: Stage4LinearCandidate,
    *,
    config: Stage4LinearConfig,
) -> Pipeline:
    numeric_cols, categorical_cols = _feature_blocks(train_df, feature_columns)
    transformers: list[tuple[str, Pipeline, list[str]]] = []
    z_value = _parse_robust_clip(candidate.robust_clip)
    if numeric_cols:
        transformers.append(
            (
                "num",
                Pipeline(
                    steps=[
                        ("clip", RobustZClipper(z=z_value)),
                        ("imputer", SimpleImputer(strategy="median", add_indicator=config.missing_indicators)),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_cols,
            )
        )
    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_cols,
            )
        )
    if not transformers:
        raise ValueError("No usable features are available for preprocessing")
    return Pipeline(
        steps=[
            ("preprocess", ColumnTransformer(transformers=transformers, remainder="drop")),
            ("model", _make_estimator(candidate)),
        ]
    )


def fit_oof_calibration(
    train_df: pd.DataFrame,
    feature_columns: Sequence[str],
    candidate: Stage4LinearCandidate,
    *,
    config: Stage4LinearConfig,
) -> dict[str, object]:
    if candidate.calibration == "none":
        return _identity_calibration("none")
    if candidate.calibration != "linear":
        raise ValueError(f"Unsupported calibration mode: {candidate.calibration}")
    if len(train_df) < config.calibration_min_rows:
        return _identity_calibration("linear", reason="not_enough_train_rows")
    folds = min(max(2, int(config.calibration_cv_folds)), len(train_df))
    if len(train_df) // folds < 2:
        return _identity_calibration("linear", reason="folds_too_small")

    y = train_df[config.target_col].to_numpy(dtype=float)
    oof_pred = np.full(len(train_df), np.nan, dtype=float)
    kfold = KFold(n_splits=folds, shuffle=True, random_state=config.random_state)
    for fold_train_idx, fold_valid_idx in kfold.split(train_df):
        fold_train = train_df.iloc[fold_train_idx].reset_index(drop=True)
        fold_valid = train_df.iloc[fold_valid_idx].reset_index(drop=True)
        fold_scores = train_feature_scores(fold_train, feature_columns, config=config)
        fold_features, _ = select_stage4_features(
            fold_train,
            feature_columns,
            candidate.feature_selection,
            scores=fold_scores,
            config=config,
        )
        fold_pipeline = make_stage4_linear_pipeline(
            fold_train,
            fold_features,
            candidate,
            config=config,
        )
        _fit_estimator_suppressing_convergence_warnings(
            fold_pipeline,
            fold_train[fold_features],
            _transform_target(fold_train[config.target_col], candidate.target_transform),
        )
        fold_raw = np.ravel(fold_pipeline.predict(fold_valid[fold_features]))
        fold_pred = apply_prediction_clip(
            _inverse_transform_target(fold_raw, candidate.target_transform),
            candidate.prediction_clip,
        )
        oof_pred[fold_valid_idx] = fold_pred
    return fit_linear_calibration_from_predictions(oof_pred, y)


def fit_linear_calibration_from_predictions(prediction: Any, actual: Any) -> dict[str, object]:
    pred = np.asarray(prediction, dtype=float)
    y = np.asarray(actual, dtype=float)
    valid = np.isfinite(pred) & np.isfinite(y)
    if int(valid.sum()) < 5:
        return _identity_calibration("linear", reason="not_enough_oof_predictions")
    pred = pred[valid]
    y = y[valid]
    if float(np.nanstd(pred)) <= 1e-12:
        return _identity_calibration("linear", reason="constant_oof_predictions")
    slope, intercept = np.polyfit(pred, y, deg=1)
    return {
        "calibration": "linear",
        "calibration_fit_source": "oof",
        "calibration_applied": True,
        "calibration_intercept": float(intercept),
        "calibration_slope": float(slope),
        "calibration_skip_reason": "",
    }


def apply_calibration(prediction: Any, calibration_record: Mapping[str, object]) -> np.ndarray:
    pred = np.asarray(prediction, dtype=float)
    if bool(calibration_record.get("calibration_applied", False)):
        pred = float(calibration_record.get("calibration_intercept", 0.0)) + float(
            calibration_record.get("calibration_slope", 1.0)
        ) * pred
    return pred


def apply_prediction_clip(prediction: Any, mode: str) -> np.ndarray:
    pred = np.asarray(prediction, dtype=float)
    if mode == "none":
        return pred
    if mode == "0_100":
        return np.clip(pred, 0.0, 100.0)
    raise ValueError(f"Unsupported prediction_clip mode: {mode}")


def dummy_baseline_value(train_df: pd.DataFrame, strategy: str, *, target_col: str) -> float:
    y = pd.to_numeric(train_df[target_col], errors="coerce").dropna()
    if y.empty:
        raise ValueError("Cannot fit dummy baseline without training targets")
    if strategy == "dummy_mean":
        return float(y.mean())
    if strategy == "dummy_median":
        return float(y.median())
    if strategy == "dummy_last":
        ordered = train_df.assign(_target=pd.to_numeric(train_df[target_col], errors="coerce"))
        ordered = ordered.dropna(subset=["_target"]).sort_values(["calendarDate", "analysis_window_id"])
        return float(ordered["_target"].iloc[-1])
    raise ValueError(f"Unknown dummy baseline strategy: {strategy}")


def _fit_estimator_suppressing_convergence_warnings(estimator: BaseEstimator, X: Any, y: Any) -> BaseEstimator:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        return estimator.fit(X, y)


def _record_value(record: Mapping[str, object], key: str, default: object) -> object:
    value = record.get(key, default)
    if _is_missing_scalar(value):
        return default
    return value


def _optional_record_float(record: Mapping[str, object], key: str) -> float | None:
    value = record.get(key)
    if _is_missing_scalar(value):
        return None
    return float(value)


def _optional_record_int(record: Mapping[str, object], key: str) -> int | None:
    value = record.get(key)
    if _is_missing_scalar(value):
        return None
    return int(float(value))


def _is_missing_scalar(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _estimator_coefficients(model: BaseEstimator) -> np.ndarray | None:
    coefficients = getattr(model, "coef_", None)
    if coefficients is None and hasattr(model, "model_"):
        coefficients = getattr(model.model_, "coef_", None)
    if coefficients is None:
        return None
    return np.asarray(coefficients, dtype=float)


def _source_feature_from_transformed_name(name: str, selected_features: Sequence[str]) -> str:
    clean = str(name)
    if "__" in clean:
        clean = clean.split("__", 1)[1]
    if clean.startswith("missingindicator_"):
        clean = clean.removeprefix("missingindicator_")
    if clean in selected_features:
        return clean
    for feature in sorted(selected_features, key=len, reverse=True):
        if clean == feature or clean.startswith(f"{feature}_"):
            return feature
    return clean


def _normalize_dummy_validation_summary(dummy_tuning_summary: pd.DataFrame) -> pd.DataFrame:
    out = dummy_tuning_summary.copy()
    aliases = {
        "valid_mae": "mean_valid_mae",
        "valid_mae_std": "std_valid_mae",
        "valid_rmse": "mean_valid_rmse",
        "valid_rmse_std": "std_valid_rmse",
        "valid_r2": "mean_valid_r2",
        "valid_r2_std": "std_valid_r2",
        "valid_spearman": "mean_valid_spearman",
        "valid_spearman_std": "std_valid_spearman",
        "train_mae": "mean_train_mae",
        "train_mae_std": "std_train_mae",
        "train_rmse": "mean_train_rmse",
        "train_rmse_std": "std_train_rmse",
        "train_r2": "mean_train_r2",
        "train_r2_std": "std_train_r2",
    }
    for source, alias in aliases.items():
        if alias not in out.columns and source in out.columns:
            out[alias] = out[source]
    out["candidate_short_label"] = out.get("candidate_short_label", out["model_kind"])
    out["feature_selection_mode"] = out.get("feature_selection_mode", "none")
    out["robust_clip"] = out.get("robust_clip", "none")
    out["calibration"] = out.get("calibration", "none")
    sort_col = "mean_valid_mae" if "mean_valid_mae" in out.columns else "selection_metric_value"
    return out.sort_values(sort_col, na_position="last").reset_index(drop=True)


def _attach_leaderboard_test_metrics(rows: pd.DataFrame, leaderboard: pd.DataFrame) -> pd.DataFrame:
    test_cols = [
        "test_mae",
        "test_rmse",
        "test_r2",
        "test_pearson",
        "test_spearman",
        "test_bias_pred_minus_target",
    ]
    available_test_cols = [column for column in test_cols if column in leaderboard.columns]
    if not available_test_cols:
        return rows
    out = rows.copy()
    if "candidate_id" in out.columns and "candidate_id" in leaderboard.columns:
        keyed_rows = out.assign(_candidate_id_key=pd.to_numeric(out["candidate_id"], errors="coerce"))
        keyed_leaderboard = leaderboard.assign(
            _candidate_id_key=pd.to_numeric(leaderboard["candidate_id"], errors="coerce")
        )
        merge_cols = ["_candidate_id_key", *available_test_cols]
        merged = keyed_rows.merge(
            keyed_leaderboard[merge_cols].dropna(subset=["_candidate_id_key"]).drop_duplicates("_candidate_id_key"),
            on="_candidate_id_key",
            how="left",
            suffixes=("", "_leaderboard"),
        ).drop(columns=["_candidate_id_key"])
    elif {"model_kind", "candidate_short_label"} <= set(out.columns) and {
        "model_kind",
        "candidate_short_label",
    } <= set(leaderboard.columns):
        merge_cols = ["model_kind", "candidate_short_label", *available_test_cols]
        merged = out.merge(
            leaderboard[merge_cols].drop_duplicates(["model_kind", "candidate_short_label"]),
            on=["model_kind", "candidate_short_label"],
            how="left",
            suffixes=("", "_leaderboard"),
        )
    else:
        return out
    for column in available_test_cols:
        leaderboard_col = f"{column}_leaderboard"
        if leaderboard_col in merged.columns:
            if column in merged.columns:
                merged[column] = merged[column].combine_first(merged[leaderboard_col])
            else:
                merged[column] = merged[leaderboard_col]
            merged = merged.drop(columns=[leaderboard_col])
    return merged


def _attach_dummy_test_metrics(rows: pd.DataFrame, leaderboard: pd.DataFrame) -> pd.DataFrame:
    test_cols = [
        "test_mae",
        "test_rmse",
        "test_r2",
        "test_pearson",
        "test_spearman",
        "test_bias_pred_minus_target",
    ]
    available_test_cols = [column for column in test_cols if column in leaderboard.columns]
    if not available_test_cols or "model_kind" not in leaderboard.columns:
        return rows
    dummy_lookup = leaderboard.loc[
        leaderboard.get("candidate_type", pd.Series(index=leaderboard.index, dtype=object)).astype(str).eq("dummy")
    ].copy()
    if dummy_lookup.empty:
        dummy_lookup = leaderboard.loc[leaderboard["model_kind"].astype(str).str.startswith("dummy_")].copy()
    if dummy_lookup.empty:
        return rows
    merged = rows.merge(
        dummy_lookup[["model_kind", *available_test_cols]].drop_duplicates("model_kind"),
        on="model_kind",
        how="left",
        suffixes=("", "_leaderboard"),
    )
    for column in available_test_cols:
        leaderboard_col = f"{column}_leaderboard"
        if leaderboard_col in merged.columns:
            if column in merged.columns:
                merged[column] = merged[column].combine_first(merged[leaderboard_col])
            else:
                merged[column] = merged[leaderboard_col]
            merged = merged.drop(columns=[leaderboard_col])
    return merged


def _plan_option_line(name: str, values: object) -> str:
    items = list(values) if isinstance(values, Sequence) and not isinstance(values, str) else [values]
    return f"  {name}: {items}  count={len(items)}"


def _validation_parameter_record(row: pd.Series) -> dict[str, object]:
    model_kind = str(row.get("model_kind", "model"))
    model_params: list[str] = []
    if model_kind in {"ridge", "lasso", "elastic_net", "huber"} and pd.notna(row.get("alpha")):
        model_params.append(f"alpha={_compact_number(row['alpha'])}")
    if model_kind == "elastic_net" and pd.notna(row.get("l1_ratio")):
        model_params.append(f"l1_ratio={_compact_number(row['l1_ratio'])}")
    if model_kind == "huber" and pd.notna(row.get("epsilon")):
        model_params.append(f"epsilon={_compact_number(row['epsilon'])}")
    if model_kind == "pls" and pd.notna(row.get("n_components")):
        model_params.append(f"n_components={_compact_number(row['n_components'])}")

    selector_mode = str(row.get("feature_selection_mode", "none"))
    selector_params: list[str] = []
    if selector_mode in {"top_spearman", "top_mutual_info", "spearman_then_correlation"}:
        selector_params.append(f"top_k={_compact_number(row.get('feature_selection_top_k'))}")
    if selector_mode in {"correlation_prune", "spearman_then_correlation"}:
        selector_params.append(
            f"corr={_compact_number(row.get('feature_selection_correlation_threshold'))}"
        )
    if selector_mode == "lasso_nonzero":
        selector_params.append(
            f"alpha={_compact_number(row.get('feature_selection_lasso_alpha'))}"
        )
    if selector_mode != "none":
        selector_params.append(
            f"min_features={_compact_number(row.get('feature_selection_min_features'))}"
        )

    model_label = model_kind.replace("_", " ").title()
    if model_kind == "elastic_net":
        model_label = "ElasticNet"
    elif model_kind == "pls":
        model_label = "PLS"
    model_short = model_label
    if model_kind in {"ridge", "lasso", "elastic_net", "huber"} and pd.notna(row.get("alpha")):
        model_short += f" alpha={_compact_number(row['alpha'])}"
    if model_kind == "elastic_net" and pd.notna(row.get("l1_ratio")):
        model_short += f" l1={_compact_number(row['l1_ratio'])}"
    if model_kind == "huber" and pd.notna(row.get("epsilon")):
        model_short += f" eps={_compact_number(row['epsilon'])}"
    if model_kind == "pls" and pd.notna(row.get("n_components")):
        model_short += f" k={_compact_number(row['n_components'])}"
    selector_short = selector_mode
    if selector_mode in {"top_spearman", "top_mutual_info"}:
        selector_short += f"_{_compact_number(row.get('feature_selection_top_k'))}"
    elif selector_mode == "spearman_then_correlation":
        selector_short += (
            f"_{_compact_number(row.get('feature_selection_top_k'))}"
            f"_corr{_compact_number(row.get('feature_selection_correlation_threshold'))}"
        )
    elif selector_mode == "correlation_prune":
        selector_short += f"_{_compact_number(row.get('feature_selection_correlation_threshold'))}"
    elif selector_mode == "lasso_nonzero":
        selector_short += f"_{_compact_number(row.get('feature_selection_lasso_alpha'))}"
    short_label = f"{model_short} | {selector_short} | clip={row.get('robust_clip', 'none')}"
    if str(row.get("calibration", "none")) != "none":
        short_label += f" | cal={row['calibration']}"
    if str(row.get("target_transform", "none")) != "none":
        short_label += f" | target={row['target_transform']}"

    return {
        "model_param_1": model_params[0] if len(model_params) > 0 else "",
        "model_param_2": model_params[1] if len(model_params) > 1 else "",
        "feature_selection_param_1": selector_params[0] if len(selector_params) > 0 else "",
        "feature_selection_param_2": selector_params[1] if len(selector_params) > 1 else "",
        "model_parameter_label": ", ".join(model_params),
        "feature_selection_parameter_label": ", ".join(selector_params),
        "feature_selection_config_label": selector_short,
        "candidate_short_label": short_label,
    }


def _compact_number(value: object) -> str:
    if pd.isna(value):
        return ""
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.6g}"


def _best_dummy_validation_mae(dummy_tuning_summary: pd.DataFrame) -> float:
    for column in ["mean_valid_mae", "valid_mae", "selection_metric_value"]:
        if column in dummy_tuning_summary.columns:
            values = pd.to_numeric(dummy_tuning_summary[column], errors="coerce")
            if values.notna().any():
                return float(values.min())
    return np.nan


def _best_dummy_validation_row(dummy_tuning_summary: pd.DataFrame) -> pd.Series | None:
    if dummy_tuning_summary.empty:
        return None
    for column in ["mean_valid_mae", "valid_mae", "selection_metric_value"]:
        if column in dummy_tuning_summary.columns:
            values = pd.to_numeric(dummy_tuning_summary[column], errors="coerce")
            if values.notna().any():
                return dummy_tuning_summary.loc[values.idxmin()]
    return None


def _model_family_colors(model_kinds: Sequence[object]) -> dict[str, str]:
    palette = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2", "#9D755D"]
    return {
        str(model_kind): palette[idx % len(palette)]
        for idx, model_kind in enumerate(sorted(str(value) for value in model_kinds))
    }


def _feature_selector_family(config_label: object) -> str:
    label = str(config_label)
    for family in [
        "spearman_then_correlation",
        "top_spearman",
        "top_mutual_info",
        "correlation_prune",
        "lasso_nonzero",
    ]:
        if label.startswith(family):
            return family
    return "none" if label == "none" else "other"


def _feature_selector_color_map(config_labels: Sequence[object]) -> dict[str, str]:
    family_colors = {
        "none": "#C5CAD3",
        "top_spearman": "#A3BEFA",
        "top_mutual_info": "#F0986E",
        "correlation_prune": "#A3D576",
        "spearman_then_correlation": "#F390CA",
        "lasso_nonzero": "#FFE15B",
        "other": "#E2E5EA",
    }
    return {
        str(label): family_colors[_feature_selector_family(label)]
        for label in config_labels
    }


def _feature_selector_family_map(config_labels: Sequence[object]) -> dict[str, str]:
    return {
        str(label): _feature_selector_family(label).replace("_", " ")
        for label in config_labels
    }


def _boxplot_by_group(
    ax: Any,
    frame: pd.DataFrame,
    *,
    group_col: str,
    value_col: str,
    title: str,
    group_label: str,
    value_label: str | None = None,
    zero_reference: bool = True,
    group_color_map: Mapping[str, str] | None = None,
    group_family_map: Mapping[str, str] | None = None,
    legend_title: str | None = None,
) -> None:
    groups = (
        frame.groupby(group_col, dropna=False)[value_col]
        .median()
        .sort_values()
        .index.tolist()
    )
    values = [
        pd.to_numeric(
            frame.loc[frame[group_col].eq(group), value_col],
            errors="coerce",
        ).dropna().to_numpy(dtype=float)
        for group in groups
    ]
    box = ax.boxplot(
        values,
        tick_labels=groups,
        patch_artist=True,
        showfliers=True,
        orientation="horizontal",
    )
    for patch, group in zip(box["boxes"], groups):
        patch.set_facecolor(
            group_color_map.get(str(group), "#A3BEFA")
            if group_color_map is not None
            else "#A3BEFA"
        )
        patch.set_edgecolor("#2E4780")
        patch.set_alpha(0.72)
    if group_color_map is not None and group_family_map is not None:
        from matplotlib.patches import Patch

        family_handles: dict[str, Any] = {}
        for group in groups:
            family = group_family_map.get(str(group), str(group))
            if family not in family_handles:
                family_handles[family] = Patch(
                    facecolor=group_color_map.get(str(group), "#A3BEFA"),
                    edgecolor="#2E4780",
                    alpha=0.72,
                    label=family,
                )
        ax.legend(
            handles=list(family_handles.values()),
            title=legend_title,
            frameon=False,
            loc="best",
        )
    if zero_reference:
        ax.axvline(0.0, color="#333333", linestyle="--", linewidth=1.0)
    ax.invert_yaxis()
    ax.set_title(title)
    ax.set_xlabel(value_label or value_col.replace("_", " "))
    ax.set_ylabel(group_label)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(True, axis="x", color="#E6E6E6")


_GRID_SPEC_SEQUENCE_FIELDS = {
    "model_kinds",
    "feature_selection_modes",
    "top_k_values",
    "min_abs_spearman_values",
    "min_mutual_info_values",
    "correlation_thresholds",
    "lasso_selector_alphas",
    "robust_clips",
    "calibrations",
    "target_transforms",
    "prediction_clips",
    "ridge_alphas",
    "lasso_alphas",
    "elastic_net_alphas",
    "elastic_net_l1_ratios",
    "huber_alphas",
    "huber_epsilons",
    "pls_components",
}


def _coerce_grid_spec_overrides(overrides: Mapping[str, object]) -> dict[str, object]:
    fields = set(Stage4LinearGridSpec.__dataclass_fields__)
    clean: dict[str, object] = {}
    for key, value in overrides.items():
        if key not in fields:
            raise TypeError(f"Unknown Stage4LinearGridSpec field: {key}")
        if value is None:
            continue
        if key in _GRID_SPEC_SEQUENCE_FIELDS:
            clean[key] = _as_tuple(value)
        else:
            clean[key] = value
    return clean


def _as_tuple(value: object) -> tuple[object, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _validate_grid_spec(grid_spec: Stage4LinearGridSpec) -> None:
    _validate_known_values("model_kinds", grid_spec.model_kinds, STAGE4_LINEAR_MODEL_KINDS)
    _validate_known_values(
        "feature_selection_modes",
        grid_spec.feature_selection_modes,
        STAGE4_LINEAR_FEATURE_SELECTION_MODES,
    )
    _validate_known_values("robust_clips", grid_spec.robust_clips, ("none", "z=4", "z=5"))
    _validate_known_values("calibrations", grid_spec.calibrations, ("none", "linear"))
    _validate_known_values("target_transforms", grid_spec.target_transforms, ("none", "log1p"))
    _validate_known_values("prediction_clips", grid_spec.prediction_clips, ("none", "0_100"))
    if not grid_spec.model_kinds:
        raise ValueError("grid_spec.model_kinds must not be empty")
    if not grid_spec.feature_selection_modes:
        raise ValueError("grid_spec.feature_selection_modes must not be empty")
    if not grid_spec.robust_clips:
        raise ValueError("grid_spec.robust_clips must not be empty")
    if not grid_spec.calibrations:
        raise ValueError("grid_spec.calibrations must not be empty")
    if not grid_spec.target_transforms:
        raise ValueError("grid_spec.target_transforms must not be empty")
    if not grid_spec.prediction_clips:
        raise ValueError("grid_spec.prediction_clips must not be empty")


def _validate_known_values(name: str, values: Sequence[object], allowed: Sequence[object]) -> None:
    unknown = sorted(set(values) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown {name}: {unknown}. Allowed: {list(allowed)}")


def _first_non_null(frame: pd.DataFrame, column: str, default: str) -> str:
    if column not in frame.columns:
        return default
    values = frame[column].dropna().astype(str)
    return values.iloc[0] if not values.empty else default


def _prediction_provenance_label(values: pd.Series) -> str:
    provenance = {str(value) for value in values.dropna().unique()}
    if {"final_refit_future_test", "final_refit_in_sample_pretest"} <= provenance:
        return "final-refit predictions; train/valid in-sample"
    if provenance == {"final_refit_future_test"}:
        return "final-refit future-test predictions"
    if provenance == {"final_refit_in_sample_pretest"}:
        return "final-refit pre-test in-sample predictions"
    if provenance:
        return ", ".join(sorted(provenance))
    return "prediction provenance unavailable"


def _feature_selection_configs_from_grid_spec(grid_spec: Stage4LinearGridSpec) -> list[Stage4FeatureSelectionConfig]:
    configs: list[Stage4FeatureSelectionConfig] = []
    modes = set(grid_spec.feature_selection_modes)
    if "none" in modes:
        configs.append(Stage4FeatureSelectionConfig(mode="none", min_features=grid_spec.min_features))
    if "top_spearman" in modes:
        for top_k, min_abs_spearman in product(grid_spec.top_k_values, grid_spec.min_abs_spearman_values):
            configs.append(
                Stage4FeatureSelectionConfig(
                    mode="top_spearman",
                    top_k=int(top_k),
                    min_features=grid_spec.min_features,
                    min_abs_spearman=float(min_abs_spearman),
                )
            )
    if "top_mutual_info" in modes:
        for top_k, min_mutual_info in product(grid_spec.top_k_values, grid_spec.min_mutual_info_values):
            configs.append(
                Stage4FeatureSelectionConfig(
                    mode="top_mutual_info",
                    top_k=int(top_k),
                    min_features=grid_spec.min_features,
                    min_mutual_info=float(min_mutual_info),
                )
            )
    if "correlation_prune" in modes:
        for threshold in grid_spec.correlation_thresholds:
            configs.append(
                Stage4FeatureSelectionConfig(
                    mode="correlation_prune",
                    min_features=grid_spec.min_features,
                    correlation_threshold=float(threshold),
                )
            )
    if "spearman_then_correlation" in modes:
        for top_k, min_abs_spearman, threshold in product(
            grid_spec.top_k_values,
            grid_spec.min_abs_spearman_values,
            grid_spec.correlation_thresholds,
        ):
            configs.append(
                Stage4FeatureSelectionConfig(
                    mode="spearman_then_correlation",
                    top_k=int(top_k),
                    min_features=grid_spec.min_features,
                    min_abs_spearman=float(min_abs_spearman),
                    correlation_threshold=float(threshold),
                )
            )
    if "lasso_nonzero" in modes:
        for alpha in grid_spec.lasso_selector_alphas:
            configs.append(
                Stage4FeatureSelectionConfig(
                    mode="lasso_nonzero",
                    min_features=grid_spec.min_features,
                    lasso_alpha=float(alpha),
                    lasso_max_iter=grid_spec.lasso_selector_max_iter,
                )
            )
    return configs


def _model_configs_from_grid_spec(grid_spec: Stage4LinearGridSpec) -> list[dict[str, object]]:
    configs: list[dict[str, object]] = []
    kinds = set(grid_spec.model_kinds)
    if "linear" in kinds:
        configs.append({"model_kind": "linear"})
    if "ridge" in kinds:
        configs.extend({"model_kind": "ridge", "alpha": float(alpha)} for alpha in grid_spec.ridge_alphas)
    if "lasso" in kinds:
        configs.extend({"model_kind": "lasso", "alpha": float(alpha)} for alpha in grid_spec.lasso_alphas)
    if "elastic_net" in kinds:
        configs.extend(
            {
                "model_kind": "elastic_net",
                "alpha": float(alpha),
                "l1_ratio": float(l1_ratio),
            }
            for alpha, l1_ratio in product(grid_spec.elastic_net_alphas, grid_spec.elastic_net_l1_ratios)
        )
    if "huber" in kinds:
        configs.extend(
            {
                "model_kind": "huber",
                "alpha": float(alpha),
                "epsilon": float(epsilon),
            }
            for alpha, epsilon in product(grid_spec.huber_alphas, grid_spec.huber_epsilons)
        )
    if "pls" in kinds:
        configs.extend(
            {"model_kind": "pls", "n_components": int(n_components)}
            for n_components in grid_spec.pls_components
        )
    if not configs:
        raise ValueError("Grid spec produced no model configurations")
    return configs


def _feature_blocks(frame: pd.DataFrame, feature_columns: Sequence[str]) -> tuple[list[str], list[str]]:
    numeric_cols: list[str] = []
    categorical_cols: list[str] = []
    for column in feature_columns:
        if column not in frame.columns:
            continue
        if pd.api.types.is_numeric_dtype(frame[column]) or pd.api.types.is_bool_dtype(frame[column]):
            numeric_cols.append(column)
        else:
            categorical_cols.append(column)
    return numeric_cols, categorical_cols


def _numeric_imputed_frame(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    data: dict[str, pd.Series] = {}
    for column in columns:
        values = (
            pd.to_numeric(frame[column], errors="coerce")
            .astype("float64")
            .replace([np.inf, -np.inf], np.nan)
        )
        median = values.median()
        if not np.isfinite(median):
            median = 0.0
        data[column] = values.fillna(float(median))
    return pd.DataFrame(data, index=frame.index)


def _safe_corr_pair(x: pd.Series, y: pd.Series, *, method: str) -> float:
    valid = x.notna() & y.notna()
    if int(valid.sum()) < 3:
        return np.nan
    return _safe_corr(x.loc[valid].to_numpy(dtype=float), y.loc[valid].to_numpy(dtype=float), method=method)


def _safe_corr(x: Any, y: Any, *, method: str) -> float:
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    valid = np.isfinite(x_arr) & np.isfinite(y_arr)
    if int(valid.sum()) < 3:
        return np.nan
    x_arr = x_arr[valid]
    y_arr = y_arr[valid]
    if np.nanstd(x_arr) <= 1e-12 or np.nanstd(y_arr) <= 1e-12:
        return np.nan
    if method == "pearson":
        return float(stats.pearsonr(x_arr, y_arr).statistic)
    if method == "spearman":
        return float(stats.spearmanr(x_arr, y_arr, nan_policy="omit").statistic)
    raise ValueError(method)


def _top_ranked_features(
    scores: pd.DataFrame,
    *,
    score_col: str,
    top_k: int,
    min_score: float,
) -> list[str]:
    ranked = scores.loc[scores[score_col].fillna(0.0).ge(min_score)].copy()
    ranked = ranked.sort_values([score_col, "feature"], ascending=[False, True])
    return ranked.head(max(1, int(top_k)))["feature"].tolist()


def _correlation_pruned_features(
    train_df: pd.DataFrame,
    columns: Sequence[str],
    scores: pd.DataFrame,
    *,
    threshold: float,
) -> tuple[list[str], dict[str, str]]:
    if not 0 < threshold <= 1:
        raise ValueError("correlation threshold must be in (0, 1]")
    columns = [column for column in columns if column in train_df.columns]
    if not columns:
        return [], {}
    X = _numeric_imputed_frame(train_df, columns)
    corr = X.corr(method="spearman").abs().fillna(0.0)
    score_lookup = scores.set_index("feature")["selection_score"].fillna(0.0).to_dict()
    ranked = sorted(columns, key=lambda column: (-score_lookup.get(column, 0.0), column))
    selected: list[str] = []
    dropped: dict[str, str] = {}
    for feature in ranked:
        if not selected:
            selected.append(feature)
            continue
        selected_corr = corr.loc[feature, selected]
        max_corr = float(selected_corr.max()) if len(selected_corr) else 0.0
        if max_corr <= threshold:
            selected.append(feature)
        else:
            dropped[feature] = f"abs_spearman_corr>{threshold:g} with {selected_corr.idxmax()}"
    return selected, dropped


def _lasso_nonzero_features(
    train_df: pd.DataFrame,
    columns: Sequence[str],
    target_col: str,
    *,
    alpha: float,
    max_iter: int,
    tol: float,
    random_state: int,
) -> tuple[list[str], pd.DataFrame]:
    columns = [column for column in columns if column in train_df.columns]
    if not columns:
        return [], pd.DataFrame(columns=["feature", "feature_selection_lasso_coef"])
    X = _numeric_imputed_frame(train_df, columns)
    y = pd.to_numeric(train_df[target_col], errors="coerce")
    valid = y.notna()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.loc[valid])
    model = Lasso(alpha=float(alpha), fit_intercept=True, max_iter=max_iter, tol=tol, random_state=random_state)
    _fit_estimator_suppressing_convergence_warnings(model, X_scaled, y.loc[valid].to_numpy(dtype=float))
    detail = pd.DataFrame(
        {
            "feature": columns,
            "feature_selection_lasso_coef": np.ravel(model.coef_),
        }
    )
    detail["feature_selection_lasso_abs_coef"] = detail["feature_selection_lasso_coef"].abs()
    selected = detail.loc[detail["feature_selection_lasso_abs_coef"].gt(1e-8), "feature"].tolist()
    return selected, detail


def _ensure_minimum_features(selected: Sequence[str], fallback: Sequence[str], min_features: int) -> list[str]:
    out = list(dict.fromkeys(selected))
    for feature in fallback:
        if len(out) >= min_features:
            break
        if feature not in out:
            out.append(feature)
    return out


def _make_estimator(candidate: Stage4LinearCandidate) -> BaseEstimator:
    if candidate.model_kind == "linear":
        return LinearRegression(fit_intercept=candidate.fit_intercept)
    if candidate.model_kind == "ridge":
        return Ridge(alpha=float(candidate.alpha), fit_intercept=candidate.fit_intercept)
    if candidate.model_kind == "lasso":
        return Lasso(
            alpha=float(candidate.alpha),
            fit_intercept=candidate.fit_intercept,
            max_iter=candidate.max_iter,
            tol=candidate.tol,
            random_state=0,
        )
    if candidate.model_kind == "elastic_net":
        return ElasticNet(
            alpha=float(candidate.alpha),
            l1_ratio=float(candidate.l1_ratio),
            fit_intercept=candidate.fit_intercept,
            max_iter=candidate.max_iter,
            tol=candidate.tol,
            random_state=0,
        )
    if candidate.model_kind == "huber":
        return HuberRegressor(
            epsilon=float(candidate.epsilon),
            alpha=float(candidate.alpha),
            fit_intercept=candidate.fit_intercept,
            max_iter=candidate.max_iter,
            tol=candidate.tol,
        )
    if candidate.model_kind == "pls":
        return SafePLSRegressor(n_components=int(candidate.n_components or 3))
    raise ValueError(f"Unsupported model_kind: {candidate.model_kind}")


def _transform_target(y: Any, mode: str) -> np.ndarray:
    y_array = np.asarray(y, dtype=float)
    if mode == "none":
        return y_array
    if mode == "log1p":
        return np.log1p(np.clip(y_array, 0.0, None))
    raise ValueError(f"Unsupported target_transform: {mode}")


def _inverse_transform_target(y: Any, mode: str) -> np.ndarray:
    y_array = np.asarray(y, dtype=float)
    if mode == "none":
        return y_array
    if mode == "log1p":
        return np.expm1(y_array)
    raise ValueError(f"Unsupported target_transform: {mode}")


def _parse_robust_clip(mode: str) -> float | None:
    if mode == "none":
        return None
    if mode.startswith("z="):
        return float(mode.split("=", 1)[1])
    raise ValueError(f"Unsupported robust_clip mode: {mode}")


def _identity_calibration(mode: str, *, reason: str = "") -> dict[str, object]:
    return {
        "calibration": mode,
        "calibration_fit_source": "oof" if mode != "none" else "none",
        "calibration_applied": False,
        "calibration_intercept": 0.0,
        "calibration_slope": 1.0,
        "calibration_skip_reason": reason,
    }


def _candidate_record(candidate: Stage4LinearCandidate) -> dict[str, object]:
    selection = candidate.feature_selection
    return {
        "candidate_id": candidate.candidate_id,
        "model_kind": candidate.model_kind,
        "feature_selection_mode": selection.mode,
        "feature_selection_top_k": selection.top_k,
        "feature_selection_min_features": selection.min_features,
        "feature_selection_min_abs_spearman": selection.min_abs_spearman,
        "feature_selection_min_mutual_info": selection.min_mutual_info,
        "feature_selection_correlation_threshold": selection.correlation_threshold,
        "feature_selection_lasso_alpha": selection.lasso_alpha,
        "robust_clip": candidate.robust_clip,
        "calibration": candidate.calibration,
        "target_transform": candidate.target_transform,
        "prediction_clip": candidate.prediction_clip,
        "alpha": candidate.alpha,
        "l1_ratio": candidate.l1_ratio,
        "epsilon": candidate.epsilon,
        "n_components": candidate.n_components,
        "fit_intercept": candidate.fit_intercept,
        "max_iter": candidate.max_iter,
        "tol": candidate.tol,
    }


def _calibration_record_for_table(record: Mapping[str, object]) -> dict[str, object]:
    return {
        "calibration_fit_source": record.get("calibration_fit_source", "none"),
        "calibration_applied": bool(record.get("calibration_applied", False)),
        "calibration_intercept": float(record.get("calibration_intercept", 0.0)),
        "calibration_slope": float(record.get("calibration_slope", 1.0)),
        "calibration_skip_reason": record.get("calibration_skip_reason", ""),
    }


def _prediction_frame(
    split_df: pd.DataFrame,
    target_col: str,
    prediction: np.ndarray,
    *,
    model_name: str,
    model_kind: str,
    split_name: str,
    candidate: Stage4LinearCandidate | None = None,
    candidate_type: str = "linear_family",
    validation_selection_rank: int | None = None,
    prediction_provenance: str = "",
) -> pd.DataFrame:
    out = split_df[["analysis_window_id", "calendarDate", target_col]].copy()
    out["split"] = split_name
    out["candidate_type"] = candidate_type
    out["model_name"] = model_name
    out["model_kind"] = model_kind
    out["validation_selection_rank"] = validation_selection_rank
    out["prediction_provenance"] = prediction_provenance
    if candidate is not None:
        for key, value in _candidate_record(candidate).items():
            out[key] = value
    out["prediction"] = prediction
    out["residual"] = out["prediction"] - out[target_col]
    out["abs_error"] = out["residual"].abs()
    return out


def _markdown_table(df: pd.DataFrame, columns: Sequence[str]) -> str:
    available = [column for column in columns if column in df.columns]
    if df.empty or not available:
        return "No rows available."
    rows = df[available].to_dict("records")

    def fmt(value: object) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.3f}"
        if isinstance(value, (bool, np.bool_)):
            return "true" if bool(value) else "false"
        return str(value).replace("|", "\\|")

    lines = [
        "| " + " | ".join(available) + " |",
        "| " + " | ".join("---" for _ in available) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column, "")) for column in available) + " |")
    return "\n".join(lines)
