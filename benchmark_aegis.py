import time
import json
import statistics
import requests
from pathlib import Path

API_URL = "http://127.0.0.1:5000/api/incidents/demo"
RESULTS_DIR = Path("benchmark_results")
RESULTS_DIR.mkdir(exist_ok=True)


def run_once():
    start = time.perf_counter()
    response = requests.post(API_URL, timeout=120)
    end = time.perf_counter()

    response.raise_for_status()
    data = response.json()

    duration = end - start
    events = data.get("events", [])

    return {
        "run_id": data.get("run_id"),
        "status": data.get("status"),
        "duration_seconds": duration,
        "events_count": len(events),
        "stages": [e.get("stage") for e in events],
        "unit_tests": data.get("unit_tests", {}).get("status"),
        "red_team": data.get("red_team", {}).get("audit_status"),
        "pr_mode": data.get("pull_request", {}).get("mode"),
    }


def main(runs=10):
    results = []

    for i in range(runs):
        print(f"Running benchmark {i + 1}/{runs}...")
        result = run_once()
        results.append(result)
        print(f"Run {i + 1}: {result['duration_seconds']:.2f}s | {result['status']}")

    durations = [r["duration_seconds"] for r in results]

    summary = {
        "runs": runs,
        "successful_runs": sum(1 for r in results if r["status"] == "awaiting_human_approval"),
        "avg_latency_seconds": round(statistics.mean(durations), 3),
        "p50_latency_seconds": round(statistics.median(durations), 3),
        "p95_latency_seconds": round(sorted(durations)[int(0.95 * len(durations)) - 1], 3),
        "min_latency_seconds": round(min(durations), 3),
        "max_latency_seconds": round(max(durations), 3),
        "throughput_workflows_per_minute": round(60 / statistics.mean(durations), 2),
        "manual_sre_baseline_minutes": 30,
        "automated_avg_minutes": round(statistics.mean(durations) / 60, 2),
        "estimated_time_reduction_percent": round(
            ((30 - (statistics.mean(durations) / 60)) / 30) * 100, 2
        ),
    }

    output = {
        "summary": summary,
        "runs": results,
    }

    out_file = RESULTS_DIR / "aegis_benchmark_results.json"
    out_file.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("\n===== AegisSRE Benchmark Summary =====")
    for k, v in summary.items():
        print(f"{k}: {v}")

    print(f"\nSaved results to: {out_file}")


if __name__ == "__main__":
    main(runs=10)
