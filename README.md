# Delegate Tracking

This repository stores a Python Script for monitoring delegated MKR to Aligned Delegates at MakerDAO.

Since it utilizes Etherscan's API, an Etherscan API Key is required.

It will generate the amount of MKR delegated to each AD for each date in the selected range, as well as calculate the rank of that AD compared to all other ADs. This can be exported as a csv for ease of use.

AD information should be loaded as a CSV called "Aligned Delegates.csv" in the data folder. An example is provided that is correct as of 2024-01-04.

## To Dos

* General code clean up.
* Add support for GSL end dates - currently this needs to be checked manually.
* Automatically source participation data for votes.
