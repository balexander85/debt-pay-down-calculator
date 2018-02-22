"""
    I found this nifty debt pay down calculator on bankrate.com
    but to use it you have to manually go through all these steps
    to generate a debt pay down plan. I wanted to be able to setup
    my loans and credit cards with balances and info saved and then
    run a script to generate a plan. Then I could make tweaks to my
    details and generate a new plan. Based on outcomes of my tweaks
    I could then take action on the plan that has the best outcome.
"""
import logging
import json
import os
import sys
from typing import List

import requests
from bs4 import BeautifulSoup


logging.basicConfig(
    level=logging.ERROR,
    format="%(levelname)7s: %(message)s",
    stream=sys.stdout,
)

LOG = logging.getLogger("")

loan_types = {
    "Credit card or retailer charge card": 0,
    "Car, truck, motorcycle, or boat loan": 1,
    "Home equity loan": 2,
    "Mortgage": 3,
    "Other kind of loan": 4
}

promo_types = {
    "A low introductory interest rate that will increase at a later date": 0,
    "No payments are due until a later date": 1,
    "No special promotion on this card": 2
}

tax_brackets = {
    "10% (up to $7,825 single; up to $15,650 married)": "10",
    "15% ($7,826-$31,850 single; $15,651-$63,700 married)": "15",
    "25% ($31,851-$77,100 single; $63,701-$128,500 married)": "25",
    "28% ($77,101-$160,850 single; $128,501-$195,850 married)": "28",
    "33% ($169,851-$349,700 single; $195,851-$349,700 married)": "33",
    "35% ($349,701 or more)": "35"
}


class Windfall:
    """
        Cash 'windfalls': Any one-time events that will
        increase the cash you have in a given month
    """
    def __init__(self, amount: str, date: str):
        self.amount = amount
        self.date = date


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


class DebtCalculatorClient:
    """
        Client used to interact with the debt-pay-down-calculator.aspx
    """

    url = "https://www.bankrate.com/calculators/managing-debt" \
          "/debt-pay-down-calculator.aspx"

    def __init__(
            self,
            plan_name: str,
            number_of_debts: int,
            user_info: dict,
            windfalls: List[Windfall]
    ):
        self.session = requests.Session()
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/webp,image/apng,*/*;q=0.8",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "path": "/calculators/managing-debt/debt-pay-down-calculator.aspx",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/64.0.3282.140 Safari/537.36"
        }
        self.plan_name = plan_name
        self.loan_count = number_of_debts
        self.tax_bracket = user_info.get("tax_bracket")
        self.budget_cuts = user_info.get("budget_savings")
        self.future_raises = user_info.get("raises")
        self.windfalls = windfalls
        self.view_state = None
        self.declare_number_of_debts()

    def __enter__(self):
        """
        Context Manager so one can use this object With

        :example    with DebtCalculatorClient() as client:
                        client.add_loan()

        :return: self
        """
        return self

    def __exit__(self, *args):
        """
            Basically the wrap-up method, After all the
            loan info is inserted continue on to the budget,
            savings, raises and finally generating the
            debt pay down plan
        """
        self.continue_to_saving_options()
        self.budget_savings()
        self.forecasted_raises()
        self.forecasted_windfalls()
        self.select_tax_bracket()
        self.generate_plan()
        LOG.info("Debt Pay Down Plan Generated")

    def submit_request(self, params) -> requests.Response:
        """
            Just a wrapper for posting requests
        """
        params.update({"__VIEWSTATE": self.view_state})
        post_response = self.session.post(
            self.url, data=params, headers=self.headers
        )
        self.view_state = get_view_state(post_response)
        # save_page(post_response, "submit-request")
        return post_response

    def declare_number_of_debts(self):
        """
            First question:
            How many debts do you want to include in your plan?
        """
        self.view_state = get_view_state(
            self.session.get(self.url, headers=self.headers)
        )
        params = {
            "ctl00$well$defaultUC$isValid": "DEFAULT",
            "ctl00$well$defaultUC$debts": self.loan_count
        }
        self.submit_request(params=params)

    def post_lender_name_and_loan_type(self, loan: Loan):
        """
            Second question:
            Type of loan:
                * Credit card or retailer charge card
                * Car, truck, motorcycle, or boat loan
                * Home equity loan
                * Mortgage
                * Other kind of loan
        """
        params = {
            "ctl00$well$defaultUC$isValid": "LT",
            "ctl00$well$defaultUC$lenderNameLT": loan.lender_name,
            "ctl00$well$defaultUC$AnswerLT": loan_types.get(loan.loan_type)
        }
        self.submit_request(params=params)

    def enter_loan_balance(self, loan: Loan):
        """
              Add total of balance of debt
        """
        params = {
            "ctl00$well$defaultUC$isValid": "LB",
            "ctl00$well$defaultUC$lenderNameLB": loan.lender_name,
            "ctl00$well$defaultUC$loanBalanceLB": loan.balance,
        }
        self.submit_request(params=params)

    def enter_loan_details(self, loan: Loan):
        """
              Enter details of the loan
        """
        params = {
            "ctl00$well$defaultUC$isValid": "OL",
            "ctl00$well$defaultUC$currMonthlyPaymentOL":
                loan.min_monthly_payment,
            "ctl00$well$defaultUC$interestRateOL": loan.interest_rate,
            "ctl00$well$defaultUC$selectedOL": loan.deductible
        }
        self.submit_request(params=params)

    def is_change_loan_details(self, change: str):
        """
              Will the interest rate or payment amount
              change in the future on this loan?
        """
        params = {
            "ctl00$well$defaultUC$isValid": "",
            "ctl00$well$defaultUC$selectedICONIF": change,
            "ctl00$well$defaultUC$SubmitICONIF": "Submit"
        }
        self.submit_request(params=params)

    def select_promo_type(self, promo_type: str):
        """
            Add the type of promo if applicable
        """
        params = {
            "ctl00$well$defaultUC$isValid": "",
            "ctl00$well$defaultUC$AnswerPT": promo_types.get(promo_type),
            "ctl00$well$defaultUC$SubmitPT": "Submit",

        }
        self.submit_request(params=params)

    def post_promo_details(self, promo: Promotion):
        """
            Add the type of promo if applicable
        """
        params = {
            "ctl00$well$defaultUC$isValid": "LIIR",
            "ctl00$well$defaultUC$introInterestLIIR": promo.promo_rate,
            "ctl00$well$defaultUC$currMinPaymentLIIR":
                promo.minimum_monthly_payment,
            "ctl00$well$defaultUC$introEndsLIIR": promo.end_date,
            "ctl00$well$defaultUC$normalInterestLIIR": promo.regular_rate,

        }
        self.submit_request(params=params)

    def add_interest_rate_and_payments(self, loan: Loan):
        """
            Enter the interest rate and Minimum Monthly Payment
        """
        params = {
            "ctl00$well$defaultUC$isValid": "NSP",
            "ctl00$well$defaultUC$interestRateNSP": loan.interest_rate,
            "ctl00$well$defaultUC$minMonthlyPaymentNSP":
                loan.min_monthly_payment,

        }
        self.submit_request(params=params)

    def continue_to_saving_options(self):
        """
            Your monthly budget savings: Money from your current
             budget that you can apply to your debts
            Income raises: Any anticipated raise to your monthly
             income that you can apply to your debts
            Cash 'windfalls': Any one-time events that will
             increase the cash you have in a given month
        """
        params = {
            "ctl00$well$defaultUC$isValid": "",
            "ctl00$well$defaultUC$SubmitGIAL": "Continue"

        }
        self.submit_request(params=params)

    def budget_savings(self):
        """
            Your monthly budget savings: Money from your current
             budget that you can apply to your debts
        """
        params = {
            "ctl00$well$defaultUC$isValid": "AMC",
            "ctl00$well$defaultUC$additionPayAMC": self.budget_cuts

        }
        self.submit_request(params=params)

    def forecasted_raises(self):
        """
            Income raises: Any anticipated raise to your monthly
             income that you can apply to your debts
        """
        params = {
            "ctl00$well$defaultUC$isValid": "NOR",
            "ctl00$well$defaultUC$numberOfRaisesNOR": self.future_raises
        }
        self.submit_request(params=params)

    def forecasted_windfalls(self):
        """
            Cash 'windfalls': Any one-time events that will
             increase the cash you have in a given month
        """
        amount = len(self.windfalls)
        params = {
            "ctl00$well$defaultUC$isValid": "NOW",
            "ctl00$well$defaultUC$windFallNOW": amount,
        }
        self.submit_request(params=params)
        if amount <= 0:
            pass
        else:
            self.add_windfalls()

    def select_tax_bracket(self):
        """
            Add the type of promo if applicable
        """
        params = {
            "ctl00$well$defaultUC$isValid": "",
            "ctl00$well$defaultUC$AnswerSTB": tax_brackets.get(
                self.tax_bracket
            ),
            "ctl00$well$defaultUC$SubmitSTB": "Submit"

        }
        self.submit_request(params=params)

    def add_loan(self, loan: Loan):
        self.post_lender_name_and_loan_type(loan=loan)
        self.enter_loan_balance(loan=loan)
        if loan.loan_type == "Other kind of loan":
            self.enter_loan_details(loan=loan)
            self.is_change_loan_details(change="1")
        else:
            self.add_credit_card(loan=loan)

    def add_credit_card(self, loan: Loan):
        """
            This path covers loan types of Credit card or retailer charge card
        """
        if loan.promo_details:
            self.select_promo_type(promo_type=loan.promo_details.promo_type)
            self.post_promo_details(promo=loan.promo_details)
        else:
            self.select_promo_type(
                promo_type="No special promotion on this card"
            )
            self.add_interest_rate_and_payments(loan=loan)

    def add_windfalls(self):
        """If windfalls add them"""
        params = {
            "ctl00$well$defaultUC$isValid": "",
            "ctl00$well$defaultUC$SubmitWI": "Submit"
        }
        for count, windfall in enumerate(self.windfalls, start=1):
            params.update(
                {f"ctl00$well$defaultUC$SalAmountWI{count}": windfall.amount}
            )
            params.update(
                {f"ctl00$well$defaultUC$SalDateWI{count}": windfall.date}
            )
        self.submit_request(params=params)

    def add_raises(self):
        """If windfalls add them"""
        raise NotImplementedError

    def generate_plan(self):
        """
            Add the type of promo if applicable
        """
        params = {
            "ctl00$well$defaultUC$isValid": "",
            "ctl00$well$defaultUC$SubmitNOMTP": "Get Plan",

        }
        response = self.submit_request(params=params)
        save_page(page_response=response, page_name=self.plan_name)


def save_page(page_response: requests.Response, page_name: str):
    soup = BeautifulSoup(page_response.content, "html.parser")
    with open(f"plans/{page_name}.html", "w") as web_page:
        web_page.write(str(soup.select_one("div.calculator")))


def get_view_state(page_response: requests.Response) -> str:
    soup = BeautifulSoup(page_response.content, "html.parser")
    return soup.select_one("input#__VIEWSTATE").attrs.get("value")


if __name__ == "__main__":

    for plan in os.listdir("plan_configs"):
        with open(f"plan_configs/{plan}", "r") as loan_json:
            loaded_json = json.load(loan_json)
            user_loans = Loans(loaded_json.get("loans"))
            user_windfalls = [
                Windfall(**wf) for wf in loaded_json.get("windfalls")
            ]
            user = loaded_json.get("user")

        with DebtCalculatorClient(
                plan_name=plan.replace(".json", ""),
                number_of_debts=len(user_loans),
                user_info=user,
                windfalls=user_windfalls
        ) as debt_calculator:
            for user_loan in user_loans:
                debt_calculator.add_loan(loan=user_loan)
