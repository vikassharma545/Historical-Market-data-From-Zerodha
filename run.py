from login import login
from stock_data import stock_data

if __name__ == '__main__':

    print("""         Login Zerodha            """)
    user_id = input('Enter User ID : ')
    pwd = input('Enter Passward :')

    zerodha = login(user_id=user_id, password=pwd, totp=totp)

    z_data = stock_data(zerodha.enc_cookies)



