import dataclasses
import enum
import logging
import time
import threading
import asyncio
import json
import argparse
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclasses.dataclass
class RecBotOptions:
    url: str
    email: str
    password: str
    date: str


class RecBotState(enum.Enum):
    LOGGED_OUT = 1
    RESERVING = 2
    PURCHASING = 3


class RecGovBot:
    # XPaths for elements on the page
    LOGIN_BUTTON = '//*[@id="ga-global-nav-log-in-link"]'
    EMAIL_INPUT = '//*[@id="email"]'
    PASSWORD_INPUT = '//*[@id="rec-acct-sign-in-password"]'
    SUBMIT_LOGIN_BUTTON = '/html/body/div[6]/div/div/div/div[2]/div/div/div[2]/form/button'
    USER_NAME_ELEMENT = '//*[@id="nav-header-container"]/div/nav/div/div[2]/div[2]/div/div/div/div/button'
    DATE_MONTH_INPUT = '//div[@aria-label="month, "]'
    DATE_DAY_INPUT = '//div[@aria-label="day, "]'
    DATE_YEAR_INPUT = '//div[@aria-label="year, "]'
    TIME_BUTTONS_DIV = '//*[@id="use-id-37"]/div/div'
    FINAL_BUTTON = '//*[@id="request-tickets"]'
    NO_AVAILABLE_XPATH = "//h2[@class='h6' and text()='No available times']"

    def __init__(self, options: RecBotOptions):
        self.options = options
        self.state = RecBotState.LOGGED_OUT
        self.driver = self.setup_webdriver()

    @staticmethod
    def setup_webdriver():
        chromedriver_path = os.environ.get('DRIVER_PATH', 'chromedriver')
        service = Service(chromedriver_path)
        chrome_options = Options()
        return webdriver.Chrome(service=service, options=chrome_options)

    def wait_for_element(self, by, value, timeout=10):
        """
        Wait for an element to be present on the page and return it.

        :param by: The method to locate the element (e.g., By.XPATH, By.ID)
        :param value: The locator value
        :param timeout: Maximum time to wait for the element
        :return: The WebElement if found, None otherwise
        """
        try:
            logging.debug(f"Waiting for element: {value}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            logging.debug(f"Element found: {value}")
            return element
        except TimeoutException:
            logging.error(f"Element not found: {value}")
            return None
        except Exception as e:
            logging.error(f"An error occurred while waiting for {value}: {str(e)}")
            return None

    # Log in to the website
    def login(self) -> bool:
        logging.info("Starting login process")
        self.driver.get(self.options.url)

        login_button = self.wait_for_element(By.XPATH, self.LOGIN_BUTTON)
        if login_button:
            login_button.click()
        else:
            raise Exception("Failed to find login button")

        email_input = self.wait_for_element(By.XPATH, self.EMAIL_INPUT)
        password_input = self.wait_for_element(By.XPATH, self.PASSWORD_INPUT)

        if email_input and password_input:
            email_input.send_keys(self.options.email)
            password_input.send_keys(self.options.password)
            password_input.send_keys(Keys.RETURN)
            logging.info("Credentials entered and submitted")
        else:
            raise Exception("Failed to find email or password input fields")

        time.sleep(2)

        user_name_element = self.wait_for_element(By.XPATH, self.USER_NAME_ELEMENT)
        if user_name_element:
            logging.info("User has logged in successfully")
            return True
        else:
            raise Exception("Failed to find user name element")

    # Makes the reservation. Assumes the session is logged in
    def reserve(self) -> bool:
        month, day, year = self.options.date.split('/')

        month_input = self.wait_for_element(By.XPATH, self.DATE_MONTH_INPUT)
        day_input = self.wait_for_element(By.XPATH, self.DATE_DAY_INPUT)
        year_input = self.wait_for_element(By.XPATH, self.DATE_YEAR_INPUT)

        if month_input and day_input and year_input:
            month_input.send_keys(month)
            day_input.send_keys(day)
            year_input.send_keys(year)
            logging.info(f"Set date to: {self.options.date}")

            for element in [month_input, day_input, year_input]:
                element.send_keys(Keys.TAB)
            logging.info("Tabbed through date inputs")
        else:
            raise Exception("Failed to find date inputs")

        final_button = self.wait_for_element(By.XPATH, self.FINAL_BUTTON)
        if not final_button:
            raise Exception("Failed to find final button")

        # Wait for either the final button to be enabled or the "No available times" message
        try:
            WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    EC.element_to_be_clickable((By.XPATH, self.FINAL_BUTTON)),
                    EC.presence_of_element_located((By.XPATH, self.NO_AVAILABLE_XPATH))
                )
            )
        except TimeoutException:
            logging.error("Timed out waiting for final button or no available times message")
            return False

        if final_button.get_attribute("disabled") == "true":
            logging.info("No times available")
            return False
        final_button.click()
        logging.info("Clicked final button")
        return True

    # State machine logic to determine the next state
    # Logs in, tries to reserve until successful, then prompts the user to purchase
    def next_state(self) -> RecBotState:
        match self.state:
            case RecBotState.LOGGED_OUT:
                if self.login():
                    self.state = RecBotState.RESERVING
                else:
                    logging.error("Failed to log in")
                    time.sleep(5)
            case RecBotState.RESERVING:
                if self.reserve():
                    self.state = RecBotState.PURCHASING
                else:
                    logging.error("Failed to reserve")
                    time.sleep(1)
            case RecBotState.PURCHASING:
                # TODO: Implement purchasing logic
                logging.info("Purchasing")
                input("Press Enter to continue...")
        return self.state

    # Run the state machine
    def run(self):
        while self.state is not None:
            logging.info(f"Current state: {self.state}")
            try:
                self.state = self.next_state()
            except Exception as e:
                logging.error(f"An error occurred: {str(e)}")
                time.sleep(5)  # Retry after 5 seconds


sample_options = [RecBotOptions(
    date="1/1/2024",
    password="password",
    email="email",
    url="https://www.recreation.gov/timed-entry/10087086/ticket/10087087"
)]


# Creates a sample sample_options.json file
def create_sample_options_file():
    with open("sample_options.json", "w") as f:
        json.dump([dataclasses.asdict(options) for options in sample_options], f)


def main():
    create_sample_options_file()

    # Read options_list json file from the cli argument with argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("options", help="The path to the JSON config file")
    parser.add_argument("--instances", type=int, default=1, help="Number of instances to run for each option")

    with open(parser.parse_args().options, "r") as f:
        options_list = [RecBotOptions(**options) for options in json.load(f)]
        # Duplicate each option by the number of instances
        options_list = [option for option in options_list for _ in range(parser.parse_args().instances)]

    threads = []
    for options in options_list:
        print(f"Starting bot for {options.url}")
        bot = RecGovBot(options)
        thread = threading.Thread(target=bot.run)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
