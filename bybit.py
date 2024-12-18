import requests
import time
import hashlib
import hmac

# API credentials
api_key = 'UkOIXed03THSXs5NAB'
api_secret = 'wXscv0H6T0w9nQY8HYaOAu2v5TqZnNxP4Szd'

# API endpoint and parameters
url = "https://api.bybit.com/v5/market/funding/history"
params = {
    "category": "linear",
    "symbol": "SXPUSDT",
    "limit": 18
}

# Generate timestamp and sign
timestamp = str(int(time.time() * 1000))
recv_window = "5000"

# Create the string for signing
param_str = f"{timestamp}{api_key}{recv_window}category=linear&symbol=SAFEUSDT&limit=18"

# Generate the HMAC SHA256 signature
signature = hmac.new(
    api_secret.encode('utf-8'),
    param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Headers for authenticated request
headers = {
    "X-BAPI-API-KEY": api_key,
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-SIGN": signature,
    "X-BAPI-RECV-WINDOW": recv_window
}

# Send the GET request
response = requests.get(url, headers=headers, params=params)

# Check and print only the funding rates
if response.status_code == 200:
    funding_data = response.json()
    funding_rates = [entry['fundingRate'] for entry in funding_data['result']['list']]
    print(funding_rates)
else:
    print(f"Request failed with status code: {response.status_code}, response: {response.text}")
