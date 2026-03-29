"""
CLI module
"""
from datetime import datetime
from typing import Self
from playwright.sync_api import sync_playwright, Page
from argparse import ArgumentParser
from dataclasses import dataclass, field
from dataclass_wizard import JSONFileWizard
from sys import stdout, exit
from os import environ
from dotenv import load_dotenv
import logging
from re import split
from pathlib import Path

from automed.auth import User
from automed.prescriptions import Prescriptions
load_dotenv()

PRESCRIPTIONS_FILENAME = "prescriptions.json"
MOCK_PAGES_FOLDER_NAME = "mock-pages"
MOCK_REFILL_PAGE_FILE = "refill.htm"
MOCK_ORDER_CONFIRMATION_PAGE_FILE = "order-result.htm"

# Get current logger
log = logging.getLogger(__name__)

class ScriptError(Exception):
    pass


def get_filtered_prescriptions_from_user(filepath: str) -> Prescriptions:
    """
    Read prescriptions from file. Get the specific prescriptions to order from user.
    """
    # Get prescriptions from filepath
    log.info("Get prescription info from filename: %s", PRESCRIPTIONS_FILENAME)
    try:
        prescriptions_output = Prescriptions.from_json_file(filepath)
    except FileNotFoundError as e:
        raise ScriptError("The prescriptions.json file is not defined in the current directory (%s)." % Path.cwd())
    log.info("Got prescriptions!")
    log.debug("Output data: %r", prescriptions_output)
    prescriptions = prescriptions_output[0] if isinstance(prescriptions_output, list) else prescriptions_output

    # Filter prescriptions by user
    log.info("Found %i prescriptions", len(prescriptions.prescriptions))
    presc_with_keys = [ (str(k), p) for k, p in enumerate(prescriptions.prescriptions) ]
    for key, presc in presc_with_keys:
        log.info("Prescription ID: %s, Prescription: %s", key, presc)
    print()
    print("Enter the ids for the prescriptions you want to refill separated by spaces")
    print("If you want all of them, just hit enter (put in an empty string):")
    print("Available Ids:")
    for key, presc in presc_with_keys:
        print(f"\t[{key}]: {presc.name}")
    ids_input = input("Enter ids: ")
    log.info("Got input from user: %r", ids_input)
    ids = [k for k in split(r"\s+", ids_input) if k]
    log.info("Ids from input: %s", ids)
    if len(ids) == 0:
        log.info("User opted out of filtering. Returning current prescriptions list")
        return prescriptions
    new_prescs = [ presc for k, presc in presc_with_keys if k in ids ]
    prescriptions.prescriptions = new_prescs
    log.info("New prescriptions: %s", prescriptions.prescriptions)
    return prescriptions

def log_in_to_form(user: User, page: Page):
    """
    Log into actual website
    """
    # Do Sign in
    log.info('Log in')
    page.goto("https://myhealth.atriushealth.org")
    page.get_by_role("textbox", name="Username").type(user.username)
    page.get_by_role("textbox", name="Password").type(user.password.reveal())
    page.get_by_role("button", name="SIGN IN").click()

    # Now we gotta handle 2-factor auth...
    # We'll prompt me for the code
    log.info("2-FACTOR AUTH!!!!!!!!!!!!!!")
    page.get_by_role("button", name="Text the code to my phone").click()
    page.get_by_text("Trust this device for 30 days").click()
    code = input("Enter 2-Factor Code from Text Message: ")
    page.get_by_role("textbox", name="Enter Code").type(code)
    page.locator("#submitSecondaryValidation").click()

    # Go to medication refill form
    page.get_by_role("link", name="Medications").click()
    page.get_by_role("link", name="Request Refill from Atrius Health Pharmacy").click()


def MOCK_log_in_to_form(_user: User, page: Page):
    """
    Load MOCK log in html
    """
    mock_path = Path(__file__).parents[2] / "mock-pages" / MOCK_REFILL_PAGE_FILE
    mock_url = f"file:///{mock_path}"
    log.info("Mock login page path: %s", mock_url)
    page.goto(mock_url)


def fill_prescription_form(prescriptions: Prescriptions, page: Page):
    """
    Fill form
    """
    # Get form context (create helper methods)
    form = page.locator('iframe[name="MyChart_RxRefill"]').content_frame
    def enter(name: str, value: str):
        form.locator(f'input[name="{name}"]').type(value)
    def select(name: str, value: str):
        form.locator(f'select[name="{name}"]').select_option(value)
    def radio(name: str, value: str):
        form.locator(f'input[name="{name}"][text="{value}"]').click()

    # Enter preliminary data
    log.info("Enter preliminary information")
    enter("PatientName", prescriptions.prelim.PatientName)
    select("DobMonth", prescriptions.prelim.DobMonth)
    select("DobDay", prescriptions.prelim.DobDay)
    select("DobYear", prescriptions.prelim.DobYear)
    enter("Email", prescriptions.prelim.Email)
    enter("PhoneAC", prescriptions.prelim.PhoneAC)
    enter("PhonePrefix", prescriptions.prelim.PhonePrefix)
    enter("PhoneSuffix", prescriptions.prelim.PhoneSuffix)
    enter("Availability", prescriptions.prelim.Availability)
    select("PharmacyId", prescriptions.prelim.PharmacyId)
    radio("IsAutoRefill", prescriptions.prelim.IsAutoRefill)
    radio("OrderTypeId", prescriptions.prelim.OrderTypeId)

    # Enter prescription data
    for index, presc in enumerate(prescriptions.prescriptions):
        log.info("Entering prescription info for (%i) %s", index, presc)
        row = index + 1
        enter(f'Prescription{row}', presc.rxid)
        enter(f'DrugName{row}', presc.name)
        select(f'Quantity{row}', prescriptions.defaultSupply)

    # Confirm from user
    confirm = input('Confirm information and proceed? [yN]: ')
    if confirm != 'y':
        print('Cancelling...')
        exit(1)
    print('Confirmed!')

    # Submit
    log.info('Submit information and place order')
    form.get_by_role("button", name="Continue").click()
    form.get_by_role("button", name="Place Order").click()
    log.info("Medication refills submitted!")

def MOCK_open_order_confirmation_form(page: Page):
    """
    Load MOCK order confirmation html
    """
    mock_path = Path(__file__).parents[2] / "mock-pages" / MOCK_ORDER_CONFIRMATION_PAGE_FILE
    mock_url = f"file:///{mock_path}"
    log.info("Mock login page path: %s", mock_url)
    page.goto(mock_url)

def save_order_receipt(prescriptions: Prescriptions, page: Page):
    """
    Make sure order receipt is saved
    """
    receipt_dir = Path(prescriptions.receiptPath)
    receipt_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    receipt_file = receipt_dir / f'{receipt_timestamp}.pdf'
    page.pdf(path=receipt_file)
    log.info("Receipt saved to %s", receipt_file)

def cli():
    """
    Run CLI Tool
    """
    # Parse arguments
    argparse = ArgumentParser()
    args = argparse.parse_args()

    # Configure logging
    logging.basicConfig(stream=stdout, level=logging.INFO)

    # Get user
    user = User.from_env()
    prescriptions = get_filtered_prescriptions_from_user(PRESCRIPTIONS_FILENAME)

    # Open playwright
    with sync_playwright() as p:
        # Launch Firefox
        log.info('Launch Firefox')
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        # Fill out form
        log_in_to_form(user, page)
        fill_prescription_form(prescriptions, page)
        page.pause()