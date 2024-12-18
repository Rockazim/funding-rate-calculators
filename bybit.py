import requests
import time
import hashlib
import hmac

# API credentials
api_key = 'INSERT YOUR API KEY HERE'
api_secret = 'INSERT YOUR API SECRET HERE'

# Function to generate signature
def generate_signature(api_secret, param_str):
    return hmac.new(
        api_secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

# Function to fetch data with rate limit handling
def fetch_with_rate_limit(url, params):
    timestamp = str(int(time.time() * 1000))
    recv_window = "5000"
    param_str = f"{timestamp}{api_key}{recv_window}" + "&".join([f"{k}={v}" for k, v in params.items()])
    signature = generate_signature(api_secret, param_str)
    
    headers = {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-SIGN": signature,
        "X-BAPI-RECV-WINDOW": recv_window
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        remaining = int(response.headers.get('X-Bapi-Limit-Status', 1))
        if remaining <= 1:
            reset_timestamp = int(response.headers.get('X-Bapi-Limit-Reset-Timestamp', time.time() * 1000))
            sleep_time = (reset_timestamp - int(time.time() * 1000)) / 1000
            if sleep_time > 0:
                print(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
    
    return response

# Fetch all perpetual futures tickers
def fetch_tickers():
    url = "https://api.bybit.com/v5/market/tickers"
    params = {"category": "linear"}
    
    response = fetch_with_rate_limit(url, params)
    if response.status_code == 200:
        return response.json()['result']['list']
    else:
        print(f"Failed to fetch tickers: {response.status_code}, {response.text}")
        return []

# Fetch funding interval for each ticker
def fetch_funding_interval(symbol):
    url = "https://api.bybit.com/v5/market/instruments-info"
    params = {"category": "linear", "symbol": symbol}
    
    response = fetch_with_rate_limit(url, params)
    if response.status_code == 200:
        data = response.json()['result']['list']
        if data:
            return data[0]['fundingInterval']
    print(f"Failed to fetch funding interval for {symbol}: {response.status_code}, {response.text}")
    return None

# Fetch funding rate history for each ticker
def fetch_funding_rate_history(symbol, funding_interval):
    intervals_per_day = 1440 / funding_interval
    total_intervals = int(3 * intervals_per_day)
    
    url = "https://api.bybit.com/v5/market/funding/history"
    params = {
        "category": "linear",
        "symbol": symbol,
        "limit": total_intervals
    }
    
    response = fetch_with_rate_limit(url, params)
    if response.status_code == 200:
        rates = [float(entry['fundingRate']) for entry in response.json()['result']['list']]
        return rates
    else:
        print(f"Failed to fetch funding rate history for {symbol}: {response.status_code}, {response.text}")
        return []

# Main execution
results = []
tickers = fetch_tickers()
for ticker in tickers:
    symbol = ticker['symbol']
    funding_interval = fetch_funding_interval(symbol)
    if funding_interval:
        funding_rates = fetch_funding_rate_history(symbol, funding_interval)
        if funding_rates:
            average_rate = (sum(funding_rates) / 3) * 100
            results.append((symbol, average_rate))

# Sort results by average rate in descending order
results.sort(key=lambda x: x[1], reverse=True)

# Write to file
with open("rates.txt", "w") as file:
    for symbol, rate in results:
        file.write(f"{symbol}: {rate:.4f}\n")
print("Funding rate calculation and writing to 'rates.txt' is complete.")
