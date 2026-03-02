from __future__ import annotations

import pandas as pd

from garmin_analytics.modeling.recovery import (
    TimeSplitConfig,
    build_confusion_table,
    build_feature_importance_table,
    build_permutation_importance_table,
    evaluate_recovery_classification_models,
    evaluate_recovery_classification_models_tuned,
    evaluate_recovery_regression_models,
    fit_recovery_classification_models,
    forward_select_classification_features,
    split_time_ordered,
    tune_probability_threshold,
)


def _sample_model_frame() -> pd.DataFrame:
    rows = []
    for i in range(20):
        rows.append(
            {
                "calendarDate": pd.Timestamp("2025-01-01") + pd.Timedelta(days=i),
                "totalSteps": 4000 + 300 * i,
                "restingHeartRate": 58 - (i % 4),
                "bodyBatteryNetBalance": -12 + i,
                "weekday_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"][i % 5],
                "target_low_recovery_next_night": 1 if i < 8 else 0,
                "target_sleepRecoveryScore_next_night": 58 + i,
            }
        )
    return pd.DataFrame(rows)


def test_split_time_ordered_returns_contiguous_blocks() -> None:
    frame = _sample_model_frame()
    splits = split_time_ordered(frame, train_frac=0.5, valid_frac=0.25)

    assert len(splits["train"]) == 10
    assert len(splits["valid"]) == 5
    assert len(splits["test"]) == 5
    assert splits["train"]["calendarDate"].max() < splits["valid"]["calendarDate"].min()
    assert splits["valid"]["calendarDate"].max() < splits["test"]["calendarDate"].min()


def test_evaluate_recovery_classification_models_runs() -> None:
    frame = _sample_model_frame()
    out = evaluate_recovery_classification_models(
        frame,
        feature_cols=["totalSteps", "restingHeartRate", "bodyBatteryNetBalance", "weekday_name"],
        split_config=TimeSplitConfig(train_frac=0.5, valid_frac=0.25),
    )

    assert set(out["model"]) == {
        "dummy_most_frequent",
        "logistic_regression",
        "logistic_regression_l1",
        "logistic_regression_elasticnet",
        "random_forest",
        "hist_gradient_boosting",
    }
    assert set(out["split"]) == {"train", "valid", "test"}
    assert {"accuracy", "balanced_accuracy", "f1", "roc_auc", "pr_auc"}.issubset(out.columns)


def test_evaluate_recovery_regression_models_runs() -> None:
    frame = _sample_model_frame()
    out = evaluate_recovery_regression_models(
        frame,
        feature_cols=["totalSteps", "restingHeartRate", "bodyBatteryNetBalance", "weekday_name"],
        split_config=TimeSplitConfig(train_frac=0.5, valid_frac=0.25),
    )

    assert set(out["model"]) == {
        "dummy_median",
        "ridge",
        "lasso",
        "elastic_net",
        "random_forest",
        "hist_gradient_boosting",
    }
    assert set(out["split"]) == {"train", "valid", "test"}
    assert {"mae", "rmse", "r2"}.issubset(out.columns)


def test_tune_probability_threshold_returns_valid_threshold() -> None:
    y_true = pd.Series([0, 0, 0, 1, 1, 1])
    y_score = [0.10, 0.20, 0.30, 0.55, 0.70, 0.90]

    tuned = tune_probability_threshold(y_true, y_score, metric="balanced_accuracy")

    assert 0.05 <= tuned["threshold"] <= 0.95
    assert tuned["metric_name"] == "balanced_accuracy"
    assert tuned["metric_value"] >= 0.5


def test_evaluate_recovery_classification_models_tuned_runs() -> None:
    frame = _sample_model_frame()
    out, fitted = evaluate_recovery_classification_models_tuned(
        frame,
        feature_cols=["totalSteps", "restingHeartRate", "bodyBatteryNetBalance", "weekday_name"],
        split_config=TimeSplitConfig(train_frac=0.5, valid_frac=0.25),
    )

    assert set(out["model"]) == {
        "dummy_most_frequent",
        "logistic_regression",
        "logistic_regression_l1",
        "logistic_regression_elasticnet",
        "random_forest",
        "hist_gradient_boosting",
    }
    assert set(out["split"]) == {"train", "valid", "test"}
    assert "threshold" in out.columns
    assert "valid_metric_at_threshold" in out.columns
    assert set(fitted.keys()) == {
        "dummy_most_frequent",
        "logistic_regression",
        "logistic_regression_l1",
        "logistic_regression_elasticnet",
        "random_forest",
        "hist_gradient_boosting",
    }


def test_build_feature_importance_table_for_logistic_pipeline() -> None:
    frame = _sample_model_frame()
    fitted, _, _ = fit_recovery_classification_models(
        frame,
        feature_cols=["totalSteps", "restingHeartRate", "bodyBatteryNetBalance", "weekday_name"],
        split_config=TimeSplitConfig(train_frac=0.5, valid_frac=0.25),
    )

    importance = build_feature_importance_table(fitted["logistic_regression"], top_n=5)

    assert not importance.empty
    assert "feature" in importance.columns
    assert "coefficient" in importance.columns
    assert len(importance) <= 5


def test_build_permutation_importance_table_runs() -> None:
    frame = _sample_model_frame()
    fitted, splits, feature_cols = fit_recovery_classification_models(
        frame,
        feature_cols=["totalSteps", "restingHeartRate", "bodyBatteryNetBalance", "weekday_name"],
        split_config=TimeSplitConfig(train_frac=0.5, valid_frac=0.25),
        model_names=["hist_gradient_boosting"],
    )

    importance = build_permutation_importance_table(
        fitted["hist_gradient_boosting"],
        splits["test"][feature_cols],
        splits["test"]["target_low_recovery_next_night"],
        top_n=4,
        n_repeats=3,
    )

    assert not importance.empty
    assert "feature" in importance.columns
    assert "importance_mean" in importance.columns
    assert len(importance) <= 4


def test_forward_select_classification_features_runs() -> None:
    frame = _sample_model_frame()
    history, selected = forward_select_classification_features(
        frame,
        candidate_feature_cols=["totalSteps", "restingHeartRate", "bodyBatteryNetBalance", "weekday_name"],
        split_config=TimeSplitConfig(train_frac=0.5, valid_frac=0.25),
        model_name="logistic_regression",
        max_features=3,
    )

    assert not history.empty
    assert len(selected) >= 1
    assert len(selected) <= 3
    assert set(selected).issubset({"totalSteps", "restingHeartRate", "bodyBatteryNetBalance", "weekday_name"})
    assert "added_feature" in history.columns
    assert "candidate_score" in history.columns


def test_build_confusion_table_counts_match_threshold() -> None:
    y_true = pd.Series([0, 0, 1, 1])
    y_score = [0.1, 0.7, 0.6, 0.9]

    table = build_confusion_table(y_true, y_score, threshold=0.5)

    assert int(table.loc[0, "tn"]) == 1
    assert int(table.loc[0, "fp"]) == 1
    assert int(table.loc[0, "fn"]) == 0
    assert int(table.loc[0, "tp"]) == 2


def test_evaluate_recovery_regression_models_reports_bounded_predictions() -> None:
    frame = _sample_model_frame()
    out = evaluate_recovery_regression_models(
        frame,
        feature_cols=["totalSteps", "restingHeartRate", "bodyBatteryNetBalance", "weekday_name"],
        split_config=TimeSplitConfig(train_frac=0.5, valid_frac=0.25),
        target_bounds=(0.0, 100.0),
    )

    assert "target_bounds" in out.columns
    assert "pred_min" in out.columns
    assert "pred_max" in out.columns
    assert bool((out["pred_min"] >= 0.0).all())
    assert bool((out["pred_max"] <= 100.0).all())
