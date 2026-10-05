import sklearn  # <--- WAJIB UNTUK XGBOOST
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
import joblib

print("🧠 Memulai Pelatihan Model Machine Learning (xG)...")

# Load data tembakan asli
df = pd.read_csv("real_shots_data.csv")

# Feature Engineering
df['X'] = df['X'].astype(float) * 105
df['Y'] = df['Y'].astype(float) * 68
df['distance'] = np.sqrt((105 - df['X'])**2 + (34 - df['Y'])**2)
df['angle'] = np.arctan2(7.32 * df['X'], (df['X']**2 + df['Y']**2 - (7.32/2)**2))

df = pd.get_dummies(df, columns=['shotType', 'situation'])
df['is_goal'] = df['result'].apply(lambda x: 1 if x == 'Goal' else 0)

feature_cols = [c for c in df.columns if c.startswith(('shotType_', 'situation_'))] + ['distance', 'angle']
X = df[feature_cols]
y = df['is_goal']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Training Model
model = XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=3)
model.fit(X_train, y_train)

# Simpan Model
joblib.dump(model, "xg_model.pkl")
print("✅ MODEL SELESAI DILATIH & DISIMPAN SANGAT PRESISI ('xg_model.pkl')!")