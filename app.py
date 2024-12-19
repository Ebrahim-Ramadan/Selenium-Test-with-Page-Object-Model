import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

# Page Objects
class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
    
    def find_element(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

class LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.url = "https://www.saucedemo.com/"
        
    def navigate(self):
        self.driver.get(self.url)
        
    def login(self, username, password):
        self.find_element(By.ID, "user-name").send_keys(username)
        self.find_element(By.ID, "password").send_keys(password)
        self.find_element(By.ID, "login-button").click()
        
    def get_error_message(self):
        return self.find_element(By.CLASS_NAME, "error-message-container").text

class InventoryPage(BasePage):
    def add_item_to_cart(self, item_name):
        self.find_element(By.XPATH, f"//div[text()='{item_name}']/../..//button").click()
        
    def remove_item_from_cart(self, item_name):
        self.find_element(By.XPATH, f"//div[text()='{item_name}']/../..//button[text()='Remove']").click()
        
    def get_cart_count(self):
        return int(self.find_element(By.CLASS_NAME, "shopping_cart_badge").text)
    
    def open_cart(self):
        self.find_element(By.CLASS_NAME, "shopping_cart_link").click()
        
    def sort_items(self, sort_option):
        select = Select(self.find_element(By.CLASS_NAME, "product_sort_container"))
        select.select_by_visible_text(sort_option)
        
    def get_item_price(self, item_name):
        return self.find_element(By.XPATH, f"//div[text()='{item_name}']/../..//div[@class='inventory_item_price']").text

class CartPage(BasePage):
    def checkout(self):
        self.find_element(By.ID, "checkout").click()
        
    def continue_shopping(self):
        self.find_element(By.ID, "continue-shopping").click()
        
    def get_cart_items(self):
        items = self.driver.find_elements(By.CLASS_NAME, "cart_item")
        return [item.find_element(By.CLASS_NAME, "inventory_item_name").text for item in items]

class CheckoutPage(BasePage):
    def fill_information(self, first_name, last_name, postal_code):
        self.find_element(By.ID, "first-name").send_keys(first_name)
        self.find_element(By.ID, "last-name").send_keys(last_name)
        self.find_element(By.ID, "postal-code").send_keys(postal_code)
        self.find_element(By.ID, "continue").click()
        
    def finish_checkout(self):
        self.find_element(By.ID, "finish").click()
        
    def get_total_price(self):
        return self.find_element(By.CLASS_NAME, "summary_total_label").text

# Test Data
TEST_USERS = [
    ("standard_user", "secret_sauce"),
    ("locked_out_user", "secret_sauce"),
    ("problem_user", "secret_sauce"),
    ("performance_glitch_user", "secret_sauce")
]

# Fixtures
@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()

@pytest.fixture
def login_page(driver):
    return LoginPage(driver)

@pytest.fixture
def inventory_page(driver):
    return InventoryPage(driver)

@pytest.fixture
def cart_page(driver):
    return CartPage(driver)

@pytest.fixture
def checkout_page(driver):
    return CheckoutPage(driver)

# Tests
@pytest.mark.parametrize("username,password", TEST_USERS)
def test_login(login_page, username, password):
    login_page.navigate()
    login_page.login(username, password)
    
    if username == "locked_out_user":
        assert "locked out" in login_page.get_error_message().lower()
    else:
        assert "inventory.html" in login_page.driver.current_url

def test_add_remove_cart(login_page, inventory_page):
    login_page.navigate()
    login_page.login("standard_user", "secret_sauce")
    
    # Add item
    inventory_page.add_item_to_cart("Sauce Labs Backpack")
    assert inventory_page.get_cart_count() == 1
    
    # Remove item
    inventory_page.remove_item_from_cart("Sauce Labs Backpack")
    with pytest.raises(Exception):
        inventory_page.get_cart_count()

def test_sort_functionality(login_page, inventory_page):
    login_page.navigate()
    login_page.login("standard_user", "secret_sauce")
    
    inventory_page.sort_items("Price (low to high)")
    first_item_price = float(inventory_page.get_item_price("Sauce Labs Onesie").replace("$", ""))
    inventory_page.sort_items("Price (high to low)")
    last_item_price = float(inventory_page.get_item_price("Sauce Labs Fleece Jacket").replace("$", ""))
    
    assert last_item_price > first_item_price

def test_complete_checkout_flow(login_page, inventory_page, cart_page, checkout_page):
    login_page.navigate()
    login_page.login("standard_user", "secret_sauce")
    
    # Add items to cart
    inventory_page.add_item_to_cart("Sauce Labs Backpack")
    inventory_page.add_item_to_cart("Sauce Labs Bike Light")
    
    # Go to cart
    inventory_page.open_cart()
    cart_items = cart_page.get_cart_items()
    assert "Sauce Labs Backpack" in cart_items
    assert "Sauce Labs Bike Light" in cart_items
    
    # Checkout process
    cart_page.checkout()
    checkout_page.fill_information("John", "Doe", "12345")
    total = checkout_page.get_total_price()
    assert "$" in total
    
    checkout_page.finish_checkout()
    assert "complete" in checkout_page.driver.current_url.lower()