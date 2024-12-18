import requests
import time

BASE_URL = 'https://api-futures.kucoin.com'

def get_active_contracts():
    endpoint = '/api/v1/contracts/active'
    url = BASE_URL + endpoint
    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            contracts = response.json()  # Parse the response
            if isinstance(contracts, list):  # Ensure it's a list
                return contracts
            elif 'data' in contracts and isinstance(contracts['data'], list):
                return contracts['data']  # Extract data if wrapped
            else:
                print("Unexpected structure:", contracts)
                return None
        except ValueError as e:
            print("Error parsing JSON:", e)
            return None
    else:
        print(f"Error fetching active contracts: {response.status_code}")
        print(response.text)
        return None

def get_funding_history(symbol, start_time, end_time):
    endpoint = f'/api/v1/contract/funding-rates'
    params = {
        'symbol': symbol,
        'from': start_time,
        'to': end_time
    }
    url = BASE_URL + endpoint
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json().get('data', [])
    else:
        print(f"Error fetching funding history for {symbol}: {response.status_code}")
        return None

# Calculate the timestamps
current_time = int(time.time() * 1000)  # Current time in milliseconds
three_days_ago = current_time - (3 * 24 * 60 * 60 * 1000)  # 3 days ago in milliseconds

# Fetch all active contracts and their symbols with sufficient 24-hour turnover
contracts = get_active_contracts()
funding_rate_summary = []

if contracts:
    print("Fetching funding history for contracts with turnover > 500,000 USDT:")
    for contract in contracts:
        turnover = contract.get('turnoverOf24h', 0)
        if turnover > 500000:
            symbol = contract.get('symbol')
            print(f"\nFetching funding history for {symbol}...")
            funding_history = get_funding_history(symbol, three_days_ago, current_time)
            if funding_history:
                funding_rates = [entry.get('fundingRate', 0) for entry in funding_history]
                if len(funding_rates) == 9:  # Ensure exactly 9 rates are used
                    summed_rate = sum(funding_rates)
                    calculated_rate = (summed_rate / 3) * 100
                    funding_rate_summary.append((symbol, calculated_rate))
                else:
                    print(f"Skipping {symbol} due to insufficient funding data.")
            else:
                print(f"No funding history available for {symbol}.")
    
    # Sort the results by calculated_rate in descending order
    funding_rate_summary.sort(key=lambda x: x[1], reverse=True)
    
    # Write results to a text file
    with open("kucoinrates.txt", "w") as file:
        file.write("Symbols sorted by calculated funding rate (turnover > 500,000 USDT):\n")
        for symbol, rate in funding_rate_summary:
            file.write(f"Symbol: {symbol}, Rate: {rate:.6f}\n")
    
    print("\nResults written to kucoinrates.txt")
else:
    print("No contracts retrieved or unexpected format.")
