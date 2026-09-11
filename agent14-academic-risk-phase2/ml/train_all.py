import json

try:
    from .config import METRICS_DIR
    from .data_loader import build_training_sets, load_processed_data, print_target_distributions
    from .training import train_one
except ImportError:
    from config import METRICS_DIR
    from data_loader import build_training_sets, load_processed_data, print_target_distributions
    from training import train_one


def train_all() -> None:
    data = load_processed_data()
    training_sets = build_training_sets(data)
    print_target_distributions(training_sets)
    summary = {}
    for name, (frame, target, _, description) in training_sets.items():
        _, metadata = train_one(name, frame, target, description)
        summary[name] = {key: metadata[key] for key in ("model", "accuracy", "precision", "recall", "f1", "roc_auc")}
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with (METRICS_DIR / "model_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print("\n=========================================")
    print("AGENT 14 - ML TRAINING SUMMARY")
    print("=========================================")
    for name, values in summary.items():
        print(f"{name}: {values['model']} | accuracy={values['accuracy']:.2%} | f1={values['f1']:.2%} | roc_auc={values['roc_auc']}")
    print("All models saved successfully.")
    print("=========================================")


def main() -> None:
    train_all()


if __name__ == "__main__":
    main()
