"""
    Use page object to use debt pay down calculator
"""
import json

from util.wrapped_webdriver import WrappedWebDriver
from debt_pay_down_calculator import Loans
from calculator_page import Calculator, loan_types


class CalculatorClient:

    def __init__(self, plan_name: str, user_json: dict):
        self.plan_name = plan_name
        self.user_loans = Loans(user_json.get("loans"))
        self.loan_count = len(self.user_loans)
        self.user_info = user_json.get("user")
        self.tax_bracket = self.user_info.get("tax_bracket")
        self.budget_cuts = self.user_info.get("budget_savings")
        self.future_raises = self.user_info.get("raises")
        # self.windfalls = [
        #     Windfall(**wf) for wf in user_json.get("windfalls")
        # ]
        self.windfalls = 0

    def __call__(self, webdriver: WrappedWebDriver, *args, **kwargs):
        self.calculator = Calculator(webdriver=webdriver)
        webdriver.open(self.calculator.CALCULATOR_URL)
        self.calculator.declare_number_of_debts(self.loan_count)
        for count, user_loan in enumerate(self.user_loans):
            if user_loan.loan_type == loan_types.get(0):
                self.calculator.add_credit_card(index=count, card=user_loan)
            elif user_loan.loan_type == loan_types.get(4):
                self.calculator.add_loan(index=count, loan=user_loan)
        self._wrap_up_steps()

    def __repr__(self):
        return self.plan_name

    def _wrap_up_steps(self):
        self.calculator.declare_additional_income(number=self.windfalls)
        self.calculator.declare_extra_payments(number=self.budget_cuts)
        self.calculator.select_tax_bracket(bracket=self.tax_bracket)
        self.calculator.generate_plan(page_name=self.plan_name)
        self.calculator.driver.quit_driver()

if __name__ == "__main__":
    driver = WrappedWebDriver(browser="chrome")
    with open("plan_configs/example-plan-config.json", "r") as loan_json:
        loaded_json = json.load(loan_json)

    client = CalculatorClient(plan_name="example-plan", user_json=loaded_json)
    client(webdriver=driver)
