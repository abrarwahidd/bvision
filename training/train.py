import yaml, json, joblib, mlflow, mlflow.sklearn
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

# Resolve project paths independent of current working directory.
ROOT = Path(__file__).resolve().parent.parent
with open(Path(__file__).resolve().parent / "params.yaml") as f:
    cfg = yaml.safe_load(f)
dp, mp, mf = cfg["data"], cfg["model"], cfg["mlflow"]

mlflow.set_tracking_uri(mf["tracking_uri"])
mlflow.set_experiment(mf["experiment_name"])

with mlflow.start_run(run_name="rf-bisindo"):
    # 1. Load data
    df = pd.read_csv(ROOT / dp["dataset_path"])
    X, y = df.drop("label", axis=1), df["label"]

    # 2. Preprocessing
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=dp["test_size"],
        stratify=y, random_state=dp["random_state"]
    )

    # 3. Log semua parameter
    mlflow.log_params({**mp, **dp})
    mlflow.log_param("num_classes", y.nunique())
    mlflow.log_param("train_samples", len(X_train))

    # 4. Training
    model = RandomForestClassifier(**{k: v for k, v in mp.items()})
    model.fit(X_train, y_train)

    # 5. Evaluasi & log metrics
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy":    round(accuracy_score(y_test, y_pred), 4),
        "f1_macro":    round(f1_score(y_test, y_pred, average="macro"), 4),
        "f1_weighted": round(f1_score(y_test, y_pred, average="weighted"), 4),
    }
    mlflow.log_metrics(metrics)

    # Simpan metrik evaluasi.
    (ROOT / "metrics").mkdir(exist_ok=True)
    with open(ROOT / "metrics/scores.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # 6. Confusion matrix sebagai artifact
    plt.figure(figsize=(14, 8))
    sns.heatmap(confusion_matrix(y_test, y_pred), annot=True, fmt="d",
                cmap="Blues", xticklabels=sorted(y.unique()),
                yticklabels=sorted(y.unique()))
    plt.title(f"Confusion Matrix — acc={metrics['accuracy']}")
    plt.tight_layout()
    plt.savefig(ROOT / "metrics/confusion_matrix.png")
    plt.close()
    mlflow.log_artifact(str(ROOT / "metrics/confusion_matrix.png"))

    # 7. Simpan scaler
    (ROOT / "backend/models").mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, ROOT / "backend/models/scaler_new.pkl")
    joblib.dump(model,  ROOT / "backend/models/model_new.pkl") 
    mlflow.log_artifact(str(ROOT / "backend/models/scaler_new.pkl"))
    mlflow.log_artifact(str(ROOT / "backend/models/model_new.pkl"))

    # 8. Register model ke MLflow Model Registry
    mlflow.sklearn.log_model(
        sk_model=model,
        name="random_forest_bisindo",
        registered_model_name=mf["registered_model_name"],
        skops_trusted_types=["sklearn.tree._tree.Tree"],
    )

    print(f"Selesai. Run ID: {mlflow.active_run().info.run_id}")
    print(f"Metrics: {metrics}")