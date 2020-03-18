"""
    Use page object to use debt pay down calculator
"""
import logging
import json
import sys
from datetime import datetime

from wrapped_driver import WrappedDriver

from calculator_page import Calculator, loan_types, Windfall, Loans

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    stream=sys.stdout,
)
LOGGER = logging.getLogger(__name__)


class CalculatorClient:
    def __init__(self, plan_name: str, user_json: dict):
        self.plan_name = plan_name
        self.user_loans = Loans(user_json.get("loans"))
        self.loan_count = str(len(self.user_loans))
        self.user_info = user_json.get("user")
        self.tax_bracket = self.user_info.get("tax_bracket")
        self.budget_cuts = self.user_info.get("budget_savings")
        self.future_raises = self.user_info.get("raises")
        self.windfalls = [Windfall(**wf) for wf in user_json.get("windfalls")]
        LOGGER.info("Instantiated CalculatorClient")

    def __call__(self, webdriver: WrappedDriver, *args, **kwargs):
        self.calculator = Calculator(webdriver=webdriver)
        self.calculator.open_calculator()
        self.calculator.declare_number_of_debts(debts=self.loan_count)
        for count, user_loan in enumerate(self.user_loans):
            LOGGER.info(f"Loan: {user_loan}")
            self.calculator.close_promo()
            if user_loan.loan_type == loan_types.get(0):
                self.calculator.add_credit_card(index=count, card=user_loan)
            elif user_loan.loan_type == loan_types.get(4):
                self.calculator.add_loan(index=count, loan=user_loan)
        self._wrap_up_steps()

    def __repr__(self):
        return self.plan_name

    def _wrap_up_steps(self):
        if self.windfalls:
            self.calculator.declare_additional_income(number=str(len(self.windfalls)))
            for count, windfall in enumerate(self.windfalls):
                self.calculator.add_windfalls(index=count, windfall=windfall)
        else:
            self.calculator.declare_additional_income(number="0")
        self.calculator.declare_extra_payments(number=self.budget_cuts)
        self.calculator.select_tax_bracket(bracket=self.tax_bracket)
        self.calculator.generate_plan(
            page_name=f"{self.plan_name}-{self.budget_cuts}-savings"
        )
        self.calculator.driver.quit_driver()


if __name__ == "__main__":
    name = "latest-plan"
    config_file_name = f"plan_configs/{name}-config.json"
    LOGGER.info(f"Opening {config_file_name}....")
    with open(config_file_name, "r") as loan_json:
        loaded_json = json.load(loan_json)

    client = CalculatorClient(
        plan_name=f"{datetime.now().date()}-{name}", user_json=loaded_json
    )
    driver = WrappedDriver(
        chrome_driver_path="/Users/brian/bin/chromedriver", browser="headless"
    )
    client(webdriver=driver)
