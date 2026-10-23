import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = ROOT / "eval" / "casos" / "casos.json"
OUTPUT_DIR = ROOT / "eval" / "resultados"


def run_analyzer(tool, code_path):
    if tool == "ruff":
        command = [
            sys.executable, "-m", "ruff", "check",
            str(code_path), "--output-format", "json",
        ]
    else:
        command = [
            sys.executable, "-m", "bandit", "-f", "json",
            str(code_path),
        ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "detected": False,
            "findings": [],
            "error": result.stderr or result.stdout,
            "returncode": result.returncode,
        }

    if tool == "ruff":
        findings = data if isinstance(data, list) else []
    else:
        findings = data.get("results", [])

    return {
        "detected": bool(findings),
        "findings": findings,
        "error": result.stderr if result.returncode not in (0, 1) else "",
        "returncode": result.returncode,
    }


def calculate_metrics(cases, results):
    tp = fp = fn = tn = 0

    for case, result in zip(cases, results):
        expected = case["has_bug"]
        detected = result["detected"]

        if expected and detected:
            tp += 1
        elif not expected and detected:
            fp += 1
        elif expected and not detected:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    fpr = fp / (fp + tn) if fp + tn else 0.0

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate_clean_cases": fpr,
    }


def main():
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "method": (
            "A case is detected when the analyzer reports at least one "
            "finding in its code. This does not prove that the finding "
            "matches the case's intended defect."
        ),
        "total_cases": len(cases),
        "analyzers": {},
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)

        for tool in ("ruff", "bandit"):
            results = []

            for case in cases:
                code_path = temp_root / f"{case['id']}.py"
                code_path.write_text(case["code"], encoding="utf-8")

                try:
                    result = run_analyzer(tool, code_path)
                except subprocess.TimeoutExpired:
                    result = {
                        "detected": False,
                        "findings": [],
                        "error": "Analyzer timed out",
                    }

                results.append({
                    "case_id": case["id"],
                    "category": case["category"],
                    "has_bug": case["has_bug"],
                    **result,
                })

            report["analyzers"][tool] = {
                "metrics": calculate_metrics(cases, results),
                "cases": results,
            }

    output_path = OUTPUT_DIR / "static_analyzer_eval.json"
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for tool, data in report["analyzers"].items():
        print(f"\n=== {tool.upper()} ===")
        print(json.dumps(data["metrics"], indent=2, ensure_ascii=False))
        for item in data["cases"]:
            print(
                f"{item['case_id']}: "
                f"detected={item['detected']}, "
                f"findings={len(item['findings'])}"
            )
            if item.get("error"):
                print("  ERROR:", item["error"])

    print(f"\nInforme guardado en: {output_path}")


if __name__ == "__main__":
    main()