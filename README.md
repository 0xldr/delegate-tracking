# Delegate Tracking

This repository contains a Python script for monitoring MKR delegated to Aligned Delegates at MakerDAO.

## Important Note
- The script is not compatible with Python 3.12 due to the deprecation of certain datetime functions used in the code.

## Current Functionality
- Retrieves delegation logs from Etherscan.
- Allows querying of delegation data for specific dates or ranges.
- Option to export results to a CSV file.

## Requirements
- An Etherscan API Key is required.
- Python 3.x (versions prior to 3.12) and dependencies listed in `requirements.txt`.

## Installation
Follow these steps to set up the project:
1. Clone the repository:
   ```bash
   git clone https://github.com/0xldr/delegate-tracking.git
   ```
1. Navigate to the cloned directory:
   ```bash
   cd delegate-tracking
   ```
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Install the required dependencies from `requirements.txt`.
2. Run `delegate_tracking.py` and follow the on-screen prompts.

## To Dos
- [ ] General code clean up.
- [ ] Add support for GSL end dates.
- [ ] Automatically source participation data for votes.
