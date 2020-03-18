from typing import List

from wrapped_driver import WebElement


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


def send_keys_recursive(element: WebElement, value: str):
    """***WARNING RECURSIVE METHOD***

        A very forceful method that assures that the text that is passed in
        is the same text typed into the element input. A recursive loop is
        possible, especially if input value has a space at the end.
    """
    element.clear()
    for character in value:
        element.send_keys(character)
    element_value = element.get_attribute("value")
    try:
        assert element_value == value
    except AssertionError:
        send_keys_recursive(element=element, value=value)
