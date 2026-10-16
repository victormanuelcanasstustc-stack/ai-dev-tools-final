import json
import sys
import time
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = ROOT / "eval" / "casos" / "casos.json"
RESULTS_DIR = ROOT / "eval" / "resultados"

sys.path.insert(0, str(ROOT))

from agent.agent import review_code


def normalize_category(value):
    value = str(value or "").strip().lower()
    aliases = {
        "logic": "logic",
        "security": "security",
        "performance": "performance",
        "concurrency": "concurrency",
    }
    return aliases.get(value)


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with CASES_FILE.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    tp = fp = fn = 0
    clean_false_positives = 0
    clean_total = 0
    category_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    outputs = []
    start_all = time.perf_counter()

    for case in cases:
        case_id = case["id"]
        expected_bug = bool(case["has_bug"])
        category = case["category"]

        print(f"\nEvaluando {case_id}...")

        try:
            report = review_code(case["code"])
            findings = report.get("findings", [])
            valid_findings = [
                item for item in findings
                if isinstance(item, dict)
                and normalize_category(item.get("type")) is not None
            ]

            predicted_bug = len(valid_findings) > 0

            # Para los casos con defectos, se mide si detectó
            # al menos un hallazgo. No verifica aún la ubicación exacta.
            if expected_bug and predicted_bug:
                tp += 1
                category_stats[category]["tp"] += 1
            elif expected_bug and not predicted_bug:
                fn += 1
                category_stats[category]["fn"] += 1
            elif not expected_bug and predicted_bug:
                fp += 1
                clean_false_positives += 1
                category_stats["clean"]["fp"] += 1

            if not expected_bug:
                clean_total += 1

            outputs.append({
                "id": case_id,
                "expected_bug": expected_bug,
                "predicted_bug": predicted_bug,
                "expected_category": category,
                "findings": valid_findings,
                "metrics": report.get("metrics", {}),
                "error": None,
            })

            print(
                f"  Esperado: {'defecto' if expected_bug else 'limpio'} | "
                f"Detectado: {'hallazgo' if predicted_bug else 'sin hallazgos'}"
            )

        except Exception as error:
            # Una evaluación fallida no se cuenta como detección.
            if expected_bug:
                fn += 1
                category_stats[category]["fn"] += 1

            if not expected_bug:
                clean_total += 1

            outputs.append({
                "id": case_id,
                "expected_bug": expected_bug,
                "predicted_bug": False,
                "expected_category": category,
                "findings": [],
                "metrics": {},
                "error": str(error),
            })
            print(f"  ERROR: {error}")

    elapsed_all = time.perf_counter() - start_all

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )
    false_positive_rate = (
        clean_false_positives / clean_total if clean_total else 0.0
    )

    summary = {
        "cases_total": len(cases),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "clean_controls": clean_total,
        "clean_false_positives": clean_false_positives,
        "false_positive_rate_clean": round(false_positive_rate, 4),
        "elapsed_seconds": round(elapsed_all, 3),
        "category_stats": dict(category_stats),
        "results": outputs,
        "note": (
            "Métricas a nivel de caso: detectar al menos un hallazgo. "
            "No equivalen a precisión por hallazgo ni verifican ubicación."
        ),
    }

    output_file = RESULTS_DIR / "eval_run_1.json"
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    print("\n===== RESUMEN DE EVALUACIÓN =====")
    print(f"Casos: {len(cases)}")
    print(f"TP: {tp} | FP: {fp} | FN: {fn}")
    print(f"Precisión: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1: {f1:.2%}")
    print(f"Falsos positivos en controles limpios: {false_positive_rate:.2%}")
    print(f"Tiempo total: {elapsed_all:.2f} s")
    print(f"Resultados guardados en: {output_file}")


if __name__ == "__main__":
    main()