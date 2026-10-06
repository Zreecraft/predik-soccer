import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split

def train_xgboost_model():
    print("🔄 Memuat data tembakan untuk pelatihan Machine Learning...")
    try:
        df = pd.read_csv("real_shots_data.csv")
    except FileNotFoundError:
        print("❌ Error: File 'real_shots_data.csv' belum ada. Jalankan 'python fetch_data.py' dulu!")
        return

    if df.empty:
        print("⚠️ Data tembakan kosong!")
        return

    # Preprocessing Data
    df['is_goal'] = (df['result'] == 'Goal').astype(int)
    
    # Feature Selection (Koordinat X, Y, dan Situasi)
    features = ['X', 'Y', 'is_home']
    X = df[features]
    y = df['is_goal']

    # Split Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train XGBoost Model
    print("🧠 Melatih Model XGBoost Classifier...")
    model = XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    # Simpan Model Latihan
    joblib.dump(model, "xg_model.pkl")
    print("✅ Model ML berhasil dilatih & disimpan sebagai 'xg_model.pkl'!")

if __name__ == "__main__":
    train_xgboost_model()