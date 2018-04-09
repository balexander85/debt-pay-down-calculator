"""
Page objects for the debt pay down calculator
"""
from util.wrapped_webdriver import WrappedWebDriver
from debt_pay_down_calculator import Loan


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


class BasePage:
    """Base page object to share common objects and methods"""

    def __init__(self, webdriver: WrappedWebDriver):
        self.driver = webdriver


class Calculator(BasePage):
    """The overall calculator on the page"""

    CALCULATOR_URL = (
        "https://www.bankrate.com/calculators/managing-debt"
        "/debt-pay-down-calculator.aspx"
    )
    CALCULATOR_CONTAINER = "debt-pay-down-calculator"
    DEBT_COUNT_INPUT = "debtCount"
    ADDITIONAL_INCOME_INPUT = "additionalIncomeCount"
    EXTRA_PAYMENT_INPUT = "extraPayment"
    CARD_LENDER_NAME_INPUT = "lenderNamecreditCardLoan{index}"
    CARD_BALANCE_INPUT = "amountcreditCardLoan{index}"
    CARD_INTEREST_RATE_INPUT = "interestRatecreditCardLoan{index}"
    CARD_MIN_PAYMENT_INPUT = "monthlyPaymentcreditCardLoan{index}"
    CARD_PROMO_RATE = "introductoryRatecreditCardLoan{index}"
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
    CALCULATE_BUTTON = "div.grid-cell.size-1of3.\+center-content button"
    RESULTS_DIV = "//h5[text()='Results']/.."

    def declare_number_of_debts(self, debts):
        """How many debts do you want to include in your plan?"""
        input_box = self.driver.get_element(self.DEBT_COUNT_INPUT)
        self.driver.type(input_box, debts)

    def declare_additional_income(self, number):
        """
        Do you expect any additional income income that you
        can apply to your payments?
        """
        input_box = self.driver.get_element(self.ADDITIONAL_INCOME_INPUT)
        self.driver.type(input_box, number)

    def declare_extra_payments(self, number):
        """
        If you have a lot of high interest rate debt to pay down,
        then it is best to pay that down instead of saving at a low rate.
        """
        input_box = self.driver.get_element(self.EXTRA_PAYMENT_INPUT)
        self.driver.type(input_box, number)

    def select_tax_bracket(self, bracket, default_bracket="10"):
        """What tax bracket are you in?"""
        drop_down = self.driver.get_element(default_bracket)
        drop_down.click()
        self.driver.driver.find_element_by_xpath(
            f"//span[text()='{tax_brackets.get(bracket)}']"
        ).click()

    def select_loan_type(self, index, loan_type):
        """Add loan type."""
        loan_type_drop_down = self.driver.get_element(f"loanType{index}")
        loan_type_drop_down.click()
        self.driver.driver.find_elements_by_xpath(
            f"//span[text()='{loan_types.get(loan_type)}']"
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

    def add_windfalls(self, index):
        """If windfalls add them"""
        return self, index

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

    def press_calculate(self):
        button = self.driver.driver.find_element_by_css_selector(
            self.CALCULATE_BUTTON
        )
        button.click()

    def generate_plan(self, page_name):
        """Save Results table to file."""
        self.press_calculate()
        results = self.driver.driver.find_element_by_xpath(self.RESULTS_DIV)
        results_html = results.get_attribute('innerHTML')
        with open(f"plans/{page_name}.html", "w") as web_page:
            web_page.write(str(results_html))
