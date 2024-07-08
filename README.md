# Recreation.gov Reservation Bot

## Background
During my trip to Glacier National Park we quickly realized the good hikes were
gated by a reservation system that opens at exactly 7PM and sells out within seconds.
I created this bot in order to secure a reservation for Iceberg Lake Trail before selling out.
Since the bot uses multiple instances and is able to make a reservation several hundred milliseconds
after the reservation opens, it was able to secure a reservation for me and my family.

## Overview

This project provides an automated bot for making reservations on recreation.gov.
It uses Selenium for web automation and can handle multiple reservation attempts in parallel.
Since some recreation.gov reservations are in high demand and can sell out quickly, this bot can help increase your chances of securing a spot.
[Here](https://www.recreation.gov/timed-entry/10087086/ticket/10087087) is an example of a reservation that can be made by this bot.

## Features

- Automated login to recreation.gov
- Automatic date selection
- Reservation attempt automation
- Multi-threaded execution for multiple reservations

## Requirements

- Python 3.7+
- Selenium
- ChromeDriver

## Setup

1. Install the required Python packages:
```
pip install -r requirements.txt
```

2. Download and install ChromeDriver:
   - Visit the [ChromeDriver downloads page](https://developer.chrome.com/docs/chromedriver/downloads)
   - Download the version that matches your Chrome browser
   - Place the ChromeDriver executable in a directory in your system PATH

3. Update the `DRIVER_PATH` in the script to point to your ChromeDriver location:
```shell
export DRIVER_PATH = '/path/to/your/chromedriver'
```

## Configuration

Create a JSON file with your reservation options. The structure should be as follows:

```json
[
   {
      "url": "https://www.recreation.gov/timed-entry/10087086/ticket/10087087",
      "email": "your_email@example.com",
      "password": "your_password",
      "date": "1/1/2024"
   },
   {
      // Add more reservation attempts here
   }
]
```

Each object in the JSON array represents a reservation state machine that will run on a separate thread.
To maximize your chances of securing a reservation, ~4 reservation instances are recommended.
To specify the number of duplicate instances, use the --instances flag.

## Usage

Run the script with the path to your options JSON file:

```shell
python rec_gov_bot.py path/to/your/options.json --instances 4
```

## How It Works

The bot operates as a state machine with the following states:

1. LOGGED_OUT: Attempts to log in
2. RESERVING: Tries to make a reservation
3. PURCHASING: Prompts the user to complete the purchase manually

The bot will continuously attempt to make reservations until successful or stopped.

## Limitations and Notes

- The purchasing process is not automated. The bot will stop and prompt for user input when a reservation is successfully made.
- The bot includes error handling and will retry operations in case of failures.
- This bot is for educational purposes only. Be sure to comply with recreation.gov's terms of service when using automated tools.

## Disclaimer

This project is not affiliated with or endorsed by recreation.gov. Use at your own risk and in compliance with all applicable terms of service and laws.