import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

class login:
    # Private Variable
    __base_url = 'https://kite.zerodha.com'
    ___user_id = ''
    __password = ''
    __totp = ''

    # public Variable
    enc_cookies = None

    def __init__(self, user_id, password, totp=None):
        """
        Login Account For download data
        """
        self.___user_id = user_id
        self.__password = password
        self.__totp = totp

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        driver.implicitly_wait(3)
        driver.get(self.__base_url)
        driver.find_element(By.XPATH, "//input[@id='userid']").send_keys(self.___user_id)
        driver.find_element(By.XPATH, "//input[@id='password']").send_keys(self.__password)
        driver.find_element(By.XPATH, "//button[normalize-space()='Login']").click()
        sleep(3)

        if totp != None:
            driver.find_element(By.XPATH, "//input[@type='text']").send_keys(self.__totp)
            sleep(1)
            driver.find_element(By.XPATH, "//button[normalize-space()='Continue']").click()

        sleep(3)
        login_success = False
        for _ in range(40):

            # get enctoken
            cookies_data = pd.DataFrame(driver.get_cookies()).set_index('name')
            if 'enctoken' in cookies_data.index:
                self.enc_cookies = cookies_data.loc['enctoken', 'value']
                login_success = True
                break
            sleep(5)

        driver.close()

        if login_success:
            print('Login Successfull :)')
        else:
            print('Something Wrong !!!')