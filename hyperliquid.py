import requests
import time

# Define your API key and the base URL
api_key = "Put your key here"  # Replace with your actual Coinalyze API key
base_url = "https://api.coinalyze.net/v1"
headers = {"api_key": api_key}

# Set the time range for the past 3 days
end_time = int(time.time())
start_time = end_time - (3 * 24 * 60 * 60)  # 3 days in seconds

# Retrieve perpetual tickers for Hyperliquid
url_future_markets = f"{base_url}/future-markets"
try:
    response = requests.get(url_future_markets, headers=headers)
    response.raise_for_status()
    future_markets = response.json()
    symbols = [
        market['symbol'] for market in future_markets
        if market['exchange'] == "H" and market['is_perpetual'] == True
    ]
except Exception as e:
    print(f"Failed to retrieve markets: {e}")
    exit()

# Prepare to retrieve funding rate history
url_funding_rate = f"{base_url}/funding-rate-history"
average_funding_rates = []

# Process each symbol
for i, symbol in enumerate(symbols):
    params = {
        "symbols": symbol,
        "interval": "1hour",
        "from": start_time,
        "to": end_time
    }
    try:
        response = requests.get(url_funding_rate, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract 'c' (close) values from the history, assuming it represents the funding rate
        rates = [entry['c'] for entry in data[0]['history'] if 'c' in entry]
        
        if len(rates) == 72:  # Only process if we have the required 72 data points
            avg_rate = sum(rates) / 3  # Sum and divide by 3 to get the 3-day average
            average_funding_rates.append((symbol, avg_rate))
        else:
            print(f"Skipping {symbol} due to insufficient data points")

    except requests.exceptions.HTTPError as err:
        if response.status_code == 429:
            print("Rate limit exceeded. Waiting before retrying...")
            time.sleep(60)  # Wait for a minute before retrying to avoid rate limit
        else:
            print(f"Failed to retrieve funding rate for {symbol}: {err}")
    except Exception as e:
        print(f"An error occurred for {symbol}: {e}")
    
    # Introduce a delay after each request to manage rate limiting
    if (i + 1) % 10 == 0:
        time.sleep(1.5)

# Sort by funding rate in descending order
sorted_rates = sorted(average_funding_rates, key=lambda x: x[1], reverse=True)

# Write results to "hyperliquidrates.txt"
with open("hyperliquidrates.txt", "w") as file:
    for symbol, avg_rate in sorted_rates:
        file.write(f"{symbol}: {avg_rate}\n")

print("Funding rates have been written to 'hyperliquidrates.txt'.")
