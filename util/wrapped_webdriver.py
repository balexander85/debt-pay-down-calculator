
from typing import List

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options


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

    @staticmethod
    def type(element: WebElement, value):
        element.clear()
        element.send_keys(value)

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

    # def get_element_attr_value(self, locator, attr):
    #     element = self.get_element(locator=locator)
    #     return element.get_attribute(attr)
    #
    # def hover(self, locator):
    #     """
    #         Move mouse over locator element
    #     """
    #     element = self.get_element(locator=locator)
    #     ActionChains(self.driver).move_to_element(element).perform()

    # def wait_for_element_attribute_has_value(self, element, attribute, value):
    #     """
    #         Wait for given element to have the given attribute and return bool
    #     """
    #     def element_has_attribute(ele, attrib, val):
    #         """Assert element has attribute"""
    #         return ele.get_attribute(attrib) == val
    #
    #     WebDriverWait(self.driver, timeout=120).until(
    #         element_has_attribute(element, attribute, value),
    #         "Element does not have value"
    #     )


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
