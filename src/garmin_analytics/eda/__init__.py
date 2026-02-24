"""EDA preparation and plotting helpers.

Plotting helpers depend on optional notebook/visualization dependencies
(`matplotlib`, etc.). Import them lazily/optionally so data-prep helpers and
tests can run in minimal environments (e.g., CI test jobs) without plotting
stack installed.
"""

from .plots_common import maybe_savefig, repo_root, rolling_mean
from .prepare import (
	STRESS_TOTAL_ALIAS_MAP,
	add_derived_features,
	build_eda_frames,
	eda_readiness_summary,
	load_daily_sanitized,
	load_quality,
)
__all__ = [
	"STRESS_TOTAL_ALIAS_MAP",
	"add_derived_features",
	"build_eda_frames",
	"eda_readiness_summary",
	"load_daily_sanitized",
	"load_quality",
	"rolling_mean",
	"repo_root",
	"maybe_savefig",
]

try:
	from .sleep_plots import (
		plot_sleep_duration,
		plot_sleep_duration_scored,
		plot_sleep_intervals,
		plot_sleep_respiration,
		plot_sleep_scores,
		plot_sleep_spo2,
		plot_sleep_stage_fractions,
		plot_sleep_stage_hours,
		plot_sleep_stress,
	)
except ModuleNotFoundError as exc:
	# Allow importing `garmin_analytics.eda.prepare` and package-level EDA helpers
	# in environments without plotting deps (e.g., CI tests that don't render plots).
	if exc.name != "matplotlib":
		raise
else:
	__all__.extend(
		[
			"plot_sleep_intervals",
			"plot_sleep_duration",
			"plot_sleep_duration_scored",
			"plot_sleep_stage_fractions",
			"plot_sleep_stage_hours",
			"plot_sleep_scores",
			"plot_sleep_respiration",
			"plot_sleep_spo2",
			"plot_sleep_stress",
		]
	)
