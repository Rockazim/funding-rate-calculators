import requests
import time

# Hyperliquid endpoint and headers
url_info = "https://api.hyperliquid.xyz/info"
headers = {"Content-Type": "application/json"}

# ---------------------------
# 1. Retrieve Perpetual Meta Data
# ---------------------------
meta_payload = {"type": "meta"}
try:
    meta_response = requests.post(url_info, json=meta_payload, headers=headers)
    meta_response.raise_for_status()
    meta_data = meta_response.json()
    universe = meta_data.get("universe", [])
    if not universe:
        print("No perpetual metadata found.")
        exit()
except Exception as e:
    print(f"Failed to retrieve perpetual metadata: {e}")
    exit()

# Build a list of available coins and print their asset IDs (index in the universe)
coins = []
for idx, coin_info in enumerate(universe):
    coin_name = coin_info.get("name")
    # Optionally skip delisted coins (they are not available for trading)
    if coin_info.get("isDelisted", False):
        continue
    coins.append(coin_name)

# Set the time range for the past 3 days (timestamps in milliseconds)
end_time_ms = int(time.time() * 1000)
start_time_ms = end_time_ms - (3 * 24 * 60 * 60 * 1000)

average_funding_rates = []

for i, coin in enumerate(coins):
    funding_payload = {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": start_time_ms,
        "endTime": end_time_ms
    }

    try:
        response = requests.post(url_info, json=funding_payload, headers=headers)
        response.raise_for_status()
        data = response.json()  # Expecting a list of funding history entries

        # Extra validation: sort the data by timestamp
        data.sort(key=lambda x: x.get("time", 0))

        # Validate that each entry's timestamp is within the expected range
        for entry in data:
            timestamp = entry.get("time")
            if timestamp < start_time_ms or timestamp > end_time_ms:
                print(f"Warning for {coin}: entry with timestamp {timestamp} is outside the requested range.")

        # Extract fundingRate values and convert them from string to float
        rates = [float(entry["fundingRate"]) for entry in data if "fundingRate" in entry]

        # Expect 72 data points for 3 days of hourly data.
        if len(rates) == 72:
            # The original logic sums all hourly rates and divides by 3 to compute a daily average.
            avg_rate = sum(rates) / 3
            average_funding_rates.append((coin, avg_rate * 100))
        else:
            print(f"Skipping {coin}: insufficient data points ({len(rates)} found)")

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 429:
            print("Rate limit exceeded. Waiting 60 seconds before retrying...")
            time.sleep(60)
        else:
            print(f"HTTP error occurred for {coin}: {http_err}")
    except Exception as e:
        print(f"An error occurred for {coin}: {e}")

    # Small delay every 10 requests to avoid rate limiting
    if (i + 1) % 10 == 0:
        time.sleep(1.5)

sorted_rates = sorted(average_funding_rates, key=lambda x: x[1], reverse=True)

for coin, avg_rate in sorted_rates:
    print(f"{coin}: {avg_rate}%\n")