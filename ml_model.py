import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import json
import os
from datetime import datetime, timedelta

try:
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠️ TensorFlow не установлена. Использую простую линейную модель.")

from storage import get_history


class CryptoPredictor:
    """ML модель для предсказания цен крипто"""
    
    def __init__(self, coin="SOL", lookback=30):
        self.coin = coin
        self.lookback = lookback
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.model_path = f"models/{coin.lower()}_model.h5"
        self.history_data = None
        
        # Создать папку для моделей
        os.makedirs("models", exist_ok=True)
    
    def prepare_data(self):
        """Подготовить данные из истории цен"""
        history = get_history(self.coin, limit=200)
        
        if not history:
            return None, None
        
        # Извлечь цены
        prices = np.array([float(row[2]) for row in history])[::-1]  # В хронологическом порядке
        
        if len(prices) < self.lookback + 1:
            return None, None
        
        # Нормализация
        scaled_prices = self.scaler.fit_transform(prices.reshape(-1, 1))
        
        # Создать последовательности
        X, y = [], []
        for i in range(len(scaled_prices) - self.lookback):
            X.append(scaled_prices[i:i + self.lookback])
            y.append(scaled_prices[i + self.lookback])
        
        X = np.array(X)
        y = np.array(y)
        
        self.history_data = prices
        return X, y
    
    def build_model(self, X_train_shape):
        """Построить LSTM модель"""
        if not TF_AVAILABLE:
            return None
        
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(X_train_shape[1], X_train_shape[2])),
            Dropout(0.2),
            LSTM(50, activation='relu'),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def train(self, epochs=50, batch_size=32, validation_split=0.2):
        """Обучить модель"""
        if not TF_AVAILABLE:
            return {"error": "TensorFlow не установлена"}
        
        X, y = self.prepare_data()
        
        if X is None:
            return {"error": f"Недостаточно данных для {self.coin}"}
        
        # Разделение на train/test
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        self.model = self.build_model(X_train.shape)
        
        print(f"🤖 Обучаю модель для {self.coin}...")
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=0
        )
        
        # Оценка
        y_pred = self.model.predict(X_test, verbose=0)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        
        # Сохранить модель
        self.model.save(self.model_path)
        
        return {
            "status": "trained",
            "coin": self.coin,
            "epochs": epochs,
            "rmse": float(rmse),
            "mae": float(mae),
            "train_size": len(X_train),
            "test_size": len(X_test)
        }
    
    def predict(self, days=7):
        """Предсказать цены на N дней вперёд"""
        if not TF_AVAILABLE:
            return self._simple_predict(days)
        
        # Загрузить модель если нужно
        if self.model is None:
            if not os.path.exists(self.model_path):
                train_result = self.train()
                if "error" in train_result:
                    return train_result
            else:
                self.model = keras.models.load_model(self.model_path)
        
        X, y = self.prepare_data()
        
        if X is None:
            return {"error": f"Недостаточно данных"}
        
        # Последняя последовательность
        last_sequence = X[-1].copy()
        predictions = []
        
        for _ in range(days):
            next_pred = self.model.predict(last_sequence.reshape(1, self.lookback, 1), verbose=0)
            predictions.append(next_pred[0, 0])
            
            # Обновить последовательность
            last_sequence = np.append(last_sequence[1:], next_pred)
        
        # Денормализация
        predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1))
        
        current_price = self.history_data[-1]
        future_prices = [float(p[0]) for p in predictions]
        
        return {
            "coin": self.coin,
            "current_price": float(current_price),
            "predictions": future_prices,
            "days": days,
            "change_percent": [(p - current_price) / current_price * 100 for p in future_prices]
        }
    
    def _simple_predict(self, days=7):
        """Простое предсказание на основе линейного тренда (без TensorFlow)"""
        X, y = self.prepare_data()
        
        if X is None or len(self.history_data) < 10:
            return {"error": "Недостаточно данных"}
        
        prices = self.history_data[-14:]  # Последние 2 недели
        x_vals = np.arange(len(prices)).reshape(-1, 1)
        y_vals = prices.reshape(-1, 1)
        
        # Линейная регрессия
        coeffs = np.polyfit(x_vals.flatten(), y_vals.flatten(), 1)
        
        current_price = prices[-1]
        future_prices = []
        
        for i in range(1, days + 1):
            pred = coeffs[0] * (len(prices) + i - 1) + coeffs[1]
            future_prices.append(float(pred))
        
        return {
            "coin": self.coin,
            "current_price": float(current_price),
            "predictions": future_prices,
            "days": days,
            "change_percent": [(p - current_price) / current_price * 100 for p in future_prices],
            "model": "linear_trend"
        }


def get_prediction(coin="SOL", days=7):
    """Удобная функция для получения предсказания"""
    predictor = CryptoPredictor(coin=coin)
    return predictor.predict(days=days)
