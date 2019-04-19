"""
Page objects for the debt pay down calculator
"""
import logging
from datetime import datetime
from sys import stdout
from typing import List

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from util.wrapped_webdriver import WrappedWebDriver, click_visible_element


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    stream=stdout,
)
LOGGER = logging.getLogger(__name__)


tax_brackets = {
    "10": "10% (Up to $9,325 single; up to $18,650 married)",
    "15": "15% ($9,326 to $37,950 single; $18,651 to $75,900 married)",
    "25": "25% ($37,951 to $91,900 single; $75,901 to $153,100 married)",
    "28": "28% ($91,901 to $191,650 single; $153,101 to $233,350 married)",
    "33": "33% ($191,651 to $416,700 single; $233,351 to $416,700 married)",
    "35": "35% ($416,701 to $418,400 single; $416,701 to $470,000 married)",
    "39.6": "39.6% ($418,401+ single; $470,001+ married)"
}

loan_types = {
    0: "Credit card or retailer charge card",
    1: "Car, truck, motorcycle, or boat loan",
    2: "Home equity loan",
    3: "Mortgage",
    4: "Other kind of loan"
}


class Promotion:
    """
        Credit Card Promotion Details
    """

    def __init__(
            self,
            regular_rate,
            promo_rate,
            end_date: str,
            minimum_monthly_payment,
            promo_type: str
    ):
        self.regular_rate = regular_rate
        self.promo_rate = promo_rate
        self.end_date = end_date
        self.minimum_monthly_payment = minimum_monthly_payment
        self.promo_type = promo_type


class Loan:
    """
        Loan or Credit Card
    """

    def __init__(
            self,
            lender_name: str,
            interest_rate,
            balance,
            min_monthly_payment,
            loan_type,
            promo: dict = None,
            deductible: str = "1"
    ):
        self.lender_name = lender_name
        self.interest_rate = interest_rate
        self.balance = balance
        self.min_monthly_payment = min_monthly_payment
        self.loan_type = loan_type
        self.promo = promo
        self.deductible = deductible

    def __repr__(self):
        return f"<Loan: {self.lender_name} - {self.balance} - {self.loan_type}>"

    @property
    def promo_details(self) -> Promotion:
        if self.promo:
            return Promotion(**self.promo)


class Loans:

    def __init__(self, loans: List[Loan]):
        self.loans = loans

    def __len__(self):
        return len(self.loans)

    def __iter__(self) -> Loan:
        for loan in self.loans:
            yield Loan(**loan)


class Windfall:
    """
        Cash 'windfalls': Any one-time events that will
        increase the cash you have in a given month
    """
    def __init__(self, amount: str, date: str):
        self.amount = amount
        self.date = date


class BasePage:
    """Base page object to share common objects and methods"""

    def __init__(self, webdriver: WrappedWebDriver):
        self.driver = webdriver


class DatePicker:
    """Date picker on the calculator page"""
    YEAR_CELLS = "//span[text()='{}'][contains(@class, 'cell year')]"
    YEAR_HEADER = "div.vdp-datepicker__calendar header span"

    def __init__(self, webdriver: WrappedWebDriver, date: str):
        self.driver = webdriver
        self.datetime = datetime.strptime(date, "%m/%d/%Y")
        self.year = self.datetime.year
        self.month = self.datetime.strftime("%B")
        self.day = self.datetime.day
        self.select_date()

    def nav_up(self):
        """Navigate to the highest level for DatePicker from days to decade."""
        month_year_button = self.driver.driver.find_elements_by_css_selector(
            "span.up"
        )
        click_visible_element(month_year_button)
        year_button = self.driver.driver.find_elements_by_css_selector(
                "span.up"
            )
        click_visible_element(year_button)

    def select_decade(self):
        """Assumes the calendar is by decade"""
        left_arrow, decade_span, right_arrow = [
            e for e in self.driver.driver.find_elements_by_css_selector(
                self.YEAR_HEADER) if e.is_displayed()
        ]
        decade_start, decade_end = [
            int(x) for x in decade_span.text.split('-')
        ]
        if self.year < decade_start:
            left_arrow.click()
            self.select_decade()
        elif self.year > decade_end:
            right_arrow.click()
            self.select_decade()

    def select_year(self):
        """Assumes the calendar is set to the decade for the selected year."""
        year = self.driver.driver.find_elements_by_xpath(
            self.YEAR_CELLS.format(self.year)
        )
        click_visible_element(year)

    def select_month(self):
        """Assumes months are visible and then clicks the selected month"""
        month = self.driver.driver.find_elements_by_xpath(
            f"//span[text()='{self.month}']"
        )
        click_visible_element(month)

    def select_day(self):
        """Assumes days are visible and then clicks the selected day"""
        day = self.driver.driver.find_elements_by_xpath(
            f"//span[text()='{self.day}']"
        )
        click_visible_element(day)

    def select_date(self):
        """Assumed that the date picker calendar is visible and on default view
        """
        self.nav_up()
        self.select_decade()
        self.select_year()
        self.select_month()
        self.select_day()


class Calculator(BasePage):
    """The overall calculator on the page"""

    CALCULATOR_URL = (
        "https://www.bankrate.com/calculators/managing-debt"
        "/debt-pay-down-calculator.aspx"
    )
    CALCULATOR_CONTAINER = "debt-pay-down-calculator"
    DEBT_COUNT_INPUT = "debtCount"
    EXTRA_PAYMENT_INPUT = "extraPayment"
    CARD_LENDER_NAME_INPUT = "lenderNamecreditCardLoan{index}"
    CARD_BALANCE_INPUT = "amountcreditCardLoan{index}"
    CARD_INTEREST_RATE_INPUT = "interestRatecreditCardLoan{index}"
    CARD_MIN_PAYMENT_INPUT = "monthlyPaymentcreditCardLoan{index}"
    CARD_PROMO_RATE = "introductoryRatecreditCardLoan{index}"
    CARD_PROMO_END_DATE = (
        "//input[@name='introductoryRatecreditCardLoan{index}']/../../../../"
        "div[3]/div/div/div/input"
    )
    PROMO_RATE_RADIO_OPTION = (
        "//input[@name='promotionTypecreditCardLoan{index}']/.."
    )
    OTHER_LOAN_LENDER_NAME_INPUT = "lenderNameotherLoanLoan{index}"
    OTHER_LOAN_BALANCE_INPUT = "amountotherLoanLoan{index}"
    OTHER_LOAN_INTEREST_RATE_INPUT = "interestRateotherLoanLoan{index}"
    OTHER_LOAN_MONTHLY_PAYMENT_INPUT = "monthlyPaymentotherLoanLoan{index}"
    OTHER_LOAN_TAX_DEDUCTIBLE_RADIO_OPTION = (
        "//input[@name='taxDeductibleotherLoanLoan{index}'][@value='true']/.."
    )
    ADDITIONAL_INCOME_INPUT = "additionalIncomeCount"
    ADDITIONAL_INCOME_TYPE_DROP_DOWN = "incomeTypeIncome{index}"
    ADDITIONAL_INCOME_MONTHLY_AMOUNT = "amountIncome{index}"
    ADDITIONAL_INCOME_RAISE_START_DATE = (
        "//label[text()='Start date:']/../div[@class='vdp-datepicker']"
    )
    ADDITIONAL_INCOME_WINDFALL_DATE = (
        "(//label[text()='Date:']/../div[@class='vdp-datepicker'])[{index}]"
    )
    CALCULATE_BUTTON = "div.grid-cell.size-1of3.\+center-content button"
    START_OVER_BUTTON = "//button[contains(text(), 'Start over')]"
    RESULTS_DIV = "//h5[text()='Results']/.."

    def open_calculator(self):
        """Open driver to calculator page."""
        self.driver.open(self.CALCULATOR_URL)

    def declare_number_of_debts(self, debts: str):
        """How many debts do you want to include in your plan?"""
        input_box = self.driver.get_element(self.DEBT_COUNT_INPUT)
        self.driver.type(input_box, debts)

    def declare_additional_income(self, number: str):
        """
        Do you expect any additional income income that you
        can apply to your payments?
        """
        input_box = self.driver.get_element(self.ADDITIONAL_INCOME_INPUT)
        self.driver.type(input_box, number)

    def declare_extra_payments(self, number: str):
        """
        If you have a lot of high interest rate debt to pay down,
        then it is best to pay that down instead of saving at a low rate.
        """
        input_box = self.driver.get_element(self.EXTRA_PAYMENT_INPUT)
        self.driver.type(input_box, number)

    def select_tax_bracket(self, bracket: str, default_bracket: str="10"):
        """What tax bracket are you in?"""
        drop_down = self.driver.get_element(default_bracket)
        drop_down.click()
        self.driver.driver.find_element_by_xpath(
            f"//span[text()='{tax_brackets.get(bracket)}']"
        ).click()

    def select_loan_type(self, index: int, loan_type: int):
        """Add loan type."""
        loan_type_drop_down = self.driver.get_element(f"loanType{index}")
        loan_type_drop_down.click()
        self.driver.driver.find_elements_by_xpath(
            f"//span[text()='{loan_types.get(loan_type)}']"
        )[index].click()

    def select_additional_income_type(self, index: int, income_type: str):
        """Select Windfall or Raise"""
        income_type_drop_down = self.driver.get_element(
            self.ADDITIONAL_INCOME_TYPE_DROP_DOWN.format(index=index)
        )
        income_type_drop_down.click()
        self.driver.driver.find_elements_by_xpath(
            f"//span[text()='{income_type}']"
        )[index].click()

    def add_credit_card(self, index: int, card: Loan):
        """Adding basic Credit card or retailer charge card"""
        self.select_loan_type(index, 0)
        loan_name_input = self.driver.get_element(
            self.CARD_LENDER_NAME_INPUT.format(index=index)
        )
        self.driver.type(loan_name_input, card.lender_name)
        remaining_balance_input = self.driver.get_element(
            self.CARD_BALANCE_INPUT.format(index=index)
        )
        self.driver.type(remaining_balance_input, card.balance)
        interest_rate = self.driver.get_element(
            self.CARD_INTEREST_RATE_INPUT.format(index=index)
        )
        self.driver.type(interest_rate, card.interest_rate)
        min_payment = self.driver.get_element(
            self.CARD_MIN_PAYMENT_INPUT.format(index=index)
        )
        self.driver.type(min_payment, card.min_monthly_payment)
        if card.promo_details:
            self.add_credit_card_with_promo_rate(index=index, card=card)

    def add_loan(self, index: int, loan: Loan):
        """Adding basic loan"""
        self.select_loan_type(index, 4)
        lender_name_input = self.driver.get_element(
            self.OTHER_LOAN_LENDER_NAME_INPUT.format(index=index)
        )
        self.driver.type(lender_name_input, loan.lender_name)
        loan_balance_input = self.driver.get_element(
            self.OTHER_LOAN_BALANCE_INPUT.format(index=index)
        )
        self.driver.type(loan_balance_input, loan.balance)
        interest_rate = self.driver.get_element(
            self.OTHER_LOAN_INTEREST_RATE_INPUT.format(index=index)
        )
        self.driver.type(interest_rate, loan.interest_rate)
        monthly_payment = self.driver.get_element(
            self.OTHER_LOAN_MONTHLY_PAYMENT_INPUT.format(index=index)
        )
        self.driver.type(monthly_payment, loan.min_monthly_payment)
        if loan.deductible:
            tax_deductible_option = self.driver.driver.find_element_by_xpath(
                self.OTHER_LOAN_TAX_DEDUCTIBLE_RADIO_OPTION.format(index=index)
            )
            self.close_promo()
            tax_deductible_option.click()

    def add_credit_card_with_promo_rate(self, index: int, card: Loan):
        """Adding card with special promo rate."""
        promo_option = self.driver.driver.find_element_by_xpath(
            self.PROMO_RATE_RADIO_OPTION.format(index=index)
        )
        promo_option.click()
        intro_rate = self.driver.get_element(
            self.CARD_PROMO_RATE.format(index=index)
        )
        self.driver.type(intro_rate, card.promo_details.promo_rate)
        date_picker = self.driver.driver.find_element_by_xpath(
            self.CARD_PROMO_END_DATE.format(index=index)
        )
        date_picker.click()
        DatePicker(webdriver=self.driver, date=card.promo_details.end_date)

    def add_windfalls(self, index: int, windfall: Windfall):
        """If windfalls add them"""
        self.select_additional_income_type(index=index, income_type="Windfall")
        monthly_amount_input = self.driver.get_element(
            self.ADDITIONAL_INCOME_MONTHLY_AMOUNT.format(index=index)
        )
        self.driver.type(monthly_amount_input, windfall.amount)
        date_picker = self.driver.driver.find_element_by_xpath(
            self.ADDITIONAL_INCOME_WINDFALL_DATE.format(index=index+1)
        )
        date_picker.click()
        DatePicker(webdriver=self.driver, date=windfall.date)

    def press_calculate(self):
        button = self.driver.driver.find_element_by_css_selector(
            self.CALCULATE_BUTTON
        )
        button.click()
        self.driver.wait_for_element_to_be_present(By.XPATH, self.RESULTS_DIV)

    def generate_plan(self, page_name: str):
        """Save Results table to file."""
        self.press_calculate()
        results = self.driver.driver.find_element_by_xpath(self.RESULTS_DIV)
        results_html = results.get_attribute('innerHTML')
        with open(f"plans/{page_name}.html", "w") as web_page:
            LOGGER.info(f"Saving {page_name}.html")
            web_page.write(str(results_html))

    def close_promo(self):
        try:
            promo_button = self.driver.driver.find_element_by_css_selector(
                "button[title='Close']"
            )
            if promo_button:
                LOGGER.info("Promo found.")
                if promo_button.is_displayed():
                    LOGGER.info("Promo displayed.")
                    promo_button.click()
                    LOGGER.info("Promo clicked.")
                    self.driver.wait_for_element_to_not_be_visible(
                        By.CSS_SELECTOR, "button[title='Close']"
                    )
                    LOGGER.info("Promo supposedly not visible.")
        except NoSuchElementException:
            LOGGER.info("No promo button found.")
