import requests
import datetime
import os
import sys
import csv
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Etherscan API setup
etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
etherscan_base_url = 'https://api.etherscan.io/api'

# Check if API key is present
if not etherscan_api_key or etherscan_api_key == 'YOUR_ETHERSCAN_API_KEY':
    print("Error: No Etherscan API key found. Please add your API key to the .env file.")
    print("If you don't have an API key, you can obtain one from https://etherscan.io/apis")
    sys.exit(1)

# Function Definitions
def get_logs(api_key, base_url, contract_address, start_block, end_block, event_hash):
    params = {
        'module': 'logs',
        'action': 'getLogs',
        'address': contract_address,
        'fromBlock': start_block,
        'toBlock': end_block,
        'topic0': event_hash,
        'apikey': api_key
    }
    try:
        response = requests.get(etherscan_base_url, params=params)
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during requests to {base_url}: {e}")

def convert_hex_to_decimal(hex_value):
    return int(hex_value, 16)

def convert_hex_to_eth_address(hex_value):
    return '0x' + hex_value[-40:]

def convert_hex_to_datetime(hex_value):
    timestamp = int(hex_value, 16)
    return datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')  # Only return the date part

def convert_wei_to_ether(wei_value):
    return wei_value / 1e18

def get_closest_delegation(delegation_data, query_datetime):
    closest_delegation = 0
    query_date = query_datetime.date()  # Convert datetime to date for comparison
    for delegate, dates in delegation_data.items():
        for date_str, amounts in dates.items():
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            if date <= query_date:
                closest_delegation += amounts['net']
    return closest_delegation

def read_csv():
    file_path = os.path.join('delegate_data', 'Aligned Delegates.csv')
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            contracts_data = []
            for row in csv_reader:
                contracts_data.append({
                    'name': row['Delegate Name'],
                    'contract': row['Delegate Contract'],
                    'committee': row['Aligned Voter Committee'],
                    'start_date': row['Start Date'],
                    'end_date': row['End Date'],
                    'end_reason': row['End Reason']
                })
            return contracts_data
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    
def generate_dates(query_input):
    dates = []
    today = datetime.datetime.now().date()  # Get today's date
    
    try:
        if 'to' in query_input:
            # Date range
            start_str, end_str = query_input.split(' to ')
            start_date = datetime.datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_str, '%Y-%m-%d')

            # Check if end date is in the future
            if end_date.date() > today:
                print("The application cannot see into the future.")
                confirm = input("Would you like to limit the range to today's date? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    end_date = datetime.datetime.now()
                else:
                    print("Exiting.")
                    sys.exit()

            while start_date <= end_date:
                dates.append(start_date)
                start_date += datetime.timedelta(days=1)

        else:
            # Single date
            single_date = datetime.datetime.strptime(query_input, '%Y-%m-%d')

            # Check if the date is in the future
            if single_date.date() > today:
                print("The application cannot see into the future.")
                confirm = input("Would you like to query today's date instead? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    single_date = datetime.datetime.now()
                else:
                    print("Exiting.")
                    sys.exit()

            dates.append(single_date)

    except ValueError as e:
        print(f"Invalid date format: {e}. Please try again.")
        return []

    return dates

def calculate_rankings(delegate_data):
    sorted_delegates = sorted(delegate_data.items(), key=lambda x: x[1]['total'], reverse=True)
    for rank, (delegate, data) in enumerate(sorted_delegates, start=1):
        delegate_data[delegate]['rank'] = rank
    return delegate_data
        
# Read the CSV file
contracts_data = read_csv()

# Initialize a dictionary for each contract
contract_delegations = {contract['contract']: {} for contract in contracts_data}

# Event hashes
lock_event_hash = '0x625fed9875dada8643f2418b838ae0bc78d9a148a18eee4ee1979ff0f3f5d427'
free_event_hash = '0xce6c5af8fd109993cb40da4d5dc9e4dd8e61bc2e48f1e3901472141e4f56f293'

# Hardcoding the first block of 2023-01-01
start_block = '16308190'
end_block = 'latest'

# Process each contract from CSV data
for contract in contracts_data:
    address = contract['contract']
    # Initialize storage for each contract and delegate
    contract_delegations[address] = {}

    # Retrieve logs for 'Lock' and 'Free' events
    for event_hash in [lock_event_hash, free_event_hash]:
        logs = get_logs(etherscan_api_key, etherscan_base_url, address, start_block, end_block, event_hash)
        for log in logs['result']:
            hex_data = log['data']
            decimal_data = convert_hex_to_decimal(hex_data)
            ether_value = convert_wei_to_ether(decimal_data)
            delegate_address = convert_hex_to_eth_address(log['topics'][1])
            timestamp = convert_hex_to_datetime(log['timeStamp'])

            # Initialize delegate storage
            if delegate_address not in contract_delegations[address]:
                contract_delegations[address][delegate_address] = {}

            # Initialize date storage
            if timestamp not in contract_delegations[address][delegate_address]:
                contract_delegations[address][delegate_address][timestamp] = {'net': 0}

            # Adjust net delegation based on event type
            if event_hash == lock_event_hash:
                contract_delegations[address][delegate_address][timestamp]['net'] += ether_value
            elif event_hash == free_event_hash:
                contract_delegations[address][delegate_address][timestamp]['net'] -= ether_value

# Initialize a dictionary to track delegate and committee delegations
delegate_committee_delegations = {}

# Loop to allow multiple date queries
while True:
    query_input = input("\nEnter the date to query (YYYY-MM-DD), or a range (YYYY-MM-DD to YYYY-MM-DD):")
    query_dates = generate_dates(query_input)

    results = {}  # Initialize results list

    for query_date in query_dates:
        query_date_str = query_date.strftime('%Y-%m-%d')  # Define query_date_str

        delegate_committee_delegations = {}  # Reset the dictionary for each date

        # Process each contract and update delegate_committee_delegations
        for contract in contracts_data:
            delegate_name = contract['name']
            committee_name = contract['committee']
            address = contract['contract']

            # Retrieve delegation data for this contract
            delegation_data = contract_delegations.get(address, {})
            delegation_at_query = get_closest_delegation(delegation_data, query_date)

            # Initialize delegate data if not already present
            if delegate_name not in delegate_committee_delegations:
                delegate_committee_delegations[delegate_name] = {'total': 0, 'committees': {}}

            # Update total delegation and committee-specific delegation for the delegate
            delegate_committee_delegations[delegate_name]['total'] += delegation_at_query
            delegate_committee_delegations[delegate_name]['committees'][committee_name] = delegation_at_query

            # Calculate and include rankings
            delegate_committee_delegations = calculate_rankings(delegate_committee_delegations)

            # Display results and store results for each date
            print(f"\nDelegations on {query_date_str}:")
            results[query_date_str] = []
            for delegate, data in delegate_committee_delegations.items():
                print(f"\nDelegate {delegate}:")
                print(f"Total Delegation: {data['total']} MKR")
                print(f"Ranking: {data['rank']}")
                for committee, delegation in data['committees'].items():
                    print(f"   - {committee}: {delegation} MKR")
                results[query_date_str].append({
                    'Delegate': delegate,
                    'Total Delegation': data['total'],
                    'Rank': data['rank'],
                    'Date': query_date_str
                })
        
    export_to_csv = input("\nDo you want to export the results to a CSV file? (yes/no): ").strip().lower()
    if export_to_csv == 'yes':
        csv_filename = f"delegation_data_{query_date_str}.csv"
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = ['Delegate', 'Total Delegation', 'Rank', 'Date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for query_date_str, date_results in results.items():
                for row in date_results:
                    writer.writerow(row)
        print(f"Data exported to {csv_filename}")

    continue_query = input("\nDo you want to query another date? (yes/no): ").strip().lower()
    if continue_query != 'yes':
        break
