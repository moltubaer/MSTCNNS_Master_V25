from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, NoAlertPresentException
from time import sleep

BASE_URL = "http://localhost:5000"
BASE_IMSI = 208930000000000
TOTAL_SUBSCRIBERS = 1000  # scale up now that it's working

USERNAME = "admin"
PASSWORD = "free5gc"

options = Options()
driver = webdriver.Firefox(options=options)

def wait_until(condition_func, timeout=10):
    for _ in range(timeout * 10):
        try:
            if condition_func():
                return True
        except:
            pass
        sleep(0.1)
    raise TimeoutException("Timed out waiting for condition")

def login():
    print("🔐 Logging in...")
    driver.get(BASE_URL)
    sleep(2)

    email_input = driver.find_element(By.NAME, "email")
    password_input = driver.find_element(By.NAME, "password")

    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.ENTER)

    wait_until(lambda: "/login" not in driver.current_url, timeout=15)
    print(f"✅ Logged in. Current URL: {driver.current_url}")
    sleep(5)  # Let session settle

def wait_for_url_contains(substring, timeout=10):
    for _ in range(timeout * 10):
        if substring in driver.current_url:
            return True
        sleep(0.1)
    raise TimeoutException(f"Timed out waiting for URL containing '{substring}'")

def create_subscriber(imsi_number, sdn_number):
    imsi = f"imsi-{imsi_number:015d}"
    sdn = str(sdn_number)

    print(f"➡️  Creating subscriber {imsi}")
    driver.get(f"{BASE_URL}/subscriber/create")
    sleep(2)

    if "/login" in driver.current_url:
        raise Exception("❌ Session expired. Redirected to login.")

    supi_input = driver.find_element(By.NAME, "ueId")
    sdn_input = driver.find_element(By.NAME, "userNumber")

    supi_input.clear()
    supi_input.send_keys(imsi)

    sdn_input.clear()
    sdn_input.send_keys(sdn)

    sleep(0.3)
    supi_input.send_keys(Keys.ENTER)

    try:
        # Wait for redirect to /subscriber
        wait_for_url_contains("/subscriber", timeout=5)
        print(f"✅ Subscriber {imsi} created.")
    except TimeoutException:
        try:
            # Look for JavaScript alert (duplicate IMSI warning)
            alert = driver.switch_to.alert
            print(f"⚠️  Duplicate IMSI {imsi}: {alert.text}")
            alert.accept()
            sleep(1)
        except NoAlertPresentException:
            raise Exception(f"❌ Failed on IMSI {imsi}: no alert, no redirect.")

# Step 1: Login
login()

# Step 2: Create subscribers
for i in range(1, TOTAL_SUBSCRIBERS + 1):
    try:
        imsi_num = BASE_IMSI + i
        create_subscriber(imsi_num, i)
    except Exception as e:
        print(f"❌ Error on IMSI {BASE_IMSI + i:015d}: {e}")
        continue  # continue on to next IMSI

print("✅ All subscribers processed.")
driver.quit()
