import numpy as np
from ml_model import get_prediction
from crypto_data import get_crypto_data
from storage import get_history


class TradingSignal:
    """Генератор торговых сигналов на основе ML + TA"""
    
    def __init__(self, coin="SOL"):
        self.coin = coin
    
    def calculate_moving_averages(self, period=14):
        """Расчёт SMA (Simple Moving Average)"""
        history = get_history(self.coin, limit=period + 10)
        if not history:
            return None, None
        
        prices = np.array([float(row[2]) for row in history])[::-1]
        
        sma_short = np.mean(prices[-7:])  # 7-дневная
        sma_long = np.mean(prices[-period:])  # 14-дневная
        
        return float(sma_short), float(sma_long)
    
    def calculate_rsi(self, period=14):
        """Расчёт RSI (Relative Strength Index)"""
        history = get_history(self.coin, limit=period + 10)
        if not history:
            return None
        
        prices = np.array([float(row[2]) for row in history])[::-1]
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def calculate_volatility(self, period=14):
        """Расчёт волатильности (стандартное отклонение)"""
        history = get_history(self.coin, limit=period + 5)
        if not history:
            return None
        
        prices = np.array([float(row[2]) for row in history])[::-1]
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns[-period:]) * 100
        
        return float(volatility)
    
    def generate_signal(self, days_ahead=1):
        """Генерировать торговый сигнал"""
        try:
            # Получить текущие данные
            data = get_crypto_data(self.coin)
            current_price = data['price']
            
            # ML предсказание
            ml_pred = get_prediction(self.coin, days=days_ahead)
            if "error" in ml_pred:
                return {"error": ml_pred["error"]}
            
            predicted_price = ml_pred['predictions'][days_ahead - 1]
            ml_change = (predicted_price - current_price) / current_price * 100
            
            # TA индикаторы
            sma_short, sma_long = self.calculate_moving_averages()
            rsi = self.calculate_rsi()
            volatility = self.calculate_volatility()
            
            # Логика сигнала
            signals = []
            confidence_score = 0
            
            # SMA сигнал
            if sma_short and sma_long:
                if sma_short > sma_long:
                    signals.append("BUY")
                    confidence_score += 20
                else:
                    signals.append("SELL")
                    confidence_score += 20
            
            # RSI сигнал
            if rsi:
                if rsi < 30:
                    signals.append("BUY")
                    confidence_score += 20
                elif rsi > 70:
                    signals.append("SELL")
                    confidence_score += 20
            
            # ML сигнал
            if ml_change > 2:
                signals.append("BUY")
                confidence_score += 30
            elif ml_change < -2:
                signals.append("SELL")
                confidence_score += 30
            
            # Финальный сигнал (большинство голосов)
            buy_count = signals.count("BUY")
            sell_count = signals.count("SELL")
            
            if buy_count > sell_count:
                final_signal = "🟢 BUY"
            elif sell_count > buy_count:
                final_signal = "🔴 SELL"
            else:
                final_signal = "⚪ HOLD"
            
            # Risk Management
            stop_loss = current_price * 0.95  # -5%
            take_profit = current_price * 1.10  # +10%
            
            return {
                "coin": self.coin,
                "signal": final_signal,
                "current_price": float(current_price),
                "predicted_price": float(predicted_price),
                "ml_change_percent": float(ml_change),
                "confidence": min(confidence_score, 100),
                "indicators": {
                    "sma_short": float(sma_short) if sma_short else None,
                    "sma_long": float(sma_long) if sma_long else None,
                    "rsi": float(rsi) if rsi else None,
                    "volatility": float(volatility) if volatility else None
                },
                "risk_management": {
                    "stop_loss": float(stop_loss),
                    "take_profit": float(take_profit),
                    "risk_reward_ratio": (take_profit - current_price) / (current_price - stop_loss)
                },
                "days_ahead": days_ahead
            }
        
        except Exception as e:
            return {"error": str(e)}


def get_signal(coin="SOL", days=1):
    """Удобная функция для получения сигнала"""
    signal_gen = TradingSignal(coin=coin)
    return signal_gen.generate_signal(days_ahead=days)
