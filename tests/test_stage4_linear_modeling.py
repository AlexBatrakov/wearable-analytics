from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from garmin_analytics.modeling.stage4 import STAGE4_PRIMARY_TARGET, STAGE4_SLEEP_START_CONTEXT_FEATURE, STAGE4_SPLIT_COLUMN
from garmin_analytics.modeling.stage4_linear import (
    RobustZClipper,
    Stage4FeatureSelectionConfig,
    Stage4LinearCandidate,
    Stage4LinearConfig,
    Stage4LinearGridSpec,
    build_stage4_linear_best_by_model_family_artifact,
    build_stage4_linear_candidate_grid,
    build_stage4_linear_experiment_plan,
    build_stage4_linear_leaderboard_slices,
    build_stage4_linear_paired_deltas,
    build_stage4_linear_shortlist,
    build_stage4_linear_summary_markdown,
    candidate_grid_frame,
    compute_stage4_linear_feature_importance,
    dummy_baseline_value,
    evaluate_dummy_baselines,
    evaluate_stage4_linear_contiguous_dev_diagnostic,
    finalize_stage4_linear_modeling,
    format_stage4_linear_experiment_plan,
    extract_stage4_linear_coefficient_table,
    fit_stage4_linear_candidate,
    make_expanding_temporal_pretest_holdouts,
    make_repeated_pretest_holdouts,
    make_stage4_linear_tuning_holdouts,
    plot_stage4_linear_prediction_diagnostics,
    plot_stage4_linear_hyperparameter_diagnostics,
    plot_stage4_linear_factor_comparisons,
    plot_stage4_linear_finalist_metric_comparison,
    plot_stage4_linear_mixed_validation_family_comparison,
    plot_stage4_linear_validation_diagnostics,
    plot_stage4_linear_rank1_feature_importance,
    predict_stage4_linear,
    prepare_stage4_linear_model_frame,
    resolve_stage4_feature_columns,
    refresh_stage4_linear_tuning_result_summaries,
    run_stage4_linear_modeling,
    select_stage4_linear_future_test_candidates,
    select_stage4_features,
    split_stage4_model_frame,
    train_feature_scores,
    tune_stage4_linear_candidates,
    tune_stage4_linear_modeling,
    stage4_linear_candidate_from_record,
    stage4_linear_experiment_budget_issues,
)


def _linear_frame(n_rows: int = 48) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    signal = np.linspace(0, 10, n_rows)
    rows = pd.DataFrame(
        {
            "analysis_window_id": [f"window_{idx:03d}" for idx in range(n_rows)],
            "calendarDate": pd.date_range("2025-01-01", periods=n_rows),
            "signal": signal,
            "noise": rng.normal(0, 1, n_rows),
            "mostly_duplicate_signal": signal + rng.normal(0, 0.01, n_rows),
            "weekday": np.tile(["Mon", "Tue", "Wed"], int(np.ceil(n_rows / 3)))[:n_rows],
            STAGE4_SLEEP_START_CONTEXT_FEATURE: np.sin(signal),
            STAGE4_PRIMARY_TARGET: 8.0 + 1.8 * signal + rng.normal(0, 0.25, n_rows),
        }
    )
    rows[STAGE4_SPLIT_COLUMN] = "train"
    rows.loc[30:39, STAGE4_SPLIT_COLUMN] = "valid"
    rows.loc[40:, STAGE4_SPLIT_COLUMN] = "test"
    rows.loc[5, "signal"] = np.nan
    rows.loc[12, "noise"] = np.nan
    return rows


def _feature_catalog() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature_set": ["toy"] * 5,
            "feature": [
                "signal",
                "noise",
                "mostly_duplicate_signal",
                "weekday",
                STAGE4_SLEEP_START_CONTEXT_FEATURE,
            ],
        }
    )


def test_resolve_stage4_feature_columns_can_exclude_schedule_context() -> None:
    catalog = _feature_catalog()

    with_schedule = resolve_stage4_feature_columns(catalog, feature_set="toy", include_schedule_context=True)
    without_schedule = resolve_stage4_feature_columns(catalog, feature_set="toy", include_schedule_context=False)

    assert STAGE4_SLEEP_START_CONTEXT_FEATURE in with_schedule
    assert STAGE4_SLEEP_START_CONTEXT_FEATURE not in without_schedule
    assert without_schedule == ["signal", "noise", "mostly_duplicate_signal", "weekday"]


def test_repeated_holdouts_use_only_pretest_history() -> None:
    frame = _linear_frame()
    feature_cols = ["signal", "noise", "weekday"]
    model_frame = prepare_stage4_linear_model_frame(frame, feature_cols)
    splits = split_stage4_model_frame(model_frame)

    holdouts = make_repeated_pretest_holdouts(splits, repeats=3, seed=7)
    test_ids = set(splits["test"]["analysis_window_id"])

    assert len(holdouts) == 3
    for holdout in holdouts:
        train_ids = set(holdout["train"]["analysis_window_id"])
        valid_ids = set(holdout["valid"]["analysis_window_id"])
        assert train_ids.isdisjoint(test_ids)
        assert valid_ids.isdisjoint(test_ids)
        assert train_ids.isdisjoint(valid_ids)
        assert len(valid_ids) == len(splits["valid"])


def test_expanding_temporal_holdouts_are_contiguous_and_use_only_past_rows() -> None:
    frame = _linear_frame()
    model_frame = prepare_stage4_linear_model_frame(frame, ["signal", "noise", "weekday"])
    splits = split_stage4_model_frame(model_frame)

    holdouts = make_expanding_temporal_pretest_holdouts(
        splits,
        repeats=3,
        validation_rows=5,
    )
    test_ids = set(splits["test"]["analysis_window_id"])

    assert [len(holdout["train"]) for holdout in holdouts] == [25, 30, 35]
    assert [len(holdout["valid"]) for holdout in holdouts] == [5, 5, 5]
    for holdout in holdouts:
        train = holdout["train"]
        valid = holdout["valid"]
        assert holdout["holdout_type"] == "temporal"
        assert set(train["analysis_window_id"]).isdisjoint(test_ids)
        assert set(valid["analysis_window_id"]).isdisjoint(test_ids)
        assert pd.to_datetime(train["calendarDate"]).max() < pd.to_datetime(valid["calendarDate"]).min()
        valid_dates = pd.to_datetime(valid["calendarDate"]).sort_values()
        assert valid_dates.diff().dropna().eq(pd.Timedelta(days=1)).all()


def test_mixed_tuning_adds_baseline_relative_metrics_and_combined_rank() -> None:
    frame = _linear_frame()
    feature_cols = ["signal", "noise", "weekday"]
    splits = split_stage4_model_frame(prepare_stage4_linear_model_frame(frame, feature_cols))
    candidates = [
        Stage4LinearCandidate(
            candidate_id=0,
            model_kind="linear",
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
        ),
        Stage4LinearCandidate(
            candidate_id=1,
            model_kind="ridge",
            alpha=10.0,
            feature_selection=Stage4FeatureSelectionConfig(mode="top_spearman", top_k=2),
        ),
    ]
    config = Stage4LinearConfig(
        holdout_strategy="mixed",
        repeated_holdout_repeats=2,
        temporal_holdout_repeats=2,
        temporal_validation_rows=5,
        shortlist_count=2,
        shortlist_min_baseline_wins=1,
    )

    holdouts = make_stage4_linear_tuning_holdouts(splits, config=config)
    repeats, summary = tune_stage4_linear_candidates(splits, feature_cols, candidates, config=config)

    assert [holdout["holdout_type"] for holdout in holdouts] == [
        "random",
        "random",
        "temporal",
        "temporal",
    ]
    assert len(repeats) == 8
    assert {"random", "temporal"} == set(repeats["holdout_type"])
    assert {
        "baseline_valid_mae",
        "valid_mae_relative_to_baseline",
        "valid_mae_skill_vs_baseline",
        "valid_mae_delta_vs_baseline",
        "valid_mae_beats_baseline",
    } <= set(repeats.columns)
    assert {
        "random_mean_train_mae",
        "random_mean_valid_mae",
        "random_mean_relative_mae",
        "random_relative_mae_std",
        "temporal_mean_train_mae",
        "temporal_mean_valid_mae",
        "temporal_mean_relative_mae",
        "temporal_worst_relative_mae",
        "combined_rank_score",
        "baseline_gate_pass",
    } <= set(summary.columns)
    assert summary["selection_metric"].eq("combined_rank_score").all()
    assert summary["selection_rank"].tolist() == [1, 2]


def test_shortlist_preserves_model_family_and_selector_representatives() -> None:
    rows = []
    candidate_id = 0
    for family_idx, model_kind in enumerate(("linear", "ridge", "lasso", "elastic_net", "huber", "pls")):
        for within_family in range(12):
            selector = ("none", "top_spearman", "top_mutual_info")[within_family % 3]
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "model_kind": model_kind,
                    "feature_selection_mode": selector,
                    "target_transform": ("none", "log1p")[within_family % 2],
                    "calibration": ("none", "linear")[within_family % 2],
                    "combined_rank_score": family_idx + within_family / 100.0,
                    "selection_metric_value": family_idx + within_family / 100.0,
                    "temporal_mean_relative_mae": 0.80 + within_family / 100.0,
                    "temporal_worst_relative_mae": 0.90 + within_family / 100.0,
                    "random_relative_mae_std": 0.01 + within_family / 1000.0,
                    "baseline_gate_pass": family_idx < 2,
                }
            )
            candidate_id += 1
    summary = pd.DataFrame(rows)
    config = Stage4LinearConfig(
        shortlist_count=40,
        shortlist_global_top_n=10,
        shortlist_model_family_top_n=5,
        shortlist_selector_top_n=1,
        shortlist_temporal_mean_top_n=3,
        shortlist_temporal_worst_top_n=3,
        shortlist_random_stability_top_n=2,
        shortlist_target_transform_top_n=2,
        shortlist_calibration_top_n=2,
    )

    shortlist = build_stage4_linear_shortlist(summary, config=config)

    assert len(shortlist) == 40
    assert set(summary.nsmallest(10, "combined_rank_score")["candidate_id"]) <= set(shortlist["candidate_id"])
    assert shortlist.loc[
        shortlist["candidate_id"].isin(summary.nsmallest(10, "combined_rank_score")["candidate_id"]),
        "shortlist_protected",
    ].all()
    family_counts = shortlist.groupby("model_kind").size()
    assert family_counts.ge(5).all()
    assert set(shortlist["feature_selection_mode"]) == {"none", "top_spearman", "top_mutual_info"}
    assert shortlist.loc[
        shortlist["shortlist_roles"].str.contains("model_family_representative"),
        "shortlist_protected",
    ].all()


def test_future_test_candidate_selection_uses_validation_rank_and_family_representatives() -> None:
    summary = pd.DataFrame(
        [
            {"candidate_id": 1, "selection_rank": 1, "model_kind": "ridge"},
            {"candidate_id": 2, "selection_rank": 2, "model_kind": "ridge"},
            {"candidate_id": 3, "selection_rank": 3, "model_kind": "huber"},
            {"candidate_id": 4, "selection_rank": 4, "model_kind": "linear"},
        ]
    )

    selected = select_stage4_linear_future_test_candidates(
        summary,
        global_top_n=2,
        model_family_top_n=1,
    )

    assert selected["candidate_id"].tolist() == [1, 2, 3, 4]
    assert "global_validation_leader" in selected.iloc[0]["future_test_selection_roles"]
    assert "model_family_validation_leader" in selected.iloc[0]["future_test_selection_roles"]
    assert selected.iloc[1]["future_test_selection_roles"] == "global_validation_leader"


def test_feature_selection_is_fit_on_train_rows_only() -> None:
    frame = _linear_frame()
    train = frame.loc[frame[STAGE4_SPLIT_COLUMN] == "train"].copy()
    valid = frame.loc[frame[STAGE4_SPLIT_COLUMN] == "valid"].copy()
    valid["valid_only_signal"] = valid[STAGE4_PRIMARY_TARGET]
    train["valid_only_signal"] = np.random.default_rng(99).normal(size=len(train))
    combined_train = train.copy()
    features = ["signal", "noise", "valid_only_signal", "weekday"]
    config = Stage4LinearConfig(feature_set="toy", target_col=STAGE4_PRIMARY_TARGET)

    scores = train_feature_scores(combined_train, features, config=config)
    selected, detail = select_stage4_features(
        combined_train,
        features,
        Stage4FeatureSelectionConfig(mode="top_spearman", top_k=1, min_features=1),
        scores=scores,
        config=config,
    )

    assert selected[0] == "signal"
    assert "valid_only_signal" not in selected
    assert detail.loc[detail["feature"] == "signal", "selected"].iloc[0]


def test_feature_scores_impute_nullable_integer_with_fractional_median() -> None:
    frame = _linear_frame(12)
    frame["nullable_integer"] = pd.Series(
        [1, 2, pd.NA, 3, 4, pd.NA, 5, 6, pd.NA, 7, 8, pd.NA],
        dtype="Int64",
    )

    scores = train_feature_scores(
        frame,
        ["nullable_integer"],
        config=Stage4LinearConfig(feature_set="toy"),
    )

    assert scores["feature"].tolist() == ["nullable_integer"]
    assert np.isfinite(scores["mutual_info_train"]).all()


def test_robust_z_clipper_fits_thresholds_from_training_values() -> None:
    clipper = RobustZClipper(z=1.0).fit(pd.DataFrame({"x": [0.0, 1.0, 2.0]}))

    transformed = clipper.transform(pd.DataFrame({"x": [100.0, -100.0]}))

    assert transformed[0, 0] < 3.0
    assert transformed[1, 0] > -2.0


def test_candidate_grid_expands_elastic_net_cartesian_product() -> None:
    spec = Stage4LinearGridSpec(
        model_kinds=("elastic_net",),
        feature_selection_modes=("none",),
        robust_clips=("none",),
        calibrations=("none",),
        target_transforms=("none",),
        prediction_clips=("0_100",),
        elastic_net_alphas=(0.01, 0.10),
        elastic_net_l1_ratios=(0.25, 0.75),
    )

    candidates = build_stage4_linear_candidate_grid(Stage4LinearConfig(), spec)
    pairs = {(candidate.alpha, candidate.l1_ratio) for candidate in candidates}

    assert len(candidates) == 4
    assert pairs == {(0.01, 0.25), (0.01, 0.75), (0.10, 0.25), (0.10, 0.75)}


def test_candidate_grid_expands_huber_cartesian_product() -> None:
    spec = Stage4LinearGridSpec(
        model_kinds=("huber",),
        feature_selection_modes=("none",),
        robust_clips=("none",),
        calibrations=("none",),
        target_transforms=("none",),
        prediction_clips=("0_100",),
        huber_alphas=(0.0001, 0.001),
        huber_epsilons=(1.20, 1.75),
    )

    candidates = build_stage4_linear_candidate_grid(Stage4LinearConfig(), spec)
    pairs = {(candidate.alpha, candidate.epsilon) for candidate in candidates}

    assert len(candidates) == 4
    assert pairs == {(0.0001, 1.20), (0.0001, 1.75), (0.001, 1.20), (0.001, 1.75)}


def test_candidate_grid_filters_enabled_model_kinds_and_audits_to_frame() -> None:
    spec = Stage4LinearGridSpec(
        model_kinds=("ridge", "pls"),
        feature_selection_modes=("none", "spearman_then_correlation"),
        top_k_values=(3, 5),
        correlation_thresholds=(0.90, 0.95),
        robust_clips=("none",),
        calibrations=("none",),
        target_transforms=("none",),
        prediction_clips=("0_100",),
        ridge_alphas=(1.0, 10.0),
        pls_components=(2,),
    )

    candidates = build_stage4_linear_candidate_grid(Stage4LinearConfig(), spec)
    audit = candidate_grid_frame(candidates)

    assert set(audit["model_kind"]) == {"ridge", "pls"}
    assert len(audit) == 15
    assert audit["candidate_id"].is_unique
    assert set(audit["feature_selection_mode"]) == {"none", "spearman_then_correlation"}
    assert {"alpha", "n_components", "feature_selection_correlation_threshold"} <= set(audit.columns)


def test_experiment_plan_counts_cartesian_grid_and_calibration_fits() -> None:
    spec = Stage4LinearGridSpec(
        model_kinds=("linear", "ridge", "elastic_net"),
        feature_selection_modes=("none", "top_spearman"),
        top_k_values=(3, 5),
        robust_clips=("none", "z=5"),
        calibrations=("none", "linear"),
        target_transforms=("none",),
        prediction_clips=("0_100",),
        ridge_alphas=(1.0, 10.0),
        elastic_net_alphas=(0.01, 0.10),
        elastic_net_l1_ratios=(0.25, 0.75),
    )
    config = Stage4LinearConfig(
        grid_source="control_panel",
        repeated_holdout_repeats=3,
        calibration_cv_folds=2,
        finalist_count=5,
    )
    candidates = build_stage4_linear_candidate_grid(config, spec)

    plan = build_stage4_linear_experiment_plan(config, candidates, feature_columns=["a", "b"])
    text = format_stage4_linear_experiment_plan(plan)

    assert plan["feature_selector_config_count"] == 3
    assert plan["model_config_count"] == 7
    assert plan["preprocessing_multiplier"] == 2
    assert plan["calibration_variant_count"] == 2
    assert plan["candidate_count"] == 84
    assert plan["split_evaluations"] == 252
    assert plan["calibration_inner_fits"] == 252
    assert plan["approximate_base_fits"] == 504
    assert "Experiment plan" in text
    assert "elastic_net: 4" in text


def test_experiment_budget_issues_reports_only_exceeded_limits() -> None:
    plan = {
        "candidate_count": 25_020,
        "approximate_tuning_fits": 82_566,
    }

    assert stage4_linear_experiment_budget_issues(
        plan,
        max_candidates=30_000,
        max_approximate_tuning_fits=150_000,
    ) == []
    assert stage4_linear_experiment_budget_issues(
        plan,
        max_candidates=20_000,
        max_approximate_tuning_fits=80_000,
    ) == [
        "candidates: 25,020 exceeds safety budget 20,000",
        "approximate tuning fits: 82,566 exceeds safety budget 80,000",
    ]


def test_candidate_can_be_rebuilt_from_leaderboard_record() -> None:
    record = {
        "candidate_id": 42,
        "model_kind": "huber",
        "feature_selection_mode": "top_spearman",
        "feature_selection_top_k": 90,
        "feature_selection_min_features": 8,
        "robust_clip": "z=4",
        "calibration": "linear",
        "target_transform": "none",
        "prediction_clip": "0_100",
        "alpha": 30.0,
        "epsilon": 1.15,
        "fit_intercept": True,
        "max_iter": 500_000,
        "tol": 1e-4,
    }

    candidate = stage4_linear_candidate_from_record(record)

    assert candidate.candidate_id == 42
    assert candidate.model_kind == "huber"
    assert candidate.feature_selection.mode == "top_spearman"
    assert candidate.feature_selection.top_k == 90
    assert candidate.alpha == 30.0
    assert candidate.epsilon == 1.15


def test_coefficient_table_maps_pipeline_coefficients_to_source_features() -> None:
    frame = _linear_frame()
    train = frame.loc[frame[STAGE4_SPLIT_COLUMN] == "train"].reset_index(drop=True)
    candidate = Stage4LinearCandidate(
        candidate_id=0,
        model_kind="ridge",
        alpha=1.0,
        feature_selection=Stage4FeatureSelectionConfig(mode="none"),
    )

    fitted = fit_stage4_linear_candidate(
        train,
        ["signal", "noise", "weekday"],
        candidate,
        config=Stage4LinearConfig(),
    )
    coefficients = extract_stage4_linear_coefficient_table(fitted)

    assert {"feature", "standardized_coefficient", "abs_standardized_coefficient"} <= set(coefficients.columns)
    assert "signal" in set(coefficients["feature"])
    assert coefficients["coefficient_available"].all()


def test_feature_importance_uses_validation_not_future_test() -> None:
    frame = _linear_frame()
    feature_cols = ["signal", "noise", "weekday"]
    splits = split_stage4_model_frame(prepare_stage4_linear_model_frame(frame, feature_cols))
    candidate = Stage4LinearCandidate(
        candidate_id=0,
        model_kind="ridge",
        alpha=1.0,
        feature_selection=Stage4FeatureSelectionConfig(mode="none"),
    )
    config = Stage4LinearConfig(calibration_cv_folds=2, calibration_min_rows=12)

    original = compute_stage4_linear_feature_importance(
        splits,
        feature_cols,
        candidate,
        config=config,
        permutation_repeats=2,
        random_state=77,
    )
    changed_splits = {name: split.copy() for name, split in splits.items()}
    changed_splits["test"][STAGE4_PRIMARY_TARGET] = changed_splits["test"][STAGE4_PRIMARY_TARGET] + 10_000
    changed = compute_stage4_linear_feature_importance(
        changed_splits,
        feature_cols,
        candidate,
        config=config,
        permutation_repeats=2,
        random_state=77,
    )

    pd.testing.assert_frame_equal(original, changed)
    assert set(original["permutation_eval_split"]) == {"valid"}
    assert set(original["coefficient_fit_source"]) == {"final_refit_pretest"}


def test_feature_importance_plot_has_coefficient_and_permutation_panels() -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    importance = pd.DataFrame(
        {
            "feature": ["a", "b", "c"],
            "standardized_coefficient": [0.4, -0.2, 0.1],
            "abs_standardized_coefficient": [0.4, 0.2, 0.1],
            "permutation_mae_increase_mean": [0.3, 0.1, 0.5],
            "permutation_mae_increase_std": [0.05, 0.02, 0.01],
            "rank": [1, 2, 3],
        }
    )

    figure = plot_stage4_linear_rank1_feature_importance(importance, top_n=2)

    assert len(figure.axes) == 2
    assert figure.axes[0].get_title() == "Dev-Refit Coefficients: Top Absolute Effects"
    assert figure.axes[1].get_title() == "Contiguous Validation Permutation Importance"
    assert {label.get_text() for label in figure.axes[0].get_yticklabels()} == {"a", "b"}
    assert {label.get_text() for label in figure.axes[1].get_yticklabels()} == {"a", "c"}
    plt.close(figure)


def test_best_by_model_family_artifact_keeps_validation_selection() -> None:
    validation = pd.DataFrame(
        [
            {
                "candidate_id": 1,
                "selection_rank": 2,
                "model_kind": "linear",
                "feature_selection_mode": "none",
                "robust_clip": "none",
                "calibration": "none",
                "mean_valid_mae": 4.0,
                "std_valid_mae": 0.2,
                "mean_valid_r2": 0.1,
                "mean_valid_spearman": 0.2,
            },
            {
                "candidate_id": 2,
                "selection_rank": 1,
                "model_kind": "ridge",
                "alpha": 10.0,
                "feature_selection_mode": "top_spearman",
                "feature_selection_top_k": 3,
                "robust_clip": "z=5",
                "calibration": "none",
                "mean_valid_mae": 3.5,
                "std_valid_mae": 0.1,
                "mean_valid_r2": 0.3,
                "mean_valid_spearman": 0.5,
            },
            {
                "candidate_id": 3,
                "selection_rank": 3,
                "model_kind": "ridge",
                "alpha": 1.0,
                "feature_selection_mode": "none",
                "robust_clip": "none",
                "calibration": "none",
                "mean_valid_mae": 3.7,
                "std_valid_mae": 0.1,
                "mean_valid_r2": 0.2,
                "mean_valid_spearman": 0.4,
            },
        ]
    )
    dummy = pd.DataFrame(
        [
            {
                "model_kind": "dummy_mean",
                "mean_valid_mae": 4.8,
                "std_valid_mae": 0.3,
                "mean_valid_r2": -0.1,
            }
        ]
    )
    leaderboard = pd.DataFrame(
        [
            {"candidate_type": "linear_family", "candidate_id": 2, "test_mae": 5.2, "test_r2": 0.25},
            {"candidate_type": "dummy", "model_kind": "dummy_mean", "test_mae": 6.1, "test_r2": -0.2},
        ]
    )

    artifact = build_stage4_linear_best_by_model_family_artifact(validation, dummy, leaderboard)

    assert artifact["candidate_type"].tolist() == ["linear_family", "linear_family", "dummy"]
    assert artifact["model_kind"].tolist() == ["ridge", "linear", "dummy_mean"]
    assert artifact.loc[artifact["model_kind"].eq("ridge"), "test_mae"].iloc[0] == 5.2
    assert np.isnan(artifact.loc[artifact["model_kind"].eq("linear"), "test_mae"].iloc[0])
    assert artifact.loc[artifact["model_kind"].eq("dummy_mean"), "test_mae"].iloc[0] == 6.1


def test_control_panel_grid_source_requires_explicit_grid() -> None:
    config = Stage4LinearConfig(
        feature_set="toy",
        grid_source="control_panel",
        repeated_holdout_repeats=1,
    )

    with pytest.raises(ValueError, match="Explicit candidates or grid_spec"):
        run_stage4_linear_modeling(_linear_frame(), _feature_catalog(), config=config)


def test_paired_deltas_match_otherwise_identical_candidates() -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    spec = Stage4LinearGridSpec(
        model_kinds=("ridge",),
        feature_selection_modes=("none", "top_spearman"),
        top_k_values=(3,),
        robust_clips=("none", "z=5"),
        calibrations=("none", "linear"),
        target_transforms=("none",),
        prediction_clips=("0_100",),
        ridge_alphas=(1.0,),
    )
    grid = candidate_grid_frame(build_stage4_linear_candidate_grid(Stage4LinearConfig(), spec))
    grid["mean_valid_mae"] = np.arange(len(grid), dtype=float)

    calibration = build_stage4_linear_paired_deltas(grid, factor="calibration", reference="none")
    clipping = build_stage4_linear_paired_deltas(grid, factor="robust_clip", reference="none")
    selectors = build_stage4_linear_paired_deltas(grid, factor="feature_selection", reference="none")

    assert len(calibration) == 4
    assert len(clipping) == 4
    assert len(selectors) == 4
    assert set(calibration["factor_value"]) == {"linear"}
    assert set(clipping["factor_value"]) == {"z=5"}
    assert set(selectors["factor_value"]) == {"top_spearman_3"}
    figures = plot_stage4_linear_factor_comparisons(grid)
    assert set(figures) == {
        "calibration_comparison",
        "feature_selection_distribution",
        "feature_selection_paired_delta",
        "robust_clipping_comparison",
    }
    assert (
        figures["robust_clipping_comparison"].axes[0].get_title()
        == "Robust Clipping Paired Delta Distributions"
    )
    assert figures["feature_selection_distribution"].axes[0].get_ylabel() == "Feature selector"
    assert figures["feature_selection_paired_delta"].axes[0].get_ylabel() == "Feature selector"
    for figure in figures.values():
        plt.close(figure)


def test_feature_selector_boxplots_color_configs_by_selector_family() -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_hex

    spec = Stage4LinearGridSpec(
        model_kinds=("ridge",),
        feature_selection_modes=("none", "top_spearman", "top_mutual_info"),
        top_k_values=(3, 5),
        robust_clips=("none",),
        calibrations=("none",),
        target_transforms=("none",),
        prediction_clips=("0_100",),
        ridge_alphas=(1.0, 10.0),
    )
    grid = candidate_grid_frame(build_stage4_linear_candidate_grid(Stage4LinearConfig(), spec))
    grid["mean_valid_mae"] = np.linspace(4.0, 5.0, len(grid))

    figure = plot_stage4_linear_factor_comparisons(grid)["feature_selection_distribution"]
    axis = figure.axes[0]
    color_by_label = {
        tick.get_text(): to_hex(patch.get_facecolor(), keep_alpha=False)
        for tick, patch in zip(axis.get_yticklabels(), axis.patches)
    }

    assert color_by_label["top_spearman_3"] == color_by_label["top_spearman_5"]
    assert color_by_label["top_mutual_info_3"] == color_by_label["top_mutual_info_5"]
    assert color_by_label["top_spearman_3"] != color_by_label["top_mutual_info_3"]
    assert color_by_label["none"] != color_by_label["top_spearman_3"]
    assert {
        text.get_text() for text in axis.get_legend().get_texts()
    } == {"none", "top spearman", "top mutual info"}
    plt.close(figure)


def test_validation_diagnostics_include_balanced_top_candidates_by_model_family() -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    spec = Stage4LinearGridSpec(
        model_kinds=("linear", "ridge", "huber"),
        feature_selection_modes=("none",),
        robust_clips=("none",),
        calibrations=("none",),
        target_transforms=("none",),
        prediction_clips=("0_100",),
        ridge_alphas=(0.1, 1.0, 10.0, 100.0, 1000.0),
        huber_alphas=(0.0001, 0.001, 0.01),
        huber_epsilons=(1.1, 1.35, 1.75),
    )
    summary = candidate_grid_frame(build_stage4_linear_candidate_grid(Stage4LinearConfig(), spec))
    family_offsets = {"huber": 0.0, "ridge": 1.0, "linear": 2.0}
    family_sequence = summary.groupby("model_kind").cumcount().astype(float)
    summary["mean_valid_mae"] = summary["model_kind"].map(family_offsets) + family_sequence * 0.01
    summary["std_valid_mae"] = 0.05
    summary["mean_train_mae"] = summary["mean_valid_mae"] - 0.10
    summary["mean_train_rmse"] = summary["mean_train_mae"] + 0.20
    summary["mean_valid_rmse"] = summary["mean_valid_mae"] + 0.20
    summary["mean_train_r2"] = 0.30
    summary["mean_valid_r2"] = 0.20
    summary["mean_selected_feature_count"] = 10.0
    dummy = pd.DataFrame(
        [
            {
                "model_kind": "dummy_median",
                "mean_train_mae": 2.2,
                "mean_valid_mae": 2.3,
                "mean_train_rmse": 2.5,
                "mean_valid_rmse": 2.6,
                "mean_train_r2": 0.0,
                "mean_valid_r2": -0.1,
                "std_valid_mae": 0.1,
            }
        ]
    )

    figures = plot_stage4_linear_validation_diagnostics(
        summary,
        dummy,
        top_n=5,
        top_per_model_family=3,
    )

    assert len(figures["top_candidates"].axes[0].patches) == 5
    assert len(figures["top_candidates_by_model_family"].axes[0].patches) == 7
    if len(figures["top_candidates_by_model_family"].axes) > 1:
        assert not any(
            label.get_visible()
            for label in figures["top_candidates_by_model_family"].axes[1].get_yticklabels()
        )
    for figure in figures.values():
        plt.close(figure)


def test_hyperparameter_heatmaps_are_bounded_for_wide_grids() -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    spec = Stage4LinearGridSpec(
        model_kinds=("elastic_net", "huber"),
        feature_selection_modes=("none",),
        robust_clips=("none",),
        calibrations=("none",),
        target_transforms=("none",),
        prediction_clips=("0_100",),
        elastic_net_alphas=tuple(np.logspace(-4, 1, 12)),
        elastic_net_l1_ratios=tuple(np.linspace(0.05, 0.95, 11)),
        huber_alphas=tuple(np.logspace(-4, 1, 10)),
        huber_epsilons=tuple(np.linspace(1.1, 2.0, 10)),
    )
    summary = candidate_grid_frame(build_stage4_linear_candidate_grid(Stage4LinearConfig(), spec))
    summary["mean_valid_mae"] = np.linspace(4.0, 6.0, len(summary))

    figures = plot_stage4_linear_hyperparameter_diagnostics(summary)

    assert set(figures) == {
        "elastic_net_alpha",
        "elastic_net_l1_ratio",
        "elastic_net",
        "huber_alpha",
        "huber_epsilon",
        "huber",
    }
    for figure in figures.values():
        width, height = figure.get_size_inches()
        assert width <= 10.0
        assert height <= 7.0
        plt.close(figure)


def test_tuning_phase_is_separate_from_finalist_refit() -> None:
    candidates = [
        Stage4LinearCandidate(
            candidate_id=0,
            model_kind="linear",
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
        ),
        Stage4LinearCandidate(
            candidate_id=1,
            model_kind="ridge",
            alpha=1.0,
            feature_selection=Stage4FeatureSelectionConfig(mode="top_spearman", top_k=2),
        ),
    ]
    config = Stage4LinearConfig(
        feature_set="toy",
        grid_source="control_panel",
        repeated_holdout_repeats=1,
        finalist_count=1,
    )

    tuning_result = tune_stage4_linear_modeling(
        _linear_frame(),
        _feature_catalog(),
        config=config,
        candidates=candidates,
    )

    assert not hasattr(tuning_result, "final_metrics")
    assert set(tuning_result.validation_slices) == {
        "overall_validation",
        "best_by_model_kind",
        "best_by_model_kind_feature_selection",
        "dummy_validation",
    }
    overall = tuning_result.validation_slices["overall_validation"]
    assert {
        "mean_train_mae",
        "mean_train_rmse",
        "mean_train_r2",
        "mean_valid_mae",
        "std_valid_mae",
        "model_param_1",
        "feature_selection_param_1",
        "candidate_short_label",
    } <= set(overall.columns)
    assert overall.loc[overall["model_kind"].eq("ridge"), "model_param_1"].iloc[0] == "alpha=1"

    selected = select_stage4_linear_future_test_candidates(
        tuning_result.tuning_summary,
        global_top_n=1,
        model_family_top_n=1,
    )
    result = finalize_stage4_linear_modeling(
        tuning_result,
        finalist_candidate_ids=selected["candidate_id"].tolist(),
    )
    assert len(result.final_metrics.query("split == 'test'")) == len(selected)
    assert set(result.final_metrics["split"]) == {"dev", "test"}


def test_refresh_tuning_result_reaggregates_stored_holdouts_without_changing_repeats() -> None:
    config = Stage4LinearConfig(
        feature_set="toy",
        holdout_strategy="mixed",
        repeated_holdout_repeats=1,
        temporal_holdout_repeats=1,
        temporal_validation_rows=5,
    )
    candidates = [
        Stage4LinearCandidate(
            candidate_id=0,
            model_kind="ridge",
            alpha=1.0,
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
        )
    ]
    tuning_result = tune_stage4_linear_modeling(
        _linear_frame(),
        _feature_catalog(),
        config=config,
        candidates=candidates,
    )
    original_repeats = tuning_result.tuning_repeats.copy()
    tuning_result.tuning_summary = tuning_result.tuning_summary.drop(
        columns=["temporal_mean_train_mae", "random_mean_train_mae"]
    )

    refreshed = refresh_stage4_linear_tuning_result_summaries(tuning_result)

    pd.testing.assert_frame_equal(refreshed.tuning_repeats, original_repeats)
    assert {"temporal_mean_train_mae", "random_mean_train_mae"} <= set(refreshed.tuning_summary.columns)
    assert {"temporal_mean_train_mae", "random_mean_train_mae"} <= set(refreshed.dummy_tuning_summary.columns)


def test_contiguous_dev_diagnostic_uses_only_dev_rows() -> None:
    frame = _linear_frame()
    feature_cols = ["signal", "noise", "weekday"]
    splits = split_stage4_model_frame(prepare_stage4_linear_model_frame(frame, feature_cols))
    candidate = Stage4LinearCandidate(
        candidate_id=0,
        model_kind="ridge",
        alpha=1.0,
        feature_selection=Stage4FeatureSelectionConfig(mode="none"),
    )

    metrics, predictions = evaluate_stage4_linear_contiguous_dev_diagnostic(
        splits,
        feature_cols,
        candidate,
        config=Stage4LinearConfig(calibration_cv_folds=2, calibration_min_rows=12),
    )

    assert metrics["split"].tolist() == ["dev_train", "dev_valid", "dev_test"]
    assert set(predictions["split"]) == {"dev_train", "dev_valid", "dev_test"}
    assert set(predictions["analysis_window_id"]).isdisjoint(set(splits["test"]["analysis_window_id"]))
    ordered = predictions.sort_values("calendarDate")
    assert ordered["split"].drop_duplicates().tolist() == ["dev_train", "dev_valid", "dev_test"]


def test_parallel_tuning_matches_serial_tuning() -> None:
    frame = _linear_frame()
    feature_cols = ["signal", "noise", "weekday"]
    splits = split_stage4_model_frame(prepare_stage4_linear_model_frame(frame, feature_cols))
    candidates = [
        Stage4LinearCandidate(
            candidate_id=0,
            model_kind="linear",
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
        ),
        Stage4LinearCandidate(
            candidate_id=1,
            model_kind="ridge",
            alpha=1.0,
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
        ),
    ]
    serial_config = Stage4LinearConfig(repeated_holdout_repeats=1, n_jobs=1)
    parallel_config = Stage4LinearConfig(
        repeated_holdout_repeats=1,
        n_jobs=2,
        parallel_backend="threading",
    )

    _, serial = tune_stage4_linear_candidates(splits, feature_cols, candidates, config=serial_config)
    _, parallel = tune_stage4_linear_candidates(splits, feature_cols, candidates, config=parallel_config)

    pd.testing.assert_frame_equal(serial, parallel)


@pytest.mark.parametrize(
    ("n_jobs", "parallel_backend"),
    [(1, "loky"), (2, "threading")],
)
def test_tuning_progress_callback_reports_completed_candidate_evaluations(
    n_jobs: int,
    parallel_backend: str,
) -> None:
    frame = _linear_frame()
    feature_cols = ["signal", "noise", "weekday"]
    splits = split_stage4_model_frame(prepare_stage4_linear_model_frame(frame, feature_cols))
    candidates = [
        Stage4LinearCandidate(
            candidate_id=0,
            model_kind="linear",
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
        ),
        Stage4LinearCandidate(
            candidate_id=1,
            model_kind="ridge",
            alpha=1.0,
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
        ),
    ]
    progress: list[tuple[int, int]] = []

    tune_stage4_linear_candidates(
        splits,
        feature_cols,
        candidates,
        config=Stage4LinearConfig(
            repeated_holdout_repeats=2,
            n_jobs=n_jobs,
            parallel_backend=parallel_backend,
        ),
        progress_callback=lambda completed, total: progress.append((completed, total)),
    )

    assert progress == [(completed, 4) for completed in range(5)]


def test_stage4_linear_candidate_supports_categorical_features() -> None:
    frame = _linear_frame()
    train = frame.loc[frame[STAGE4_SPLIT_COLUMN] == "train"].reset_index(drop=True)
    candidate = Stage4LinearCandidate(
        candidate_id=0,
        model_kind="ridge",
        alpha=1.0,
        feature_selection=Stage4FeatureSelectionConfig(mode="none"),
        robust_clip="z=4",
        calibration="linear",
    )
    config = Stage4LinearConfig(calibration_cv_folds=3, calibration_min_rows=12)

    fitted = fit_stage4_linear_candidate(train, ["signal", "weekday"], candidate, config=config)
    pred = predict_stage4_linear(fitted, train.head(5))

    assert len(pred) == 5
    assert np.isfinite(pred).all()
    assert fitted.calibration_record["calibration"] == "linear"


def test_tuning_does_not_change_when_future_test_targets_change() -> None:
    frame = _linear_frame()
    feature_cols = ["signal", "noise", "weekday"]
    model_frame = prepare_stage4_linear_model_frame(frame, feature_cols)
    splits = split_stage4_model_frame(model_frame)
    candidates = [
        Stage4LinearCandidate(
            candidate_id=0,
            model_kind="linear",
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
            calibration="none",
        ),
        Stage4LinearCandidate(
            candidate_id=1,
            model_kind="ridge",
            alpha=10.0,
            feature_selection=Stage4FeatureSelectionConfig(mode="top_spearman", top_k=2),
            robust_clip="z=5",
            calibration="linear",
        ),
    ]
    config = Stage4LinearConfig(repeated_holdout_repeats=2, calibration_cv_folds=2, calibration_min_rows=12)

    _, original_summary = tune_stage4_linear_candidates(splits, feature_cols, candidates, config=config)
    changed_splits = {name: split.copy() for name, split in splits.items()}
    changed_splits["test"][STAGE4_PRIMARY_TARGET] = changed_splits["test"][STAGE4_PRIMARY_TARGET] + 10_000
    _, changed_summary = tune_stage4_linear_candidates(changed_splits, feature_cols, candidates, config=config)

    pd.testing.assert_frame_equal(original_summary, changed_summary)


def test_run_stage4_linear_modeling_returns_finalist_and_dummy_leaderboard() -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    frame = _linear_frame()
    catalog = _feature_catalog()
    candidates = [
        Stage4LinearCandidate(
            candidate_id=0,
            model_kind="linear",
            feature_selection=Stage4FeatureSelectionConfig(mode="none"),
            calibration="none",
        ),
        Stage4LinearCandidate(
            candidate_id=1,
            model_kind="ridge",
            alpha=1.0,
            feature_selection=Stage4FeatureSelectionConfig(mode="spearman_then_correlation", top_k=3),
            robust_clip="z=4",
            calibration="none",
        ),
    ]
    config = Stage4LinearConfig(
        feature_set="toy",
        repeated_holdout_repeats=2,
        finalist_count=1,
        calibration_cv_folds=2,
        calibration_min_rows=12,
    )

    result = run_stage4_linear_modeling(frame, catalog, config=config, candidates=candidates)
    test_metrics = result.final_metrics.loc[result.final_metrics["split"] == "test"]
    dummy_test = result.dummy_metrics.loc[result.dummy_metrics["split"] == "test"]
    slices = build_stage4_linear_leaderboard_slices(
        result.tuning_summary,
        result.final_metrics,
        result.dummy_tuning_summary,
        result.dummy_metrics,
    )

    assert len(result.candidate_grid) == 2
    assert len(test_metrics) == 1
    assert set(dummy_test["model_kind"]) == {"dummy_mean", "dummy_median", "dummy_last"}
    assert set(result.final_metrics["split"]) == {"dev", "test"}
    assert set(result.dummy_metrics["split"]) == {"dev", "test"}
    assert "test_mae" in result.leaderboard.columns
    assert set(result.leaderboard_slices) == {
        "overall_validation",
        "best_by_model_kind",
        "best_by_model_kind_feature_selection",
        "dummy_baselines",
        "final_future_test",
    }
    assert set(slices["best_by_model_kind"]["model_kind"]) == {"linear", "ridge"}
    assert "test_mae" in slices["dummy_baselines"].columns
    assert result.feature_selection_detail["candidate_id"].nunique() == 1
    assert result.final_predictions["prediction_provenance"].str.contains("final_refit").any()
    fig = plot_stage4_linear_prediction_diagnostics(result.final_predictions)
    assert len(fig.axes) == 4
    plt.close(fig)
    finalist_metric_fig = plot_stage4_linear_finalist_metric_comparison(
        result.final_metrics,
        result.dummy_metrics,
        baseline_strategy=config.baseline_strategy,
    )
    assert len(finalist_metric_fig.axes) == 3
    plt.close(finalist_metric_fig)
    validation_figures = plot_stage4_linear_validation_diagnostics(
        result.tuning_summary,
        result.dummy_tuning_summary,
        top_n=2,
    )
    assert {
        "validation_mae_distribution",
        "top_candidates",
        "top_candidates_by_model_family",
        "best_by_model_family",
        "model_family_distribution",
        "train_validation_gap",
        "performance_stability",
    } <= set(validation_figures)
    for validation_fig in validation_figures.values():
        plt.close(validation_fig)
    mixed_result = tune_stage4_linear_modeling(
        frame,
        catalog,
        config=Stage4LinearConfig(
            feature_set="toy",
            holdout_strategy="mixed",
            repeated_holdout_repeats=1,
            temporal_holdout_repeats=1,
            temporal_validation_rows=5,
            calibration_cv_folds=2,
            calibration_min_rows=12,
        ),
        candidates=candidates,
    )
    mixed_family_fig = plot_stage4_linear_mixed_validation_family_comparison(
        mixed_result.tuning_summary,
        mixed_result.dummy_tuning_summary,
    )
    assert len(mixed_family_fig.axes) == 2
    plt.close(mixed_family_fig)
    mixed_validation_figures = plot_stage4_linear_validation_diagnostics(
        mixed_result.tuning_summary,
        mixed_result.dummy_tuning_summary,
        top_n=2,
    )
    assert "random_vs_temporal" in mixed_validation_figures
    assert "feature_selector_distribution" not in mixed_validation_figures
    assert len(mixed_validation_figures["validation_mae_distribution"].axes) == 2
    assert len(mixed_validation_figures["performance_stability"].axes) == 2
    assert not any(
        label.get_visible()
        for label in mixed_validation_figures["top_candidates_by_model_family"].axes[1].get_yticklabels()
    )
    assert all(
        axis.collections
        for axis in mixed_validation_figures["top_candidates_by_model_family"].axes
    )
    for mixed_validation_fig in mixed_validation_figures.values():
        plt.close(mixed_validation_fig)
    hyperparameter_figures = plot_stage4_linear_hyperparameter_diagnostics(result.tuning_summary)
    assert "ridge" in hyperparameter_figures
    for hyperparameter_fig in hyperparameter_figures.values():
        plt.close(hyperparameter_fig)
    assert dummy_baseline_value(
        pd.concat([split_stage4_model_frame(prepare_stage4_linear_model_frame(frame, ["signal"]))["train"],
                   split_stage4_model_frame(prepare_stage4_linear_model_frame(frame, ["signal"]))["valid"]]),
        "dummy_last",
        target_col=STAGE4_PRIMARY_TARGET,
    ) == evaluate_dummy_baselines(split_stage4_model_frame(prepare_stage4_linear_model_frame(frame, ["signal"])), config=config)[0].query(
        "model_kind == 'dummy_last' and split == 'test'"
    )["baseline_value"].iloc[0]

    result.dummy_metrics.loc[
        result.dummy_metrics["split"].eq("test") & result.dummy_metrics["model_kind"].eq("dummy_mean"),
        "mae",
    ] = 0.1
    result.dummy_metrics.loc[
        result.dummy_metrics["split"].eq("test") & result.dummy_metrics["model_kind"].eq("dummy_median"),
        "mae",
    ] = 10.0
    selected_model_test_mae = float(
        result.final_metrics.loc[
            result.final_metrics["split"].eq("test")
            & result.final_metrics["validation_selection_rank"].eq(1),
            "mae",
        ].iloc[0]
    )
    summary_text = build_stage4_linear_summary_markdown(result)
    assert "- Comparison baseline selected before fixed-future-holdout evaluation: `dummy_median`" in summary_text
    assert f"improved fixed-future-holdout MAE by `{10.0 - selected_model_test_mae:.3f}` points" in summary_text
    assert "versus the preselected `dummy_median` baseline" in summary_text
