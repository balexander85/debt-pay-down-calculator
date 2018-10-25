
from time import sleep
from typing import List

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


chromedriver_path = "/Users/brian/bin/chromedriver"
mobile_emulation = {"deviceName": "iPhone 6"}
chrome_options = Options()
chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)


class WrappedWebDriver:

    def __init__(self, browser="chrome"):
        if browser == "chrome":
            self.driver = webdriver.Chrome(executable_path=chromedriver_path)
        elif browser == "mobile":
            self.driver = webdriver.Chrome(
                executable_path=chromedriver_path,
                chrome_options=chrome_options
            )

    def open(self, url):
        self.driver.get(url)

    def close(self):
        self.driver.close()

    def quit_driver(self):
        self.driver.quit()

    def get_element(self, element_id):
        return self.driver.find_element_by_id(element_id)

    def click(self, locator):
        self.get_element(locator).click()

    def type(self, element: WebElement, value: str):
        """***WARNING RECURSIVE METHOD***

            A very forceful method that assures that the text that is passed in
            is the same text typed into the element input. A recursive loop is
            possible, especially if input value has a space at the end.
        """
        element.clear()
        element.send_keys(value)
        sleep(2)
        element_value = element.get_attribute('value')
        try:
            assert element_value == value
        except AssertionError:
            self.type(element=element, value=value)

    def locator_visible(self, locator):
        element = self.driver.find_element_by_css_selector(locator)
        return self.element_visible(element)

    @staticmethod
    def element_visible(element):
        return element.is_displayed()

    def get_current_url(self):
        return self.driver.current_url

    def get_window_handles(self):
        return self.driver.window_handles

    def switch_to_window(self, window):
        self.driver.switch_to.window(window)

    @property
    def switch_to_alert(self):
        return self.driver.switch_to.alert

    def wait_for_element_to_be_present(self, by, locator) -> bool:
        """Wait for element to be present"""
        return WebDriverWait(driver=self.driver, timeout=10).until(
            EC.presence_of_element_located((by, locator))
        )


def click_visible_element(elements: List[WebElement]):
    """
        Pass list of elements in and click the element
        that is visible there should only be one
    """
    element = [e for e in elements if e.is_displayed()]
    if len(element) == 1:
        element[0].click()
    else:
        raise Exception("More than one element is visible.")
