import selenium
import urllib
import time
import argparse
import logging
from tqdm import tqdm
from csv import DictReader
from datetime import timedelta
from selenium import webdriver

WHATSAPP_URL = "https://web.whatsapp.com"
MESSAGE_URL = WHATSAPP_URL + "/send?phone={number}&text={msg}"
WAIT_FOR_ERROR_TIME = 0.5

logger = logging.getLogger(__name__)

global gtimeout


class TimeoutReachedException(Exception):
    pass

class TqdmLoggingHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            self.handleError(record)

class XPATHS():
    LOGIN_PAGE = '//canvas[@aria-label="Scan this QR code to link a device!"]'
    MAIN_PAGE = '//span[@aria-label="WhatsApp"]'
    CONTINUE_BUTTON = '//div[text()="Continue"]'
    SEND_BUTTON = '//span[@data-icon="wds-ic-send-filled"]'
    ERROR = '//span[@data-icon="error"]'

def csv_to_items(file_path):
    with open(file_path, "r") as f:
        return [line for line in DictReader(f)]

def get_element_by_xpath(driver, xpath):
    try:
        return driver.find_element(selenium.webdriver.common.by.By.XPATH, xpath)
    except selenium.common.exceptions.NoSuchElementException:
        return None

def is_element_exists(driver, xpath):
    return bool(get_element_by_xpath(driver, xpath))

def wait_for_xpath(driver, xpath, timeout=None, timeout_bar=False):
    if timeout is None:
        global gtimeout
        timeout = gtimeout
    iterable = tqdm(range(timeout)) if timeout_bar else range(timeout)
    for _ in iterable:
        if is_element_exists(driver, xpath):
            return
        time.sleep(1)
    raise TimeoutReachedException()
        
def send_message(driver, number, message):
    driver.get(MESSAGE_URL.format(number=number, msg=urllib.parse.quote(message)))
    assert not is_element_exists(driver, XPATHS.LOGIN_PAGE), "You are not logged in"
    wait_for_xpath(driver, XPATHS.MAIN_PAGE)
    wait_for_xpath(driver, XPATHS.SEND_BUTTON, 2)
    send_button = get_element_by_xpath(driver, XPATHS.SEND_BUTTON)
    send_button.click()
    time.sleep(WAIT_FOR_ERROR_TIME)
    if get_element_by_xpath(driver, XPATHS.ERROR):
        logger.info(f"Message was not sent to {number}")
        return False
    else:
        logger.info(f"Sent message to {number}")
        return True

def handle_whatsapp_login(driver):
    driver.get(WHATSAPP_URL)
    wait_for_xpath(driver, XPATHS.LOGIN_PAGE)
    logger.info("Waiting on QR login")
    wait_for_xpath(driver, XPATHS.MAIN_PAGE, timeout_bar=True)
    logger.info("Logged in!")
    # sometimes a pop-up about whatsapp web appears. if so, press continue
    continue_button = get_element_by_xpath(driver, XPATHS.CONTINUE_BUTTON)
    if continue_button is not None:
        continue_button.click()

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(options=options)

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = TqdmLoggingHandler()
    formatter = logging.Formatter('[%(asctime)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def main(args):
    global gtimeout
    gtimeout = args.timeout
    setup_logger()
    msgs_to_send = csv_to_items(args.csv_path)
    driver = get_driver()
    logger.info("Initiating")
    handle_whatsapp_login(driver)
    approximate_time = timedelta(seconds=(len(msgs_to_send) * (gtimeout + WAIT_FOR_ERROR_TIME)))
    logger.info(f"starting to send messages to {len(msgs_to_send)} numbers. This will take approximately {approximate_time}")
    fails = []
    for entry in tqdm(msgs_to_send):
        try:
            send_message(driver, entry['number'], entry['message'])
            time.sleep(args.sleep_time)
        except Exception:
            logger.exception(f"Exception while sending message to {entry['number']}")
            fails.append(entry['number'])
    logger.info(f"Successfully sent {len(msgs_to_send) - len(fails)}/{len(msgs_to_send)} messages")
    if len(fails) > 0:
        logger.info(f"Failed numbers: {fails}")
    input("Press enter to close")

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser("Automatic Whatsapp Sender")
        parser.add_argument("csv_path", type=str, help="Path to csv of numbers and messages.\nNumbers should start with regional prefix.")
        parser.add_argument("-t" "--timeout", type=int, default=60, help="Timeout when waiting on web elements.", dest="timeout")
        parser.add_argument("-s", "--sleep-time", type=int, default=3, help="Sleep time between messages.", dest="sleep_time")
        args = parser.parse_args()
        main(args)
    except KeyboardInterrupt:
        logger.info("Keyboard Interrupt received. Aborting.")