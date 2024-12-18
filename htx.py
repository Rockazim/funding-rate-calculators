import requests

# Define base URL and endpoint
base_url = "https://api.hbdm.com"
endpoint = "/linear-swap-api/v1/swap_historical_funding_rate"

# Fetch all contract codes
def get_contracts():
    url = f"{base_url}/linear-swap-api/v1/swap_contract_info"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return [contract['contract_code'] for contract in data['data']]

# Fetch historical funding rates for a specific contract
def get_historical_funding_rate(contract_code, page_index=1, page_size=9):
    url = f"{base_url}{endpoint}"
    params = {
        "contract_code": contract_code,
        "page_index": page_index,
        "page_size": page_size,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

# Main execution
try:
    # Step 1: Get all contract codes
    contracts = get_contracts()

    # Step 2: Fetch and process funding rates for each contract
    processed_rates = []
    for contract in contracts:
        print(f"Fetching funding rates for {contract}...")
        response = get_historical_funding_rate(contract)
        if response["status"] == "ok" and "data" in response and response["data"]["data"]:
            rates = response["data"]["data"]
            funding_rates = [float(rate["funding_rate"]) for rate in rates if rate["funding_rate"] is not None]

            if len(funding_rates) >= 9:
                # Take the 9 most recent rates
                funding_rates = funding_rates[:9]

                # Calculate the rate: (Sum of 9 rates / 3) * 100
                adjusted_rate = (sum(funding_rates) / 3) * 100

                # Append the result to the processed rates list
                processed_rates.append((contract, adjusted_rate))
            else:
                print(f"Not enough funding rates for {contract}. Skipping...")
        else:
            print(f"No valid data for {contract}. Skipping...")

    # Step 3: Sort rates by adjusted rate in descending order
    processed_rates.sort(key=lambda x: x[1], reverse=True)

    # Step 4: Write results to "htx.rates"
    with open("htxrates.txt", "w") as file:
        for contract, rate in processed_rates:
            file.write(f"{contract}: {rate:.6f}\n")

    print("Funding rates have been written to 'htxrates.txt'.")

except requests.exceptions.RequestException as e:
    print(f"API request failed: {e}")
