import joblib, os

BASE = "models/screening"

models = [
    "ds1_svm", "ds1_rf", "ds1_mlp",
    "ds2_svm", "ds2_rf", "ds2_mlp"
]

def test_all_models_load():
    for name in models:
        model_path  = f"{BASE}/{name}.pkl"
        scaler_path = f"{BASE}/{name}_scaler.pkl"

        assert os.path.exists(model_path),  f"MISSING: {model_path}"
        assert os.path.exists(scaler_path), f"MISSING: {scaler_path}"

        model  = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        assert model  is not None, f"Failed to load {name}"
        assert scaler is not None, f"Failed to load {name}_scaler"

        print(f"OK: {name}")

if __name__ == "__main__":
    test_all_models_load()
    print("\nAll 6 models loaded successfully.")