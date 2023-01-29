import totp
import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


class Login:
    # Private Variable
    __base_url = 'https://kite.zerodha.com'
    __enc_cookies = None

    def __init__(self, user_id=None, password=None, totp_key=None):
        """
        Login Account For saving cookies to accessing zerodha data
        """

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        driver.implicitly_wait(3)
        driver.get(self.__base_url)

        if user_id is not None:
            driver.find_element(By.XPATH, "//input[@id='userid']").send_keys(user_id)

        if password is not None:
            driver.find_element(By.XPATH, "//input[@id='password']").send_keys(password)

        if user_id is not None and password is not None:
            driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()

            sleep(3)

            if totp_key is not None:
                totp = pyotp.TOTP(totp_key).now()
                driver.find_element(By.XPATH, "//input[@type='text']").send_keys(totp)

        sleep(3)
        login_success = False

        for _ in range(40):
            # get enctoken
            cookies_data = pd.DataFrame(driver.get_cookies()).set_index('name')
            if 'enctoken' in cookies_data.index:
                self.__enc_cookies = cookies_data.loc['enctoken', 'value']
                login_success = True
                break
            sleep(5)

        driver.close()

        print('Login Successfull :)') if login_success else print('Something Wrong !!!')

    def get_enc_cookie(self):
        if self.__enc_cookies is None:
            print('Login Again !!!')
            return self.__enc_cookies
        else:
            return self.__enc_cookies
