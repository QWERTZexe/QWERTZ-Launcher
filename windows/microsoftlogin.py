#!/usr/bin/env python3
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel
from PyQt5.QtCore import QUrl, QLocale
from PyQt5.QtGui import QPixmap
import minecraft_launcher_lib
import json
import sys
import os

CLIENT_ID = "3d006e3a-abc5-4c7f-af37-d4f2104128f5"
REDIRECT_URL = "https://login.microsoftonline.com/common/oauth2/nativeclient/"


class LoginWindow(QWebEngineView):
    username = ""
    token = ""
    uuid = ""
    def __init__(self):
        super().__init__()
        cwd = os.path.dirname(sys.argv[0])
        self.setWindowTitle("Logging in to microsoft")
        # Set the path where the refresh token is saved
        self.refresh_token_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "refresh_token.json")
        pic = QLabel(self)
        pic.setPixmap(QPixmap(f"{cwd}\\success.png"))
        pic.show() # You were missing this.
        # Login with refresh token, if it exists
        if os.path.isfile(self.refresh_token_file):
            with open(self.refresh_token_file, "r", encoding="utf-8") as f:
                refresh_token = json.load(f)
                # Do the login with refresh token
                try:
                    account_informaton = minecraft_launcher_lib.microsoft_account.complete_refresh(CLIENT_ID, None, REDIRECT_URL, refresh_token)
                    self.token =account_informaton["access_token"]
                    self.username =account_informaton["name"]
                    self.uuid=account_informaton["id"]
                    secrets = [self.token,self.username,self.uuid]
                    cwd = os.path.dirname(sys.argv[0])
                    with open(f"{cwd}\\secrets.txt","w") as f:
                        f.write('\n'.join(secrets) + '\n')
                   # print(self.uuid)
                    self.show_account_information(account_informaton)
                    pic = QLabel(self)
                    pic.setPixmap(QPixmap(f"{cwd}\\success.png"))

                    pic.show() # You were missing this.
                # Show the window if the refresh token is invalid
                except minecraft_launcher_lib.exceptions.InvalidRefreshToken:
                    pass

        # Open the login url
        login_url, self.state, self.code_verifier = minecraft_launcher_lib.microsoft_account.get_secure_login_data(CLIENT_ID, REDIRECT_URL)
        self.load(QUrl(login_url))

        # Connects a function that is called when the url changed
        self.urlChanged.connect(self.new_url)

        self.show()
    def new_url(self, url: QUrl):
        try:
            # Get the code from the url
            auth_code = minecraft_launcher_lib.microsoft_account.parse_auth_code_url(url.toString(), self.state)
            # Do the login
            account_information = minecraft_launcher_lib.microsoft_account.complete_login(CLIENT_ID, None, REDIRECT_URL, auth_code, self.code_verifier)
            # Show the login information
            self.token =account_information["access_token"]
            self.username =account_information["name"]
            self.uuid=account_information["id"]
            secrets = [self.token,self.username,self.uuid]
            cwd = os.path.dirname(sys.argv[0])
            with open(f"{cwd}\\secrets.txt","w") as f:
                f.write('\n'.join(secrets) + '\n')
                              
            pic = QLabel(self)
            pic.setPixmap(QPixmap(f"{cwd}\\success.png"))

            pic.show() # You were missing this.
            self.show_account_information(account_information)
        except AssertionError:
            print("States do not match!")
        except KeyError:
            print("Url not valid")

    def show_account_information(self, information_dict):
        information_string = f'Username: {information_dict["name"]}<br>'
        information_string += f'UUID: {information_dict["id"]}<br>'
        information_string += f'Token: {information_dict["access_token"]}<br>'
        # Save the refresh token in a file
        with open(self.refresh_token_file, "w", encoding="utf-8") as f:
            json.dump(information_dict["refresh_token"], f, ensure_ascii=False, indent=4)

        message_box = QMessageBox()
        message_box.setWindowTitle("Account information")
        message_box.setText(information_string)
        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
      #  message_box.exec()

        # Exit the program


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # This line sets the language of the webpage to the system language
    QWebEngineProfile.defaultProfile().setHttpAcceptLanguage(QLocale.system().name().split("_")[0])
    w = LoginWindow()
    sys.exit(app.exec())