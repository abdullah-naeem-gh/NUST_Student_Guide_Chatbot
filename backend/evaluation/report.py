"""Generate a markdown evaluation report from experiment JSON outputs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings


def _utc_now_iso() -> str:
    """Return current UTC time as ISO string."""

    return datetime.now(timezone.utc).isoformat()


def _load(path: Path) -> dict[str, Any]:
    """Load JSON from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(x: float, nd: int = 4) -> str:
    """Format a float for tables."""

    return f"{float(x):.{nd}f}"


def generate_report() -> Path:
    """
    Generate `data/results/REPORT.md` from latest experiment outputs.

    Returns:
        Path to written report.
    """

    results_dir = settings.DATA_DIR / "results"
    mc_path = results_dir / "method_comparison.json"
    ps_path = results_dir / "parameter_sensitivity.json"
    sc_path = results_dir / "scalability.json"

    parts: list[str] = []
    parts.append(f"# Evaluation Report\n\nGenerated at `{_utc_now_iso()}`.\n")

    if mc_path.exists():
        mc = _load(mc_path)
        s = mc.get("summary", {})
        parts.append("## Method comparison (15 benchmark queries)\n")
        parts.append("| Method | Mean P@1 | Mean P@3 | **Mean P@5** | Mean R@5 | MAP@5 | Mean latency (ms) |\n")
        parts.append("|---|---:|---:|---:|---:|---:|---:|\n")
        for m in ("minhash", "minhash_lsh_only", "simhash", "tfidf"):
            row = s.get(m, {})
            parts.append(
                f"| {m} | {_fmt(row.get('mean_p@1', 0))} | {_fmt(row.get('mean_p@3', 0))} | **{_fmt(row.get('mean_p@5', 0))}** | {_fmt(row.get('mean_r@5', 0))} | {_fmt(row.get('map@5', 0))} | {_fmt(row.get('mean_latency_ms', 0), 2)} |\n"
            )
        parts.append("\n")

        parts.append("## Decisions / rationale\n\n")
        parts.append(
            "- **TF-IDF (baseline)**: kept default params (`ngram_max=2`, `min_df=2`, `max_df=0.85`, `max_features=20000`) because it achieved the best MAP@5 among the sweep candidates with low latency.\n"
            "- **MinHash**: tuned to `k=1` word shingles and `bands=128, rows=1` (still `num_perm=128`) to make LSH non-empty for short QA queries. System uses **MinHash+LSH** with explicit **TF-IDF fallback** when LSH returns zero candidates (reported as `fallback_rate`). The report also includes a **MinHash+LSH-only** row to show approximate behavior without fallback.\n"
            "- **SimHash**: kept baseline tokenization (unigrams, stopword removal); threshold sweep still prefers smaller thresholds.\n"
        )
        parts.append("\n")
    else:
        parts.append("## Method comparison\n\n`method_comparison.json` not found.\n\n")

    if ps_path.exists():
        ps = _load(ps_path)
        parts.append("## Parameter sensitivity\n")

        parts.append("### MinHash: NUM_PERM sweep\n")
        parts.append("| NUM_PERM | Mean Recall@5 | Mean latency (ms) | Build time (s) |\n")
        parts.append("|---:|---:|---:|---:|\n")
        for r in ps.get("minhash", []):
            parts.append(
                f"| {int(r['num_perm'])} | {_fmt(r['mean_recall@5'])} | {_fmt(r['mean_latency_ms'], 2)} | {_fmt(r['build_time_s'], 2)} |\n"
            )
        parts.append("\n")

        parts.append("### LSH: NUM_BANDS sweep\n")
        parts.append("| NUM_BANDS | Rows/band | Mean Recall@5 |\n")
        parts.append("|---:|---:|---:|\n")
        for r in ps.get("lsh", []):
            parts.append(
                f"| {int(r['num_bands'])} | {int(r['rows_per_band'])} | {_fmt(r['mean_recall@5'])} |\n"
            )
        parts.append("\n")

        parts.append("### SimHash: Hamming threshold sweep\n")
        parts.append("| Threshold | Mean Precision@5 |\n")
        parts.append("|---:|---:|\n")
        for r in ps.get("simhash", []):
            parts.append(
                f"| {int(r['hamming_threshold'])} | {_fmt(r['mean_precision@5'])} |\n"
            )
        parts.append("\n")
    else:
        parts.append("## Parameter sensitivity\n\n`parameter_sensitivity.json` not found.\n\n")

    if sc_path.exists():
        sc = _load(sc_path)
        parts.append("## Scalability\n")
        parts.append("| Scale | Chunk count | Build time (s) | TF-IDF lat (ms) | MinHash lat (ms) | SimHash lat (ms) |\n")
        parts.append("|---:|---:|---:|---:|---:|---:|\n")
        for p in sc.get("points", []):
            lat = p.get("mean_query_latency_ms", {}) if isinstance(p.get("mean_query_latency_ms", {}), dict) else {}
            parts.append(
                f"| {int(p['scale'])}x | {int(p['chunk_count'])} | {_fmt(p['build_time_s'], 2)} | {_fmt(lat.get('tfidf', 0.0), 2)} | {_fmt(lat.get('minhash', 0.0), 2)} | {_fmt(lat.get('simhash', 0.0), 2)} |\n"
            )
        parts.append("\n")
    else:
        parts.append("## Scalability\n\n`scalability.json` not found.\n\n")

    parts.append(
        "## Notes / interpretation\n\n"
        "- Precision@5 can look artificially low if the ground-truth `relevant_chunk_ids` set is small (e.g., only 1 chunk labeled relevant implies a ceiling of 0.20 for P@5).\n"
        "- Use the sensitivity sweeps to justify parameter choices (accuracy vs latency trade-offs).\n"
    )

    out_path = results_dir / "REPORT.md"
    out_path.write_text("".join(parts), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    generate_report()

