import time
import oandapyV20
from oandapyV20.endpoints.pricing import PricingInfo
from oandapyV20.endpoints.orders import OrderCreate
from oandapyV20.endpoints.positions import PositionClose
from oandapyV20.endpoints.instruments import InstrumentsCandles

# Replace with your OANDA credentials
ACCESS_TOKEN = ""
ACCOUNT_ID = ""

client = oandapyV20.API(access_token=ACCESS_TOKEN)

def is_market_open(pair):
    params = {
        "instruments": pair
    }
    pricing_info = PricingInfo(ACCOUNT_ID, params=params)
    client.request(pricing_info)
    
    # Check if the "status" is "tradeable"
    for price in pricing_info.response.get("prices", []):
        if price["status"] == "tradeable":
            return True
    return False

def get_latest_candle(pair):
    params = {
        "granularity": "M30",  # 30-minute candles
        "count": 2  # Get the last two candles to determine the previous trend
    }
    candles = InstrumentsCandles(instrument=pair, params=params)
    client.request(candles)
    return candles.response["candles"]

def place_order(order_type):
    order_data = {
        "order": {
            "instrument": "USD_JPY",  # Trading USD/JPY
            "units": "100000",  # Adjusted to 100,000 units
            "type": "MARKET",
            "positionFill": "DEFAULT"
        }
    }
    if order_type == "sell":
        order_data["order"]["units"] = "-100000"  # Sell position for 100,000 units

    order = OrderCreate(ACCOUNT_ID, data=order_data)
    client.request(order)

def close_position(position):
    # This closes an existing position
    close_data = {
        "longUnits": "ALL" if position == "buy" else "NONE",
        "shortUnits": "ALL" if position == "sell" else "NONE"
    }
    close = PositionClose(accountID=ACCOUNT_ID, instrument="USD_JPY", data=close_data)
    client.request(close)

def determine_initial_position(candles):
    # Get the second-to-last candle (the previous candle)
    prev_candle = candles[-2]
    open_price = float(prev_candle['mid']['o'])
    close_price = float(prev_candle['mid']['c'])

    if close_price > open_price:
        return "buy"  # Upward trend, start with a buy order
    else:
        return "sell"  # Downward trend, start with a sell order

def trade_logic():
    position = None
    pair = "USD_JPY"
    open_price = None

    while True:
        # Check if the market is open before executing trades
        if not is_market_open(pair):
            print("Market is closed. Waiting for it to open...")
            time.sleep(60)  # Check again in 1 minute
            continue

        candles = get_latest_candle(pair)
        latest_candle = candles[-1]
        close_price = float(latest_candle['mid']['c'])

        if position is None:
            # Determine initial position based on the previous candle
            position = determine_initial_position(candles)
            place_order(position)
            open_price = close_price
        elif position == "buy":
            if close_price > open_price:
                open_price = close_price
            elif close_price < open_price:
                close_position(position)
                place_order("sell")
                position = "sell"
                open_price = close_price
        elif position == "sell":
            if close_price < open_price:
                open_price = close_price
            elif close_price > open_price:
                close_position(position)
                place_order("buy")
                position = "buy"
                open_price = close_price

        # Wait for the next 30-minute candle
        time.sleep(1800)  # 30 minutes = 1800 seconds

if __name__ == "__main__":
    trade_logic()
