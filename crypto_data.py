from pycoingecko import CoinGeckoAPI
from datetime import datetime

cg = CoinGeckoAPI()


def get_crypto_data(coin_id="solana", vs_currency="usd"):
    try:
        price_data = cg.get_price(
            ids=coin_id,
            vs_currencies=vs_currency,
            include_24hr_change=True,
            include_market_cap=True,
        )
        details = cg.get_coin_by_id(coin_id)

        return {
            "coin": details["name"],
            "symbol": details["symbol"].upper(),
            "price": price_data[coin_id][vs_currency],
            "change_24h": price_data[coin_id].get(f"{vs_currency}_24h_change", 0),
            "market_cap": details["market_data"]["market_cap"][vs_currency],
            "volume_24h": details["market_data"]["total_volume"][vs_currency],
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}
