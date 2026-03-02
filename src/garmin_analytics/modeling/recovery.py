from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeVar

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import ElasticNet, Lasso, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

T = TypeVar("T")


@dataclass(frozen=True)
class TimeSplitConfig:
    train_frac: float = 0.6
    valid_frac: float = 0.2


def split_time_ordered(
    frame: pd.DataFrame,
    *,
    date_col: str = "calendarDate",
    train_frac: float = 0.6,
    valid_frac: float = 0.2,
) -> dict[str, pd.DataFrame]:
    """Split a frame into contiguous train/valid/test blocks ordered by date."""
    if not 0 < train_frac < 1:
        raise ValueError("train_frac must be between 0 and 1")
    if not 0 <= valid_frac < 1:
        raise ValueError("valid_frac must be between 0 and 1")
    if train_frac + valid_frac >= 1:
        raise ValueError("train_frac + valid_frac must be < 1")
    if date_col not in frame.columns:
        raise KeyError(f"frame is missing date column: {date_col}")

    ordered = frame.copy()
    ordered[date_col] = pd.to_datetime(ordered[date_col], errors="coerce")
    ordered = ordered.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    n = len(ordered)
    if n < 3:
        raise ValueError("need at least 3 rows for a time-ordered split")

    train_end = max(1, int(np.floor(n * train_frac)))
    valid_end = max(train_end + 1, int(np.floor(n * (train_frac + valid_frac))))
    valid_end = min(valid_end, n - 1)

    return {
        "train": ordered.iloc[:train_end].copy(),
        "valid": ordered.iloc[train_end:valid_end].copy(),
        "test": ordered.iloc[valid_end:].copy(),
    }


def _feature_blocks(frame: pd.DataFrame, feature_cols: Sequence[str]) -> tuple[list[str], list[str]]:
    numeric_cols: list[str] = []
    categorical_cols: list[str] = []
    for col in feature_cols:
        if col not in frame.columns:
            continue
        if pd.api.types.is_numeric_dtype(frame[col]) or pd.api.types.is_bool_dtype(frame[col]):
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)
    return numeric_cols, categorical_cols


def _make_preprocessor(frame: pd.DataFrame, feature_cols: Sequence[str]) -> ColumnTransformer:
    numeric_cols, categorical_cols = _feature_blocks(frame, feature_cols)
    transformers: list[tuple[str, Pipeline, list[str]]] = []

    if numeric_cols:
        transformers.append(
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
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
        raise ValueError("No usable feature columns were found in the frame")

    return ColumnTransformer(transformers=transformers, remainder="drop")


def _prepare_model_frame(
    frame: pd.DataFrame,
    *,
    feature_cols: Sequence[str],
    target_col: str,
    date_col: str = "calendarDate",
) -> pd.DataFrame:
    required = [date_col, target_col]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise KeyError(f"frame missing required columns: {missing}")

    keep_cols = [date_col, target_col, *[c for c in feature_cols if c in frame.columns]]
    out = frame[keep_cols].copy()
    out = out.dropna(subset=[target_col])
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    out = out.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    return out


def _existing_feature_cols(frame: pd.DataFrame, feature_cols: Sequence[str]) -> list[str]:
    return [c for c in feature_cols if c in frame.columns]


def _select_model_specs(model_specs: dict[str, T], model_names: Sequence[str] | None) -> dict[str, T]:
    if model_names is None:
        return model_specs

    missing = [name for name in model_names if name not in model_specs]
    if missing:
        raise KeyError(f"Unknown model names: {missing}")
    return {name: model_specs[name] for name in model_names}


def _classification_model_specs(random_state: int) -> dict[str, object]:
    return {
        "dummy_most_frequent": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_state),
        "logistic_regression_l1": LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            solver="saga",
            l1_ratio=1.0,
            C=0.3,
            random_state=random_state,
        ),
        "logistic_regression_elasticnet": LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            solver="saga",
            l1_ratio=0.5,
            C=0.5,
            random_state=random_state,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=3,
            class_weight="balanced_subsample",
            random_state=random_state,
        ),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_depth=3,
            max_leaf_nodes=15,
            min_samples_leaf=10,
            random_state=random_state,
        ),
    }


def _regression_model_specs(random_state: int) -> dict[str, object]:
    return {
        "dummy_median": DummyRegressor(strategy="median"),
        "ridge": Ridge(alpha=1.0),
        "lasso": Lasso(alpha=0.05, max_iter=5000),
        "elastic_net": ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=5000),
        "random_forest": RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=3,
            random_state=random_state,
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_depth=3,
            max_leaf_nodes=15,
            min_samples_leaf=10,
            random_state=random_state,
        ),
    }


def _classification_metrics(y_true: pd.Series, y_pred: np.ndarray, y_proba: np.ndarray | None) -> dict[str, float]:
    labels = [0, 1]
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    tn, fp, fn, tp = cm.ravel()
    recalls: list[float] = []
    if (tp + fn) > 0:
        recalls.append(tp / (tp + fn))
    if (tn + fp) > 0:
        recalls.append(tn / (tn + fp))

    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(np.mean(recalls)) if recalls else np.nan,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "positive_rate_true": float(pd.Series(y_true).mean()),
        "positive_rate_pred": float(pd.Series(y_pred).mean()),
    }

    if y_proba is not None and len(pd.Series(y_true).unique()) > 1:
        out["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        out["pr_auc"] = float(average_precision_score(y_true, y_proba))
    else:
        out["roc_auc"] = np.nan
        out["pr_auc"] = np.nan
    return out


def _regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": rmse,
        "r2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else np.nan,
        "pred_min": float(np.min(y_pred)) if len(y_pred) else np.nan,
        "pred_max": float(np.max(y_pred)) if len(y_pred) else np.nan,
    }


def _classification_metrics_from_threshold(
    y_true: pd.Series,
    y_score: np.ndarray | None,
    *,
    threshold: float,
    fallback_pred: np.ndarray | None = None,
) -> dict[str, float]:
    if y_score is not None:
        y_score = np.asarray(y_score, dtype=float)
        y_pred = (y_score >= threshold).astype(int)
    elif fallback_pred is not None:
        y_pred = np.asarray(fallback_pred).astype(int)
    else:
        raise ValueError("Need either y_score or fallback_pred for classification metrics")
    return _classification_metrics(y_true, y_pred, y_score)


def build_confusion_table(
    y_true: pd.Series,
    y_score: np.ndarray | None,
    *,
    threshold: float,
    fallback_pred: np.ndarray | None = None,
) -> pd.DataFrame:
    """Return a compact confusion-matrix table for a chosen threshold."""
    if y_score is not None:
        y_score = np.asarray(y_score, dtype=float)
        y_pred = (y_score >= threshold).astype(int)
    elif fallback_pred is not None:
        y_pred = np.asarray(fallback_pred).astype(int)
    else:
        raise ValueError("Need either y_score or fallback_pred for confusion table")

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else np.nan
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else np.nan
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else np.nan

    return pd.DataFrame(
        [
            {
                "threshold": float(threshold),
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
                "precision": precision,
                "recall": recall,
                "specificity": specificity,
            }
        ]
    )


def tune_probability_threshold(
    y_true: pd.Series,
    y_score: np.ndarray,
    *,
    metric: str = "balanced_accuracy",
    thresholds: Sequence[float] | None = None,
) -> dict[str, float]:
    """Select a probability threshold on a validation slice."""
    if thresholds is None:
        thresholds = np.linspace(0.05, 0.95, 19)

    best: dict[str, float] | None = None
    for threshold in thresholds:
        metrics = _classification_metrics_from_threshold(
            y_true,
            y_score,
            threshold=float(threshold),
        )
        candidate = {
            "threshold": float(threshold),
            "metric_name": metric,
            "metric_value": float(metrics.get(metric, np.nan)),
            **metrics,
        }
        if best is None:
            best = candidate
            continue
        cand_score = candidate["metric_value"]
        best_score = best["metric_value"]
        if np.isnan(best_score) or cand_score > best_score or (
            cand_score == best_score and abs(candidate["threshold"] - 0.5) < abs(best["threshold"] - 0.5)
        ):
            best = candidate

    if best is None:
        raise ValueError("Could not tune probability threshold")
    return best


def fit_recovery_classification_models(
    frame: pd.DataFrame,
    *,
    feature_cols: Sequence[str],
    target_col: str = "target_low_recovery_next_night",
    date_col: str = "calendarDate",
    split_config: TimeSplitConfig = TimeSplitConfig(),
    random_state: int = 42,
    model_names: Sequence[str] | None = None,
) -> tuple[dict[str, Pipeline], dict[str, pd.DataFrame], list[str]]:
    """Fit compact baseline classifiers and return pipelines plus contiguous splits."""
    model_frame = _prepare_model_frame(frame, feature_cols=feature_cols, target_col=target_col, date_col=date_col)
    model_frame[target_col] = pd.to_numeric(model_frame[target_col], errors="coerce").astype("Int64")
    model_frame = model_frame.dropna(subset=[target_col]).copy()
    model_frame[target_col] = model_frame[target_col].astype(int)

    splits = split_time_ordered(
        model_frame,
        date_col=date_col,
        train_frac=split_config.train_frac,
        valid_frac=split_config.valid_frac,
    )
    feature_cols_existing = _existing_feature_cols(model_frame, feature_cols)
    preprocessor = _make_preprocessor(model_frame, feature_cols_existing)

    X_train = splits["train"][feature_cols_existing]
    y_train = splits["train"][target_col]

    fitted: dict[str, Pipeline] = {}
    model_specs = _select_model_specs(_classification_model_specs(random_state), model_names)
    for model_name, estimator in model_specs.items():
        pipeline = Pipeline(
            steps=[
                ("preprocess", clone(preprocessor)),
                ("model", clone(estimator)),
            ]
        )
        pipeline.fit(X_train, y_train)
        fitted[model_name] = pipeline

    return fitted, splits, feature_cols_existing


def build_feature_importance_table(pipeline: Pipeline, *, top_n: int = 20) -> pd.DataFrame:
    """Return a feature-importance/coefficients table for fitted linear or tree models."""
    preprocess = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    feature_names = list(preprocess.get_feature_names_out())
    cleaned_names = [
        name.replace("num__", "").replace("cat__", "")
        for name in feature_names
    ]

    if hasattr(model, "coef_"):
        coef = np.ravel(model.coef_)
        out = pd.DataFrame(
            {
                "feature": cleaned_names,
                "coefficient": coef,
                "importance_abs": np.abs(coef),
                "direction": np.where(coef >= 0, "positive", "negative"),
            }
        )
        return out.sort_values("importance_abs", ascending=False).head(top_n).reset_index(drop=True)

    if hasattr(model, "feature_importances_"):
        importance = np.asarray(model.feature_importances_)
        out = pd.DataFrame(
            {
                "feature": cleaned_names,
                "importance": importance,
            }
        )
        return out.sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)

    raise ValueError(f"Model type does not expose feature importances: {type(model).__name__}")


def build_permutation_importance_table(
    pipeline: Pipeline,
    X: pd.DataFrame,
    y: pd.Series,
    *,
    top_n: int = 20,
    scoring: str = "balanced_accuracy",
    n_repeats: int = 20,
    random_state: int = 42,
) -> pd.DataFrame:
    """Return permutation importance on raw input features for estimators without native importances."""
    result = permutation_importance(
        pipeline,
        X,
        y,
        n_repeats=n_repeats,
        random_state=random_state,
        scoring=scoring,
    )
    out = pd.DataFrame(
        {
            "feature": list(X.columns),
            "importance_mean": result.importances_mean,
            "importance_std": result.importances_std,
        }
    )
    return out.sort_values("importance_mean", ascending=False).head(top_n).reset_index(drop=True)


def evaluate_recovery_classification_models(
    frame: pd.DataFrame,
    *,
    feature_cols: Sequence[str],
    target_col: str = "target_low_recovery_next_night",
    date_col: str = "calendarDate",
    split_config: TimeSplitConfig = TimeSplitConfig(),
    random_state: int = 42,
    model_names: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Evaluate compact baseline classifiers on the recovery modeling frame."""
    fitted_models, splits, feature_cols_existing = fit_recovery_classification_models(
        frame,
        feature_cols=feature_cols,
        target_col=target_col,
        date_col=date_col,
        split_config=split_config,
        random_state=random_state,
        model_names=model_names,
    )
    rows: list[dict[str, float | int | str]] = []
    for model_name, pipeline in fitted_models.items():
        for split_name, split_df in splits.items():
            X_split = split_df[feature_cols_existing]
            y_split = split_df[target_col]
            y_pred = pipeline.predict(X_split)
            y_proba = None
            if hasattr(pipeline, "predict_proba"):
                y_proba = pipeline.predict_proba(X_split)[:, 1]
            metrics = _classification_metrics(y_split, y_pred, y_proba)
            rows.append(
                {
                    "model": model_name,
                    "split": split_name,
                    "n_rows": int(len(split_df)),
                    "feature_count": int(len(feature_cols_existing)),
                    "threshold": 0.5,
                    **metrics,
                }
            )

    return pd.DataFrame(rows)


def evaluate_recovery_classification_models_tuned(
    frame: pd.DataFrame,
    *,
    feature_cols: Sequence[str],
    target_col: str = "target_low_recovery_next_night",
    date_col: str = "calendarDate",
    split_config: TimeSplitConfig = TimeSplitConfig(),
    random_state: int = 42,
    threshold_metric: str = "balanced_accuracy",
    model_names: Sequence[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Pipeline]]:
    """Evaluate classifiers after tuning a probability threshold on the validation split."""
    fitted_models, splits, feature_cols_existing = fit_recovery_classification_models(
        frame,
        feature_cols=feature_cols,
        target_col=target_col,
        date_col=date_col,
        split_config=split_config,
        random_state=random_state,
        model_names=model_names,
    )

    rows: list[dict[str, float | int | str]] = []
    for model_name, pipeline in fitted_models.items():
        X_valid = splits["valid"][feature_cols_existing]
        y_valid = splits["valid"][target_col]

        valid_proba = None
        if hasattr(pipeline, "predict_proba"):
            valid_proba = pipeline.predict_proba(X_valid)[:, 1]

        threshold_info = (
            tune_probability_threshold(y_valid, valid_proba, metric=threshold_metric)
            if valid_proba is not None
            else {
                "threshold": 0.5,
                "metric_name": threshold_metric,
                "metric_value": np.nan,
            }
        )
        threshold = float(threshold_info["threshold"])

        for split_name, split_df in splits.items():
            X_split = split_df[feature_cols_existing]
            y_split = split_df[target_col]
            split_proba = None
            split_pred = pipeline.predict(X_split)
            if hasattr(pipeline, "predict_proba"):
                split_proba = pipeline.predict_proba(X_split)[:, 1]
            metrics = _classification_metrics_from_threshold(
                y_split,
                split_proba,
                threshold=threshold,
                fallback_pred=split_pred,
            )
            rows.append(
                {
                    "model": model_name,
                    "split": split_name,
                    "n_rows": int(len(split_df)),
                    "feature_count": int(len(feature_cols_existing)),
                    "threshold": threshold,
                    "threshold_metric": threshold_metric,
                    "valid_metric_at_threshold": float(threshold_info.get("metric_value", np.nan)),
                    **metrics,
                }
            )

    return pd.DataFrame(rows), fitted_models


def forward_select_classification_features(
    frame: pd.DataFrame,
    *,
    candidate_feature_cols: Sequence[str],
    target_col: str = "target_low_recovery_next_night",
    model_name: str = "logistic_regression",
    selection_metric: str = "balanced_accuracy",
    threshold_metric: str = "balanced_accuracy",
    max_features: int | None = 8,
    min_improvement: float = 0.0,
    date_col: str = "calendarDate",
    split_config: TimeSplitConfig = TimeSplitConfig(),
    random_state: int = 42,
) -> tuple[pd.DataFrame, list[str]]:
    """Greedy forward feature selection using the validation slice of the time-ordered split."""
    available = _existing_feature_cols(frame, candidate_feature_cols)
    remaining = available.copy()
    selected: list[str] = []
    history: list[dict[str, float | int | str]] = []
    best_score = -np.inf
    step = 0

    while remaining and (max_features is None or len(selected) < max_features):
        candidates: list[dict[str, float | int | str]] = []
        for candidate in remaining:
            cols = [*selected, candidate]
            out, _ = evaluate_recovery_classification_models_tuned(
                frame,
                feature_cols=cols,
                target_col=target_col,
                date_col=date_col,
                split_config=split_config,
                random_state=random_state,
                threshold_metric=threshold_metric,
                model_names=[model_name],
            )
            valid_row = out[(out["model"] == model_name) & (out["split"] == "valid")].iloc[0]
            score = float(valid_row.get(selection_metric, np.nan))
            candidates.append(
                {
                    "candidate_feature": candidate,
                    "candidate_score": score,
                    "threshold": float(valid_row.get("threshold", np.nan)),
                    "valid_balanced_accuracy": float(valid_row.get("balanced_accuracy", np.nan)),
                    "valid_f1": float(valid_row.get("f1", np.nan)),
                    "valid_roc_auc": float(valid_row.get("roc_auc", np.nan)),
                    "valid_pr_auc": float(valid_row.get("pr_auc", np.nan)),
                    "valid_positive_rate_pred": float(valid_row.get("positive_rate_pred", np.nan)),
                }
            )

        candidate_df = pd.DataFrame(candidates).sort_values(
            ["candidate_score", "valid_roc_auc", "valid_pr_auc"],
            ascending=[False, False, False],
        )
        best_candidate = candidate_df.iloc[0]
        improvement = float(best_candidate["candidate_score"] - best_score) if np.isfinite(best_score) else np.nan

        if selected and float(best_candidate["candidate_score"]) < (best_score + min_improvement):
            break

        added_feature = str(best_candidate["candidate_feature"])
        selected.append(added_feature)
        remaining.remove(added_feature)
        step += 1
        best_score = float(best_candidate["candidate_score"])

        history.append(
            {
                "step": step,
                "model": model_name,
                "selection_metric": selection_metric,
                "added_feature": added_feature,
                "n_selected_features": len(selected),
                "selected_features": ", ".join(selected),
                "candidate_score": best_score,
                "improvement_from_prev": improvement,
                "threshold": float(best_candidate["threshold"]),
                "valid_balanced_accuracy": float(best_candidate["valid_balanced_accuracy"]),
                "valid_f1": float(best_candidate["valid_f1"]),
                "valid_roc_auc": float(best_candidate["valid_roc_auc"]),
                "valid_pr_auc": float(best_candidate["valid_pr_auc"]),
                "valid_positive_rate_pred": float(best_candidate["valid_positive_rate_pred"]),
            }
        )

    return pd.DataFrame(history), selected


def evaluate_recovery_regression_models(
    frame: pd.DataFrame,
    *,
    feature_cols: Sequence[str],
    target_col: str = "target_sleepRecoveryScore_next_night",
    date_col: str = "calendarDate",
    split_config: TimeSplitConfig = TimeSplitConfig(),
    random_state: int = 42,
    target_bounds: tuple[float, float] | None = (0.0, 100.0),
    model_names: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Evaluate compact baseline regressors on the recovery modeling frame."""
    model_frame = _prepare_model_frame(frame, feature_cols=feature_cols, target_col=target_col, date_col=date_col)
    model_frame[target_col] = pd.to_numeric(model_frame[target_col], errors="coerce")
    model_frame = model_frame.dropna(subset=[target_col]).copy()

    splits = split_time_ordered(
        model_frame,
        date_col=date_col,
        train_frac=split_config.train_frac,
        valid_frac=split_config.valid_frac,
    )
    preprocessor = _make_preprocessor(model_frame, feature_cols)

    models = _select_model_specs(_regression_model_specs(random_state), model_names)

    X_train = splits["train"][feature_cols]
    y_train = splits["train"][target_col]

    rows: list[dict[str, float | int | str]] = []
    for model_name, estimator in models.items():
        pipeline = Pipeline(
            steps=[
                ("preprocess", clone(preprocessor)),
                ("model", clone(estimator)),
            ]
        )
        pipeline.fit(X_train, y_train)

        for split_name, split_df in splits.items():
            X_split = split_df[feature_cols]
            y_split = split_df[target_col]
            y_pred = pipeline.predict(X_split)
            if target_bounds is not None:
                lo, hi = target_bounds
                y_pred = np.clip(y_pred, lo, hi)
            metrics = _regression_metrics(y_split, y_pred)
            rows.append(
                {
                    "model": model_name,
                    "split": split_name,
                    "n_rows": int(len(split_df)),
                    "feature_count": int(len(feature_cols)),
                    "target_bounds": str(target_bounds) if target_bounds is not None else "none",
                    **metrics,
                }
            )

    return pd.DataFrame(rows)
