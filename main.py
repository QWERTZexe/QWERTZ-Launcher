#Copyright (C) 2024  QWERTZexe

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published
#by the Free Software Foundation, either version 3 of the License, or
#any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.

######################################################

### MAIN ###

import sys, os, json, subprocess, shutil, zipfile
import uuid as uuuid
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QComboBox, QMessageBox, QToolBar, QGridLayout, QFrame,QMainWindow,QStyle,QStyleOption,QStylePainter,QScrollArea,QVBoxLayout,QMenu,QFileDialog,QDialog,QLineEdit,QLineEdit, QToolButton,QHBoxLayout,QHBoxLayout,QSizePolicy,QListWidget,QProgressBar,QVBoxLayout,QCheckBox,QListWidgetItem
from PyQt6.QtCore import Qt, QSize,QUrl,pyqtSignal,QThread
import minecraft_launcher_lib as mc
import threading, requests
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor,QImage,QPixmap,QAction
cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
os.chdir(cwd)
if not os.path.exists(f"{cwd}/profiles.json"):
    with open(f"{cwd}/profiles.json","w") as f:
        json.dump({"profiles":[]},f,indent=2)
if not os.path.exists(f"{cwd}/accounts.json"):
    with open(f"{cwd}/accounts.json","w") as f:
        json.dump({"accounts":[{"username":"USERNAME","uuid":"8be48703-76cc-4403-b631-fee288045323","token":"fake_token"}],"active":"USERNAME","refresh":{"start":"1","launch":"0"}},f,indent=2)
if not os.path.exists(f"{cwd}/.minecraft"):
    os.makedirs(f"{cwd}/.minecraft",exist_ok=True)
try:
    import pyi_splash # type: ignore
    pyi_splash.update_text('REFRESHING TOKENS...')
except:
    pass
mcdir = f"{cwd}/.minecraft"
CLIENT_ID = "3d006e3a-abc5-4c7f-af37-d4f2104128f5"
REDIRECT_URL = "https://login.microsoftonline.com/common/oauth2/nativeclient/"
HEADERS = {
    'User-Agent': 'github.com/QWERTZexe/QWERTZ-Launcher | QWERTZ Launcher 2.1',
}
with open(f"{cwd}/accounts.json", "r", encoding="utf-8") as f:
    accounts = json.load(f)
if accounts["refresh"]["start"] == "1":
    for account in accounts["accounts"]:
        index = accounts["accounts"].index(account)
        try:
            refresh_token = account["refresh_token"]
        except:
             refresh_token = None
        if refresh_token:
            try:
                account_informaton = mc.microsoft_account.complete_refresh(CLIENT_ID, None, REDIRECT_URL, refresh_token)
                username = account_informaton["name"]
                uuid = account_informaton["id"]
                token = account_informaton["access_token"]
                accounts["accounts"][index]["username"] = username
                accounts["accounts"][index]["uuid"] = uuid
                accounts["accounts"][index]["token"] = token
                with open(f"{cwd}/accounts.json","w") as f:
                    json.dump(accounts,f)
            except:
                pass   
class ModManagerDialog(QDialog):
    def __init__(self, parent=None, profile=None):
        super().__init__(parent)
        self.setWindowTitle("Mod Manager")
        self.profile = profile

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.mod_list = QListWidget()
        layout.addWidget(self.mod_list)

        self.populate_mod_list()

        remove_button = QPushButton("Remove Selected Mod")
        remove_button.clicked.connect(self.remove_selected_mod)
        layout.addWidget(remove_button)

    def populate_mod_list(self):
        mod_dir = f"{cwd}/profiles/{self.profile.name}/mods/"
        if os.path.exists(mod_dir):
            for mod_file in os.listdir(mod_dir):
                mod_item = QListWidgetItem(mod_file)
                self.mod_list.addItem(mod_item)

    def remove_selected_mod(self):
        selected_mod = self.mod_list.currentItem()
        if selected_mod:
            mod_name = selected_mod.text()
            mod_path = f"{cwd}/profiles/{self.profile.name}/mods/{mod_name}"
            reply = QMessageBox.question(self, 'Confirm', f'Are you sure you want to remove the mod "{mod_name}"?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                os.remove(mod_path)
                self.mod_list.takeItem(self.mod_list.row(selected_mod))
        else:
            QMessageBox.warning(self, "No Mod Selected", "Please select a mod to remove.")


class DownloadModThread(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(self, download_url, download_path):
        super().__init__()
        self.download_url = download_url
        self.download_path = download_path

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True,headers=HEADERS)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            progress = 0
            with open(self.download_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        file.write(chunk)
                        progress += len(chunk)
                        self.progress_updated.emit(int((progress / total_size) * 100))
            self.finished.emit(True)
        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            self.finished.emit(False)
class CurseForgeModBrowserDialog(QDialog):
    def __init__(self, parent=None, minecraft_version=None, loader=None, name=None):
        super().__init__(parent)
        self.setWindowTitle("CurseForge Mod Browser")
        self.setGeometry(300, 300, 600, 500)
        self.minecraft_version = minecraft_version
        self.loader = loader
        self.name = name

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for mods...")
        layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_mods)
        layout.addWidget(self.search_button)

        self.mod_list = QListWidget()
        self.mod_list.itemSelectionChanged.connect(self.display_mod_versions)
        layout.addWidget(self.mod_list)

        self.version_list = QListWidget()
        layout.addWidget(self.version_list)
        self.show_incompatible_checkbox = QCheckBox("Show Incompatible Versions", self)
        self.show_incompatible_checkbox.stateChanged.connect(self.display_mod_versions)
        layout.addWidget(self.show_incompatible_checkbox)
        self.add_button = QPushButton("Add Selected Version")
        self.add_button.clicked.connect(self.add_selected_version)
        layout.addWidget(self.add_button)
        

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    def search_mods(self):
        search_query = self.search_input.text()
        mlt = "1" if self.loader == "forge" else "4" if self.loader == "fabric" else ""
        response = requests.get(f"https://api.curse.tools/v1/cf/mods/search?gameId=432&searchFilter={search_query}&classId=6&modLoaderType={mlt}", headers=HEADERS)
        if response.status_code == 200:
            mods = response.json()["data"]
            self.mod_list.clear()
            for mod in mods:
                item = QListWidgetItem(mod["name"])
                try:
                    item.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(requests.get(mod["logo"]["url"], headers=HEADERS).content))))
                except:
                    with open(f"{cwd}/icons/curseforge.png","rb") as f:
                        ico = f.read()
                    item.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(ico))))
                item.setData(Qt.ItemDataRole.UserRole, mod["id"])
                self.mod_list.addItem(item)
        else:
            QMessageBox.warning(self, "Error", "Failed to fetch mods.")
    def display_mod_versions(self):
        if self.mod_list.selectedItems():
            item = self.mod_list.selectedItems()[0]
            mod_id = item.data(Qt.ItemDataRole.UserRole)
            response = requests.get(f"https://api.curse.tools/v1/cf/mods/{mod_id}/files?pageSize=1000&gameVersion={self.minecraft_version}", headers=HEADERS)
            if response.status_code == 200:
                files = response.json()["data"]
                self.version_list.clear()
                for file in files:
                    if self.minecraft_version in file["gameVersions"]:
                        version_item = QListWidgetItem(file["displayName"])
                        version_item.setData(Qt.ItemDataRole.UserRole, file["downloadUrl"])
                        self.version_list.addItem(version_item)

                if self.show_incompatible_checkbox.isChecked():   
                    response = requests.get(f"https://api.curse.tools/v1/cf/mods/{mod_id}/files?pageSize=1000", headers=HEADERS)
                    files = response.json()["data"]
                    if response.status_code == 200:
                        for file in files:
                            if not self.minecraft_version in file["gameVersions"]:
                                version_item = QListWidgetItem(file["displayName"])
                                version_item.setForeground(QColor(255,0,0))
                                version_item.setData(Qt.ItemDataRole.UserRole, file["downloadUrl"])  # Assuming the first file is the one to download
                                self.version_list.addItem(version_item)  
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch mod versions.")

    def add_selected_version(self):
        selected_version_item = self.version_list.currentItem()
        if selected_version_item:
            download_url = selected_version_item.data(Qt.ItemDataRole.UserRole)
            mod_name = download_url.split("/")[-1]
            download_path = f"{cwd}/profiles/{self.name}/mods/{mod_name}"
            self.download_thread = DownloadModThread(download_url, download_path)
            self.download_thread.progress_updated.connect(self.update_progress_bar)
            self.download_thread.finished.connect(self.handle_download_finished)
            self.download_thread.start()
        else:
            QMessageBox.warning(self, "No Version Selected", "Please select a version to add.")

    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress)

    def handle_download_finished(self, success):
        if success:
            QMessageBox.information(self, "Success", "Mod downloaded successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to download the mod.")
class ModBrowserDialog(QDialog):
    def __init__(self, parent=None, minecraft_version=None, loader=None,name=None):
        super().__init__(parent)
        self.setWindowTitle("Modrinth Mod Browser")
        self.setGeometry(300, 300, 600, 500)
        self.minecraft_version = minecraft_version
        self.loader = loader
        self.name = name
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for mods...")
        layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_mods)
        layout.addWidget(self.search_button)

        self.mod_list = QListWidget()
        self.mod_list.itemSelectionChanged.connect(self.display_mod_versions)
        layout.addWidget(self.mod_list)

        self.version_list = QListWidget()
        layout.addWidget(self.version_list)
        self.show_incompatible_checkbox = QCheckBox("Show Incompatible Versions", self)
        self.show_incompatible_checkbox.stateChanged.connect(self.display_mod_versions)
        layout.addWidget(self.show_incompatible_checkbox)
        self.add_button = QPushButton("Add Selected Version")
        self.add_button.clicked.connect(self.add_selected_version)
        layout.addWidget(self.add_button)
        

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    def search_mods(self):
        search_query = self.search_input.text()
        response = requests.get(f"https://api.modrinth.com/v2/search?query={search_query}",headers=HEADERS)
        if response.status_code == 200:
            mods = response.json()["hits"]
            
            self.version_list.clear()
            self.mod_list.clear()
            for mod in mods:
                item = QListWidgetItem(mod["title"])
                try:
                    item.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(requests.get(mod["icon_url"],headers=HEADERS).content).scaled(100,100))))
                except:
                    with open(f"{cwd}/icons/modrinth.png","rb") as f:
                        ico = f.read()
                    item.setIcon(QIcon(QPixmap.fromImage(QImage.fromData(ico))))
                item.setData(Qt.ItemDataRole.UserRole, mod["project_id"])
                self.mod_list.addItem(item)
        else:
            QMessageBox.warning(self, "Error", "Failed to fetch mods.")

    def display_mod_versions(self):
        if self.mod_list.selectedItems():
            mod_id = self.mod_list.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
            response = requests.get(f"https://api.modrinth.com/v2/project/{mod_id}/version",headers=HEADERS)
            if response.status_code == 200:
                versions = response.json()
                self.version_list.clear()
                for version in versions:
                    if self.minecraft_version in version["game_versions"] and self.loader in version["loaders"]:
                        version_item = QListWidgetItem(version["name"])
                        version_item.setData(Qt.ItemDataRole.UserRole, version["files"][0]["url"])  # Assuming the first file is the one to download
                        self.version_list.addItem(version_item)
                if self.show_incompatible_checkbox.isChecked():
                    for version in versions:
                        if not self.minecraft_version in version["game_versions"] or not self.loader in version["loaders"]:
                            version_item = QListWidgetItem(version["name"])
                            version_item.setForeground(QColor(255,0,0))
                            version_item.setData(Qt.ItemDataRole.UserRole, version["files"][0]["url"])  # Assuming the first file is the one to download
                            self.version_list.addItem(version_item)                      
            else:
                QMessageBox.warning(self, "Error", "Failed to fetch mod versions.")

    def add_selected_version(self):
        selected_version_item = self.version_list.currentItem()
        if selected_version_item:
            name = self.name
            download_url = selected_version_item.data(Qt.ItemDataRole.UserRole)
            mod_name = download_url.split("/")[-1]
            download_path = f"{cwd}/profiles/{name}/mods/{mod_name}"
            self.download_thread = DownloadModThread(download_url, download_path)
            self.download_thread.progress_updated.connect(self.update_progress_bar)
            self.download_thread.finished.connect(self.handle_download_finished)
            self.download_thread.start()
        else:
            QMessageBox.warning(self, "No Version Selected", "Please select a version to add.")

    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress)

    def handle_download_finished(self, success):
        if success:
            QMessageBox.information(self, "Success", "Mod downloaded successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to download the mod.")

class DownloadAndExtractThread(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(self, download_url, download_path, extract_path):
        super().__init__()
        self.download_url = download_url
        self.download_path = download_path
        self.extract_path = extract_path

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            progress = 0

            with open(self.download_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        file.write(chunk)
                        progress += len(chunk)
                        self.progress_updated.emit(int((progress / total_size) * 100))

            with zipfile.ZipFile(self.download_path, 'r') as zip_ref:
                zip_ref.extractall(f"{cwd}/.minecraft")

            os.remove(self.download_path)
            self.finished.emit(True)

        except Exception as e:
            QMessageBox.critical(None, "Error", str(e))
            self.finished.emit(False)

class DownloadAndExtractLegacyForge(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download Legacy Forge Support")
        self.layout = QVBoxLayout(self)
        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)
        self.download_url = 'https://qwertz.app/downloads/QWERTZLauncher/QWERTZ_Launcher-LEGACY-FORGE-SUPPORT.zip'
        self.download_path = f"{cwd}/.minecraft/legacy-forge-support.zip"
        self.extract_path = f"{cwd}/.minecraft"

        self.download_thread = DownloadAndExtractThread(self.download_url, self.download_path, self.extract_path)
        self.download_thread.progress_updated.connect(self.update_progress_bar)
        self.download_thread.finished.connect(self.handle_finished)
        self.download_thread.start()

    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress)
    def handle_finished(self, success):
        if success:
            QMessageBox.information(self, "Success", "Legacy Forge support installed successfully.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to install Legacy Forge support.")
            self.reject()

class LoginMainWindow(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Logging in to Microsoft")
        self.loginWindow = LoginWindow(self,parent)
        
        self.loginWindow.show()
        self.loginWindow.closed.connect(self.close)
class LoginWindow(QWebEngineView):
    closed = pyqtSignal()
    def __init__(self, parent=None,ogparent=None):
        super().__init__(parent)
        self.parent = ogparent
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(QSize(800, 600))
        self.setWindowTitle("Logging in to Microsoft")

        login_url, self.state, self.code_verifier = mc.microsoft_account.get_secure_login_data(CLIENT_ID, REDIRECT_URL)
        self.load(QUrl(login_url))

        # Connects a function that is called when the url changed
        self.urlChanged.connect(self.new_url)

        self.show()
    def closeEvent(self, event):
        self.closed.emit()  # Emit the closed signal when the window is closed
        super().closeEvent(event)
    def new_url(self, url: QUrl):
        try:
            auth_code = mc.microsoft_account.parse_auth_code_url(url.toString(), self.state)
            account_information = mc.microsoft_account.complete_login(CLIENT_ID, None, REDIRECT_URL, auth_code, self.code_verifier)
            self.handleLoginSuccess(account_information)
        except AssertionError:
            print("States do not match!")
        except KeyError:
            print("URL not valid")

    def handleLoginSuccess(self, account_information):
        self.token = account_information["access_token"]
        self.username = account_information["name"]
        self.uuid = account_information["id"]

        # Save the refresh token in a file
        with open(f"{cwd}/accounts.json", "r", encoding="utf-8") as f:
            accounts = json.load(f)
        a=0
        for acc in accounts["accounts"]:
            if acc["username"] == self.username:
                a=1
        if not a==1:
            accounts["accounts"].append({
                "username": self.username,
                "uuid": self.uuid,
                "token": self.token,
                "refresh_token":account_information["refresh_token"]
            })
            with open(f"{cwd}/accounts.json","w") as f:
                json.dump(accounts, f, ensure_ascii=False, indent=4)

            # Update the account information in the parent AccountManagementDialog
            self.parent.updateAccountInfo(self.username, self.uuid, self.token)
            
            self.close()
        else:
            QMessageBox.warning(self, "Error", f"An account with the username '{self.username}' already exists.")
        
            self.close()
class AccountManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Account Management")
        self.layout = QVBoxLayout(self)
        with open(f"{cwd}/accounts.json","r") as f:
            accounts = json.load(f)
        microsoft_accounts = []
        for account in accounts["accounts"]:
            microsoft_accounts.append(account["username"])
        # Add account list
        self.account_list = QListWidget()
        self.account_list.addItems(microsoft_accounts)
        self.layout.addWidget(self.account_list)
        # Add buttons for adding, deleting, and editing accounts
        self.add_button = QPushButton("Add Account")
        self.add_button.clicked.connect(self.add_account)
        self.layout.addWidget(self.add_button)

        self.add_fake_button = QPushButton("Add Offline Account")
        self.add_fake_button.clicked.connect(self.add_fake_account)
        self.layout.addWidget(self.add_fake_button)

        self.delete_button = QPushButton("Delete Account")
        self.delete_button.clicked.connect(self.delete_account)
        self.layout.addWidget(self.delete_button)

        self.refresh_on_start_checkbox = QCheckBox("Refresh sessions on launcher start")
        self.layout.addWidget(self.refresh_on_start_checkbox)
        
        # Checkbox for "Refresh on launch"
        self.refresh_on_launch_checkbox = QCheckBox("Refresh on launch")
        self.layout.addWidget(self.refresh_on_launch_checkbox)
        
        # Load the initial states of the checkboxes from a configuration file or settings
        self.load_checkbox_states()
        
        # Connect signals if needed, for example, to save the state when changed
        self.refresh_on_start_checkbox.stateChanged.connect(self.save_checkbox_states)
        self.refresh_on_launch_checkbox.stateChanged.connect(self.save_checkbox_states)
    def load_checkbox_states(self):
        with open(f"{cwd}/accounts.json", "r", encoding="utf-8") as f:
            accounts = json.load(f)
        self.refresh_on_launch_checkbox.setChecked(True) if accounts["refresh"]["launch"] == "1" else self.refresh_on_launch_checkbox.setChecked(False)
        self.refresh_on_start_checkbox.setChecked(True) if accounts["refresh"]["start"] == "1" else self.refresh_on_start_checkbox.setChecked(False)
    def save_checkbox_states(self):
        with open(f"{cwd}/accounts.json", "r", encoding="utf-8") as f:
            accounts = json.load(f)
        accounts["refresh"]["launch"] = "1" if self.refresh_on_launch_checkbox.isChecked() else "0"
        accounts["refresh"]["start"] = "1" if self.refresh_on_start_checkbox.isChecked() else "0"
        with open(f"{cwd}/accounts.json", "w", encoding="utf-8") as f:
            json.dump(accounts,f,indent=2)
    def add_account(self): 

        dialog = LoginMainWindow(self)
        dialog.exec()
    def updateAccountInfo(self, username, uuid,token):
        self.activeUser = username
        self.activeUUID = uuid
        self.activeToken = token
        self.updateAccountList()

    def updateAccountList(self):
        global restart
        username = self.activeUser
        uuid = self.activeUUID
        token = self.activeToken
            # Check if the account already exists


            # Update the account list in the dialog
        self.account_list.addItem(username)
        try:
            ico = requests.get(f"https://crafatar.com/avatars/{uuid}").content
        except:
            with open(f"{cwd}/icons/fallback.png","rb") as f:
                ico = f.read()
        action = QAction(QIcon(QPixmap.fromImage(QImage.fromData(ico))), f"{username}", self)
        action.triggered.connect(lambda checked, t="fake_token", uu=uuid,u=username: ex.setActiveAccount(t,uu,u))
        ex.microsoft_account_menu.addAction(action)

        ###RESTARTING BECAUSE IT IS NOT WORKING SMH
        restart = 1
        app.quit()
    def add_fake_account(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Offline Account")
        layout = QVBoxLayout(dialog)

        # Username input
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_fake_account(dialog))
        layout.addWidget(save_button)

        dialog.exec()

    def save_fake_account(self, dialog):
        username = self.username_input.text().strip().replace(" ", "_").replace("-", "_")
        if username:
            # Check if the account already exists
            with open(f"{cwd}/accounts.json", "r") as f:
                accounts = json.load(f)
            for account in accounts["accounts"]:
                if account["username"] == username:
                    # Account already exists, show an error message
                    QMessageBox.warning(self, "Error", f"An account with the username '{username}' already exists.")
                    return

            # Generate a random UUID
            uuid_str = str(uuuid.uuid4())

            # Add the fake account to the accounts.json file
            accounts["accounts"].append({
                "username": username,
                "uuid": uuid_str,
                "token": "fake_token"
            })

            with open(f"{cwd}/accounts.json", "w") as f:
                json.dump(accounts, f, indent=2)

            # Update the account list in the dialog
            self.account_list.addItem(username)
            try:
                ico = requests.get(f"https://crafatar.com/avatars/{uuid_str}").content
            except:
                with open(f"{cwd}/icons/fallback.png","rb") as f:
                    ico = f.read()
            action = QAction(QIcon(QPixmap.fromImage(QImage.fromData(ico))), f"{username} (Offline)", self)
            action.triggered.connect(lambda checked, t="fake_token", uu=uuid_str,u=username: ex.setActiveAccount(t,uu,u))
            ex.microsoft_account_menu.addAction(action)
            dialog.accept()
    def delete_account(self):
        # Get the selected account from the list
        selected_account = self.account_list.currentItem()
        if selected_account:
            # Get the username of the selected account
            username = selected_account.text()
            u2 = username
            # Ask for confirmation before deleting the account
            reply = QMessageBox.question(self, 'Confirmation', f'Are you sure you want to delete the account "{username}"?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                with open(f"{cwd}/accounts.json", "r") as f:
                    accounts = json.load(f)
                if len(accounts["accounts"]) > 1:
                    # Remove the account from the accounts.json file

                    # Find the index of the account to be deleted
                    for i, account in enumerate(accounts["accounts"]):
                        if account["username"] == username:
                            accounts["accounts"].pop(i)

                    with open(f"{cwd}/accounts.json", "w") as f:
                        json.dump(accounts, f, indent=2)

                    # Remove the account from the list widget
                    row = self.account_list.row(selected_account)
                    self.account_list.takeItem(row)

                    # If the deleted account was the active account, set the first account as active
                    if username == accounts["active"]:
                        if accounts["accounts"]:
                            accounts["active"] = accounts["accounts"][0]["username"]
                            uuid = accounts["accounts"][0]["uuid"]
                            activeuser = accounts["accounts"][0]["username"]
                        else:
                            accounts["active"] = ""
                            uuid = ""
                            activeuser = ""
                        with open(f"{cwd}/accounts.json", "w") as f:
                            json.dump(accounts, f, indent=2)
                        try:
                            ico = requests.get(f"https://crafatar.com/avatars/{uuid}").content
                        except:
                            with open(f"{cwd}/icons/fallback.png","rb") as f:
                                ico = f.read()
                        ex.active_account_icon.setPixmap(QPixmap.fromImage(QImage.fromData(ico)).scaled(40,40))
                        ex.microsoft_account_button.setText(f"{activeuser}")
    
                    for a in ex.microsoft_account_menu.actions():
                        if a.text().split(" ")[0] == u2:
                            ex.microsoft_account_menu.removeAction(a)
                else:
                    QMessageBox.warning(self,"Error","You cannot delete your only account. Create a new one first.")
class VersionDialog(QDialog):
    def __init__(self, version_list, current_version, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Select Minecraft Version')
        self.layout = QVBoxLayout(self)

        # Create and populate the combo box with versions
        self.comboBox = QComboBox(self)
        self.comboBox.addItems(version_list)
        self.comboBox.setCurrentText(current_version)
        self.layout.addWidget(self.comboBox)

        # Close button
        self.closeButton = QPushButton('Save', self)
        self.closeButton.clicked.connect(self.close)
        self.layout.addWidget(self.closeButton)

    def selected_version(self):
        return self.comboBox.currentText()
class AddProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Profile")
        self.setGeometry(500, 500, 400, 300)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Name input
        name_layout = QVBoxLayout()
        name_label = QLabel("Profile Name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Icon selection
        icon_layout = QVBoxLayout()
        icon_label = QLabel("Profile Icon:")
        self.icon_combobox = QComboBox()
        self.icon_combobox.addItem("Default", "minecraft.png")
        self.icon_combobox.addItem("Custom", "")
        self.icon_combobox.currentIndexChanged.connect(self.icon_type_changed)
        self.default_combobox = QComboBox()
        self.default_combobox.addItem("Minecraft", "minecraft.png")
        for x, y, files in os.walk(f"{cwd}/icons/profiles/"):
            for file in files:
                if not file == "minecraft.png":
                    self.default_combobox.addItem(file[0].upper() + file.split(".")[0][1:], file)
        self.icon_path_input = QLineEdit()
        self.icon_path_input.setPlaceholderText("Enter icon file path")
        self.icon_path_input.setVisible(False)
        self.icon_browse_button = QPushButton("Browse")
        self.icon_browse_button.clicked.connect(self.browse_icon)
        self.icon_browse_button.setVisible(False)
        loader_layout = QVBoxLayout()
        loader_label = QLabel("Loader:")
        self.loader_combobox = QComboBox()
        self.loader_combobox.addItem("Vanilla", "VANILLA")
        self.loader_combobox.addItem("Forge", "FORGE")
        self.loader_combobox.addItem("Fabric", "FABRIC")
        jvm_layout = QVBoxLayout()
        jvm_label = QLabel("JVM:")
        self.jvm_combobox = QComboBox()
        self.jvm_combobox.addItem("Built-in", "built-in")
        self.jvm_combobox.addItem("Custom", "custom")
        self.jvm_combobox.currentIndexChanged.connect(self.jvm_type_changed)
        jvm_layout.addWidget(jvm_label)
        jvm_layout.addWidget(self.jvm_combobox)

        # Custom JVM path
        self.jvm_path_input = QLineEdit()
        self.jvm_path_input.setPlaceholderText("Enter JVM path")
        self.jvm_path_input.setVisible(False)
        self.jvm_browse_button = QPushButton("Browse")
        self.jvm_browse_button.clicked.connect(self.browse_jvm)
        self.jvm_browse_button.setVisible(False)
        jvm_layout.addWidget(self.jvm_path_input)
        jvm_layout.addWidget(self.jvm_browse_button)


        icon_layout.addWidget(icon_label)
        icon_layout.addWidget(self.icon_combobox)
        icon_layout.addWidget(self.default_combobox)
        icon_layout.addWidget(self.icon_path_input)
        icon_layout.addWidget(self.icon_browse_button)
        layout.addLayout(icon_layout)
        
        loader_layout.addWidget(loader_label)
        loader_layout.addWidget(self.loader_combobox)
        
        layout.addLayout(loader_layout)
        # Version selection
        version_layout = QVBoxLayout()
        version_label = QLabel("Version:")
        self.version_combobox = QComboBox()
        versions = mc.utils.get_available_versions(mcdir)
        version_list = []

        for i in versions:
            if "." in i["id"] and not "fabric" in i["id"].lower() and not "forge" in i["id"].lower():
                version_list.append(i["id"])
        self.version_combobox.addItems(version_list)
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_combobox)
        layout.addLayout(version_layout)

        layout.addLayout(jvm_layout)
        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_profile)
        layout.addWidget(save_button)

    def icon_type_changed(self, index):
        self.icon_path_input.setVisible(index == 1)
        self.icon_browse_button.setVisible(index == 1)
        self.default_combobox.setVisible(index == 0)

    def browse_icon(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Image files (*.png *.jpg *.jpeg)")
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.icon_path_input.setText(selected_file)

    def jvm_type_changed(self, index):
        self.jvm_path_input.setVisible(index == 1)
        self.jvm_browse_button.setVisible(index == 1)

    def browse_jvm(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Executable files (*.exe *.jar)")
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            self.jvm_path_input.setText(selected_file)
    def save_profile(self):
        name = self.name_input.text().strip()
        if not name:
            return
        icon_type = self.icon_combobox.currentData()
        if icon_type == "":
            icon_path = self.icon_path_input.text().strip()
            if not os.path.exists(icon_path):
                return
        else:
            icon_path = self.default_combobox.currentData()
        version = self.version_combobox.currentText()
        loader = self.loader_combobox.currentData()
        new_profile = {
            "name": name,
            "icon": icon_path,
            "icon_type": "default" if icon_type else "custom",
            "loader": loader,
            "version": version,
            "jvm": "BI" if self.jvm_combobox.currentData() == "built-in" else self.jvm_path_input.text().strip()
        }
        with open(f"{cwd}/profiles.json", "r") as f:
            profiles = json.load(f)
        profiles["profiles"].append(new_profile)
        with open(f"{cwd}/profiles.json", "w") as f:
            json.dump(profiles, f, indent=2)
        os.makedirs(f"{cwd}/profiles/{name}/mods/")
        self.accept()

class ProfileButton(QPushButton):
    def __init__(self, name, icon,profilegrid, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setMinimumSize(QSize(150, 150))
        self.name = name
        self.parentt = parent
        self.profilegrid = profilegrid
        # Create a vertical layout for the button
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add the icon to the top of the    button
        self.icon = QLabel()
        self.icon.setPixmap(QIcon(icon).pixmap(96, 96))
        layout.addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add the name label to the bottom of the button
        self.nameLabel = QLabel(name)
        self.nameLabel.setFont(QFont('Consolas', 10))
        layout.addWidget(self.nameLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        # Set the stylesheet for the button
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:checked {
                background-color: #007bff;
                color: white;
            }
        """)

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QStylePainter(self)
        painter.drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt)
        super(ProfileButton, self).paintEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_icon = QIcon(f"{cwd}/icons/delete.png")
        delete_action = menu.addAction(delete_icon, "Delete Profile")
        rename_icon = QIcon(f"{cwd}/icons/rename.png")
        rename_action = menu.addAction(rename_icon, "Rename Profile")
        icon_icon = QIcon(f"{cwd}/icons/icon.png")
        icon_action = menu.addAction(icon_icon, "Change Icon")
        version_icon = QIcon(f"{cwd}/icons/version.png")
        version_action = menu.addAction(version_icon, "Change Version")
        jvm_icon = QIcon(f"{cwd}/icons/jvm.png")
        jvm_action = menu.addAction(jvm_icon, "Change JVM")
        loader_icon = QIcon(f"{cwd}/icons/loader.png") 
        loader_action = menu.addAction(loader_icon, "Change Loader")
        folder_icon = QIcon(f"{cwd}/icons/folder.png")
        folder_action = menu.addAction(folder_icon, "Open in Explorer")
        self.parentt.selectProfile(self.name)
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == delete_action:
            self.deleteProfile()
        elif action == version_action:
            self.changeVersion()
        elif action == jvm_action:
            self.changeJVM()
        elif action == loader_action:
            self.changeLoader()    
        elif action == rename_action:
            self.renameProfile()
        elif action == icon_action:
            self.changeIcon()
        elif action == folder_action:
            self.openFolder()
    def openFolder(self):
        os.startfile(f"{cwd}/profiles/{self.name}")
    def renameProfile(self):
        profile_name = self.name
        rename_dialog = QDialog(self)
        rename_dialog.setWindowTitle("Rename Profile")
        layout = QVBoxLayout()
        rename_dialog.setLayout(layout)

        label = QLabel("Enter new profile name:")
        layout.addWidget(label)

        name_input = QLineEdit()
        name_input.setText(profile_name)
        layout.addWidget(name_input)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("Save")
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        def on_ok():
            new_name = name_input.text().strip()
            if new_name and new_name != profile_name:
                with open(f"{cwd}/profiles.json", "r") as f:
                    profiles_data = json.load(f)
                for profile in profiles_data["profiles"]:
                    if profile["name"] == new_name:
                        QMessageBox.warning(self, "Error", f"A profile with the name '{new_name}' already exists.")
                        return
                for profile in profiles_data["profiles"]:
                    if profile["name"] == profile_name:
                        profile["name"] = new_name
                        break

                with open(f"{cwd}/profiles.json", "w") as f:
                    json.dump(profiles_data, f, indent=2)
                try:
                    shutil.move(f"{cwd}/profiles/{self.name}",f"{cwd}/profiles/{new_name}")
                except:
                    pass
                self.name = new_name
                self.setText(new_name)
                self.parentt.reinitLauncher()
            rename_dialog.accept()


        ok_button.clicked.connect(on_ok)

        rename_dialog.exec()

    def changeIcon(self):
        # Assuming self.name is the profile name
        profile_name = self.name
        with open(f"{cwd}/profiles.json", "r") as f:
            profiles_data = json.load(f)

        # Find the current icon of the profile
        current_icon = None
        for profile in profiles_data["profiles"]:
            if profile["name"] == self.name:
                icon_type = profile["icon_type"]
                current_icon = profile["icon"]
                break

        # Open a dialog to select the icon
        icon_dialog = QDialog(self)
        icon_dialog.setWindowTitle("Select icon")
        layout = QVBoxLayout()
        icon_dialog.setLayout(layout)

        icon_label = QLabel("Icon:")
        icon_combobox = QComboBox()
        icon_combobox.addItem("Default", "default")
        icon_combobox.addItem("Custom", "custom")
        icon_combobox.setCurrentText("Default" if icon_type == "default" else "Custom")
        icon_combobox.currentIndexChanged.connect(lambda index: icon_path_input.setVisible(index == 1))
        icon_combobox.currentIndexChanged.connect(lambda index: icon_browse_button.setVisible(index == 1))
        layout.addWidget(icon_label)
        layout.addWidget(icon_combobox)
        default_combobox = QComboBox()
        default_combobox.addItem("Minecraft", "minecraft.png")
        
        default_combobox.setVisible(icon_type != "custom")
        for x, y, files in os.walk(f"{cwd}/icons/profiles/"):
            for file in files:
                if not file == "minecraft.png":
                    default_combobox.addItem(file[0].upper() + file.split(".")[0][1:], file)
        icon_path_input = QLineEdit()
        icon_path_input.setPlaceholderText("Enter icon path")
        icon_path_input.setText(current_icon if icon_type == "custom" else "")
        icon_path_input.setVisible(icon_type == "custom")
        layout.addWidget(icon_path_input)
        layout.addWidget(default_combobox)

        icon_combobox.currentIndexChanged.connect(lambda index: default_combobox.setVisible(index != 1))
        icon_browse_button = QPushButton("Browse")
        icon_browse_button.clicked.connect(lambda: browse_icon(icon_path_input))
        icon_browse_button.setVisible(current_icon == "custom")
        layout.addWidget(icon_browse_button)

        save_button = QPushButton("Save")
        save_button.clicked.connect(icon_dialog.accept)
        layout.addWidget(save_button)

        def browse_icon(line_edit):
            file_dialog = QFileDialog()
            file_dialog.setNameFilter("Image files (*.png *.jpg *.jpeg)")
            if file_dialog.exec():
                selected_file = file_dialog.selectedFiles()[0]
                line_edit.setText(selected_file)

        if icon_dialog.exec():
            new_icon = default_combobox.currentData() if icon_combobox.currentData() == "default" else icon_path_input.text().strip()
            for profile in profiles_data["profiles"]:
                if profile["name"] == self.name:
                    index = profiles_data["profiles"].index(profile)
                    profiles_data["profiles"][index]["icon"] = new_icon
                    profiles_data["profiles"][index]["icon_type"] = "default" if icon_combobox.currentData() == "default" else "custom"
                    break
            

            with open(f"{cwd}/profiles.json", "w") as f:
                json.dump(profiles_data, f, indent=2)
            
            self.parentt.reinitLauncher()
    def changeLoader(self):
        # Assuming self.name is the profile name
        profile_name = self.name
        with open(f"{cwd}/profiles.json", "r") as f:
            profiles_data = json.load(f)

        # Find the current loader of the profile
        current_loader = None
        for profile in profiles_data["profiles"]:
            if profile["name"] == self.name:
                current_loader = profile["loader"]
                break

        # Open a dialog to select the loader
        loader_dialog = QDialog(self)
        loader_dialog.setWindowTitle("Select Loader")
        layout = QVBoxLayout()
        loader_dialog.setLayout(layout)
        loader_label = QLabel("Loader:")
        loader_combobox = QComboBox()
        loader_combobox.addItem("Vanilla", "VANILLA")
        loader_combobox.addItem("Forge", "FORGE")
        loader_combobox.addItem("Fabric", "FABRIC")
        loader_combobox.setCurrentText(current_loader)
        layout.addWidget(loader_label)
        layout.addWidget(loader_combobox)

        # Add OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Save")
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        def on_ok():
            new_loader = loader_combobox.currentData()
            for profile in profiles_data["profiles"]:
                if profile["name"] == self.name:
                    profile["loader"] = new_loader
                    break
            with open(f"{cwd}/profiles.json", "w") as f:
                json.dump(profiles_data, f, indent=2)
            
            with open(f"{cwd}/profiles.json","r") as f:
                profiles = json.load(f)
            for profile in profiles["profiles"]:
                if profile["name"] == self.name:
                    ver=profile["version"]
                    loader=profile["loader"]
                    name = profile["name"]
                    ex.update_info_label(f"Name: {name}   Version: {ver}   Loader: {loader}")
            loader_dialog.accept()
        ok_button.clicked.connect(on_ok)

        loader_dialog.exec()
    def changeJVM(self):
        # Assuming self.name is the profile name
        profile_name = self.name
        with open(f"{cwd}/profiles.json", "r") as f:
            profiles_data = json.load(f)

        # Find the current JVM of the profile
        current_jvm = None
        for profile in profiles_data["profiles"]:
            if profile["name"] == self.name:
                current_jvm = profile["jvm"]
                break

        # Open a dialog to select the JVM
        jvm_dialog = QDialog(self)
        jvm_dialog.setWindowTitle("Select JVM")
        layout = QVBoxLayout()
        jvm_dialog.setLayout(layout)

        jvm_label = QLabel("JVM:")
        jvm_combobox = QComboBox()
        jvm_combobox.addItem("Built-in", "built-in")
        jvm_combobox.addItem("Custom", "custom")
        jvm_combobox.setCurrentText("Built-in" if current_jvm == "BI" else "Custom")
        jvm_combobox.currentIndexChanged.connect(lambda index: jvm_path_input.setVisible(index == 1))
        jvm_combobox.currentIndexChanged.connect(lambda index: jvm_browse_button.setVisible(index == 1))
        layout.addWidget(jvm_label)
        layout.addWidget(jvm_combobox)

        jvm_path_input = QLineEdit()
        jvm_path_input.setPlaceholderText("Enter JVM path")
        jvm_path_input.setText(current_jvm if current_jvm != "BI" else "")
        jvm_path_input.setVisible(current_jvm != "BI")
        layout.addWidget(jvm_path_input)

        jvm_browse_button = QPushButton("Browse")
        jvm_browse_button.clicked.connect(lambda: browse_jvm(jvm_path_input))
        jvm_browse_button.setVisible(current_jvm != "BI")
        layout.addWidget(jvm_browse_button)

        save_button = QPushButton("Save")
        save_button.clicked.connect(jvm_dialog.accept)
        layout.addWidget(save_button)

        def browse_jvm(line_edit):
            file_dialog = QFileDialog()
            file_dialog.setNameFilter("Executable files (*.exe *.jar)")
            if file_dialog.exec():
                selected_file = file_dialog.selectedFiles()[0]
                line_edit.setText(selected_file)

        if jvm_dialog.exec():
            new_jvm = "BI" if jvm_combobox.currentData() == "built-in" else jvm_path_input.text().strip()
            for profile in profiles_data["profiles"]:
                if profile["name"] == self.name:
                    profile["jvm"] = new_jvm
                    break

            with open(f"{cwd}/profiles.json", "w") as f:
                json.dump(profiles_data, f, indent=2)
    def changeVersion(self):
        # Assuming self.name is the profile name
        profile_name = self.name
        with open(f"{cwd}/profiles.json", "r") as f:
            profiles_data = json.load(f)

        # Find the current version of the profile
        current_version = None
        for profile in profiles_data["profiles"]:
            if profile["name"] == self.name:
                current_version = profile["version"]
                break

        # Get available versions
        versions = mc.utils.get_available_versions(mcdir)  # Adjust the path as needed
        version_list = [v["id"] for v in versions if "." in v["id"] and "fabric" not in v["id"].lower() and "forge" not in v["id"].lower()]

        # Open the version dialog
        dialog = VersionDialog(version_list, current_version, self)
        dialog.exec()

        # Update the profile's version in the JSON file
        new_version = dialog.selected_version()
        for profile in profiles_data["profiles"]:
            if profile["name"] == self.name:
                profile["version"] = new_version
                break

        with open(f"{cwd}/profiles.json", "w") as f:
            json.dump(profiles_data, f, indent=2)
        with open(f"{cwd}/profiles.json","r") as f:
            profiles = json.load(f)
        for profile in profiles["profiles"]:
            if profile["name"] == self.name:
                ver=profile["version"]
                loader=profile["loader"]
                name = profile["name"]
                ex.update_info_label(f"Name: {name}   Version: {ver}   Loader: {loader}")
    def deleteProfile(self):
        # Remove the profile from the profiles.json file
        reply = QMessageBox.question(self, 'Confirm', f'Are you sure you want to delete the profile "{self.name}"?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if os.path.exists(f"{cwd}/profiles/{self.name}"):
                shutil.rmtree(f"{cwd}/profiles/{self.name}")
            with open(f"{cwd}/profiles.json", "r") as f:
                profiles = json.load(f)

            profiles["profiles"] = [p for p in profiles["profiles"] if p["name"] != self.name]

            with open(f"{cwd}/profiles.json", "w") as f:
                json.dump(profiles, f, indent=2)

            # Remove the profile button from the grid layout
            for i in range(self.profilegrid.count()):
                widget = self.profilegrid.itemAt(i).widget()
                if isinstance(widget, ProfileButton) and widget.name == self.name:
                    self.profilegrid.removeWidget(widget)
                    widget.deleteLater()
                    break

            # Deselect the profile if it was selected
            if self.parentt.selectedProfile == self:
                self.parentt.selectedProfile = None
                self.setChecked(False)
            self.parentt.reinitLauncher()
class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
    def initUI(self):
        self.setWindowIcon(QIcon(f'{cwd}/icons/launcher.png'))
        self.setGeometry(500, 250, 700, 500)
        self.setWindowTitle('QWERTZ Launcher')
        self.selectedProfile = None
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        self.runningprofiles={}
        # Create a QLabel to display profile information
        self.infoLabel = QLabel("Select a profile to see details here.", self)
        self.infoLabel.setFont(QFont('Arial', 12))
        self.infoLabel.setStyleSheet("QLabel { color : blue; }")
        layout.addWidget(self.infoLabel)

        self.createToolBar()
        self.profileScrollArea = QScrollArea()
        self.profileScrollArea.setWidgetResizable(True)
        self.profileScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.profileScrollArea)

        self.profileWidget = QWidget()
        self.profileGrid = QGridLayout(self.profileWidget)
        self.profileScrollArea.setWidget(self.profileWidget)

        self.populateProfiles()

        self.launchButton = QPushButton('Launch', self)
        self.launchButton.setFont(QFont('Consolas', 20))
        self.launchButton.clicked.connect(self.launch)
        self.launchButton.setFixedHeight(60)
        layout.addWidget(self.launchButton)

        # Create a horizontal layout for the buttons
        buttonLayout = QHBoxLayout()
        self.repairButton = QToolButton()
        self.repairButton.setFixedSize(60, 60)
        self.repairButton.setIcon(QIcon(f"{cwd}/icons/fix.png"))
        self.repairButton.setIconSize(QSize(40, 40))
        self.repairButton.clicked.connect(self.repair)
        self.repairButton.setToolTip("Repair Profile")
        buttonLayout.addWidget(self.launchButton)
        buttonLayout.addWidget(self.repairButton)

        layout.addLayout(buttonLayout)
        try:
            import pyi_splash # type: ignore
            pyi_splash.close()
        except:
            pass
    def reinitLauncher(self):
        self.infoLabel.setText(f"Select a profile to see details here.")
        # Remove all existing profile buttons
        for i in reversed(range(self.profileGrid.count())):
            widget = self.profileGrid.itemAt(i).widget()
            if isinstance(widget, ProfileButton):
                self.profileGrid.removeWidget(widget)
                widget.deleteLater()

        # Repopulate the grid with profile buttons
        with open(f"{cwd}/profiles.json", "r") as f:
            self.profiles = json.load(f)

        self.selectedProfile = None
        for i, profile in enumerate(self.profiles["profiles"]):
            if profile["icon_type"] == "default":
                if os.path.exists(f"{cwd}/icons/profiles/"+profile["icon"]):
                    button = ProfileButton(profile["name"], f"{cwd}/icons/profiles/"+profile["icon"], self.profileGrid, self)
                else:
                    button = ProfileButton(profile["name"], f"{cwd}/icons/profiles/minecraft.png", self.profileGrid, self)
            else:
                if os.path.exists(profile["icon"]):
                    button = ProfileButton(profile["name"], profile["icon"], self.profileGrid, self)
                else:
                    button = ProfileButton(profile["name"], f"{cwd}/icons/profiles/minecraft.png", self.profileGrid, self)
            button.clicked.connect(lambda checked, p=profile["name"]: self.selectProfile(p))
            self.profileGrid.addWidget(button, i // 4, i % 4)
    def repair(self):
        if self.selectedProfile:
            with open(f"{cwd}/profiles.json","r") as f:
                profiles = json.load(f)
            for profile in profiles["profiles"]:
                if profile["name"] == self.selectedProfile.name:
                    ver=profile["version"]
                    loader=profile["loader"]
                    name=profile["name"]
            def set_status(status: str):
                print(status)
                if status == "Installation complete":
                    ex.launchButton.setText("Launch")
            def set_progress(progress: int):
                if current_max != 0:
                    print(f"{progress}/{current_max}")
                    ex.launchButton.setText(f"{progress}/{current_max}")

            def set_max(new_max: int):
                global current_max
                current_max = new_max

            callback = {
                "setStatus": set_status,
                "setProgress": set_progress,
                "setMax": set_max
            }   
                
            self.repair_thread = RepairThread(ver, mcdir, callback, name,loader)
            self.repair_thread.repair_done.connect(self.showmessage)
            self.repair_thread.start()
        else:
            QMessageBox.warning(self, 'No Profile Selected', 'Please select a profile before trying to repair.')
    def update_info_label(self,info):
        self.infoLabel.setText(info)
        with open(f"{cwd}/profiles.json","r") as f:
            profiles = json.load(f)
        for profile in profiles["profiles"]:
            if profile["name"] == self.selectedProfile.name:
                ver=profile["version"]
                loader=profile["loader"]
                name = profile["name"]
        if loader in ["FORGE","FABRIC"]:
            self.modrinth_action.setEnabled(True)
            self.mod_manager_action.setEnabled(True)
            self.curseforge_action.setEnabled(True)
        else:
            self.modrinth_action.setEnabled(False)
            self.mod_manager_action.setEnabled(False)
            self.curseforge_action.setEnabled(False)
    def populateProfiles(self):
        with open(f"{cwd}/profiles.json", "r") as f:
            self.profiles = json.load(f)
        for i, profile in enumerate(self.profiles["profiles"]):
            if profile['icon_type'] == "custom":
                icon_path = f"{profile['icon']}" if os.path.exists(f"{profile['icon']}") else f"{cwd}/icons/profiles/minecraft.png"
            else:
                icon_path = f"{cwd}/icons/profiles/{profile['icon']}" if os.path.exists(f"{cwd}/icons/profiles/{profile['icon']}") else f"{cwd}/icons/profiles/minecraft.png"
            button = ProfileButton(profile["name"], icon_path, self.profileGrid, self)
            button.clicked.connect(lambda checked, p=profile["name"]: self.selectProfile(p))
            self.profileGrid.addWidget(button, i // 4, i % 4)
    def createToolBar(self):
        self.toolBar = QToolBar()
        self.toolBar.setMovable(False)
        self.addToolBar(self.toolBar)
        self.toolBar.setIconSize(QSize(35, 35))
        self.settingsAction = QAction(QIcon(f'{cwd}/icons/settings.png'), 'Settings', self)
        self.settingsAction.triggered.connect(self.settings)

        self.addProfileAction = QAction(QIcon(f'{cwd}/icons/add_profile.png'), 'Add Profile', self)
        self.addProfileAction.triggered.connect(self.addProfile)
        self.toolBar.addAction(self.addProfileAction)
        self.modrinth_action = QAction(QIcon(f'{cwd}/icons/modrinth.png'), "Modrinth Browser", self)
        self.modrinth_action.setEnabled(False)  # Initially disabled
        self.modrinth_action.triggered.connect(self.open_mod_browser)
        self.toolBar.addAction(self.modrinth_action)
        self.curseforge_action = QAction(QIcon(f'{cwd}/icons/curseforge.png'), "Curseforge Browser", self)
        self.curseforge_action.setEnabled(False)  # Initially disabled
        self.curseforge_action.triggered.connect(self.open_curseforge_browser)
        self.toolBar.addAction(self.curseforge_action)
        self.mod_manager_action = QAction(QIcon(f'{cwd}/icons/modmanager.png'), 'Mod Manager', self)
        self.mod_manager_action.triggered.connect(self.open_mod_manager)
        self.mod_manager_action.setEnabled(False)  # Initially disabled
        self.toolBar.addAction(self.mod_manager_action)
        # Create the Microsoft account dropdown
        with open(f"{cwd}/accounts.json","r") as f:
            self.accounts = json.load(f)

        self.microsoft_accounts = []
        activeuser = self.accounts["active"]
        username = self.accounts["active"]
        for account in self.accounts["accounts"]:
            if username == account["username"]:
                uuid = account["uuid"]
            self.microsoft_accounts.append(account["username"])
        self.microsoft_account_menu = QMenu()
        
        self.microsoft_account_button = QToolButton()
        self.microsoft_account_button.setText(f"{activeuser}")
        self.microsoft_account_button.setFixedHeight(40)
        self.microsoft_account_button.setMenu(self.microsoft_account_menu) 
        self.microsoft_account_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.active_account_icon = QLabel()
        try:
            ico = requests.get(f"https://crafatar.com/avatars/{uuid}").content
        except:
            with open(f"{cwd}/icons/fallback.png","rb") as f:
                ico = f.read()
        self.active_account_icon.setPixmap(QPixmap.fromImage(QImage.fromData(ico)).scaled(40,40))
        self.active_account_layout = QHBoxLayout()
        
        for account in self.microsoft_accounts:
            for accountx in self.accounts["accounts"]:
                if accountx["username"] == account:
                    ind = self.accounts["accounts"].index(accountx)
                    break
            username = self.accounts["accounts"][ind]["username"]
            uuid = self.accounts["accounts"][ind]["uuid"]
            token = self.accounts["accounts"][ind]["token"]
            try:
                ico = requests.get(f"https://crafatar.com/avatars/{uuid}").content
            except:
                with open(f"{cwd}/icons/fallback.png","rb") as f:
                    ico = f.read()
            if token == "fake_token":
                accountstr = f"{username} (Offline)"
            else:
                accountstr = f"{username}"
            action = QAction(QIcon(QPixmap.fromImage(QImage.fromData(ico))), accountstr, self)
            action.triggered.connect(lambda checked, t=token, uu=uuid,u=username: self.setActiveAccount(t,uu,u))
            self.microsoft_account_menu.addAction(action)
            
        # Add the active account name and profile icon
        self.active_account_layout.addWidget(self.active_account_icon,alignment=Qt.AlignmentFlag.AlignRight)
        # Add the toolbar actions
        self.toolBar.addAction(self.settingsAction)
        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.toolBar.addWidget(spacer)
        
        self.toolBar.addAction(self.settingsAction)
        self.toolBar.addWidget(self.active_account_icon)
        self.toolBar.addWidget(self.microsoft_account_button)
    def open_mod_manager(self):
        if self.selectedProfile:
            mod_manager_dialog = ModManagerDialog(self, self.selectedProfile)
            mod_manager_dialog.exec()
        else:
            QMessageBox.warning(self, 'No Profile Selected', 'Please select a profile before managing mods.')
    def open_mod_browser(self):
        with open(f"{cwd}/profiles.json","r") as f:
            profiles = json.load(f)
        for profile in profiles["profiles"]:
            if profile["name"] == self.selectedProfile.name:
                ver=profile["version"]
                loader=profile["loader"]
                name = profile["name"]
        mod_browser = ModBrowserDialog(self, ver,loader.lower(),name)
        mod_browser.exec()
    def setActiveAccount(self,token,uuid,username):
        try:
            ico = requests.get(f"https://crafatar.com/avatars/{uuid}").content
        except:
            with open(f"{cwd}/icons/fallback.png","rb") as f:
                ico = f.read()
        self.active_account_icon.setPixmap(QPixmap.fromImage(QImage.fromData(ico)).scaled(40,40))
        self.microsoft_account_button.setText(f"{username}")
        with open(f"{cwd}/accounts.json","r") as f:
            self.accounts = json.load(f)
        self.accounts["active"] = username
        with open(f"{cwd}/accounts.json","w") as f:
            json.dump(self.accounts,f,indent=4)
    def showmessage(self,messagetitle, message):
        QMessageBox.information(self,messagetitle,message)
    def open_curseforge_browser(self):
        if self.selectedProfile:
            with open(f"{cwd}/profiles.json","r") as f:
                profiles = json.load(f)
            for profile in profiles["profiles"]:
                if profile["name"] == self.selectedProfile.name:
                    ver=profile["version"]
                    loader=profile["loader"]
                    name = profile["name"]
            curseforge_browser = CurseForgeModBrowserDialog(self,ver, loader,name)
            curseforge_browser.exec()
        else:
            QMessageBox.warning(self, 'No Profile Selected', 'Please select a profile before opening the CurseForge mod browser.')
    def selectProfile(self, profile):
        for button in self.findChildren(ProfileButton):
            button.setChecked(False)
        for btn in self.findChildren(ProfileButton):
            if btn.name == profile:
                self.selectedProfile = btn
                btn.setChecked(True)
                break
        if self.selectedProfile:
            self.selectedProfile.setChecked(True)
        with open(f"{cwd}/profiles.json","r") as f:
            profiles = json.load(f)
        for profile in profiles["profiles"]:
            if profile["name"] == self.selectedProfile.name:
                ver=profile["version"]
                loader=profile["loader"]
                name = profile["name"]
                self.update_info_label(f"Name: {name}   Version: {ver}   Loader: {loader}")
    def launch(self):

        with open(f"{cwd}/accounts.json","r") as f:
            accounts = json.load(f)
        username = accounts["active"]   
        for account in accounts["accounts"]:
            if account["username"] == username:
                uuid = account["uuid"]
                token = account["token"]
                index = accounts["accounts"].index(account)
                if accounts["refresh"]["launch"] == "1":
                    try:
                        refresh_token = account["refresh_token"]
                    except:
                        refresh_token = None
                    if refresh_token:
                        try:
                            account_informaton = mc.microsoft_account.complete_refresh(CLIENT_ID, None, REDIRECT_URL, refresh_token)
                            username = account_informaton["name"]
                            uuid = account_informaton["id"]
                            token = account_informaton["access_token"]
                            accounts["accounts"][index]["username"] = username
                            accounts["accounts"][index]["uuid"] = uuid
                            accounts["accounts"][index]["token"] = token
                            with open(f"{cwd}/accounts.json","w") as f:
                                json.dump(accounts,f)
                        except:
                            pass
        options ={
                "username": username,
                "uuid": uuid,
                "token": token
            }
        if self.selectedProfile:
            try:
                if ex.runningprofiles[self.selectedProfile.name] > 0:
                    abc = True
                else:
                    abc = False 
            except:
                ex.runningprofiles[self.selectedProfile.name] = 1
                abc = False
            a=0
            if abc:
                # Ask for confirmation before launching another instance
                reply = QMessageBox.question(self, 'Confirmation', f'This instance is already running. Are you sure you want to launch another one?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:  
                    ex.runningprofiles[self.selectedProfile.name] = ex.runningprofiles[self.selectedProfile.name] +1
                    with open(f"{cwd}/profiles.json","r") as f:
                        profiles = json.load(f)
                    for profile in profiles["profiles"]:
                        if profile["name"] == self.selectedProfile.name:
                            ver=profile["version"]
                            loader=profile["loader"]
                            name=profile["name"]
                            jvm=profile["jvm"]
                    if loader == "FABRIC":
                        if not mc.fabric.is_minecraft_version_supported(ver):
                            a=1
                            QMessageBox.warning(self,"Unsupported",f"Minecraft version {ver} is not supported by Fabric!")
                    if loader == "FORGE":
                        if not mc.forge.find_forge_version(ver):
                            a=1
                            QMessageBox.warning(self,"Unsupported",f"Minecraft version {ver} is not supported by Forge!")
                    if a==0:
                        self.launch_thread = LaunchGame(ver,options,name,loader,jvm)
                        self.launch_thread.detect_crash.connect(self.showmessage)
                        self.launch_thread.start()
                    else:  
                        try:
                            ex.runningprofiles[self.selectedProfile.name] = ex.runningprofiles[self.selectedProfile.name] -1
                        except:
                            ex.runningprofiles[self.selectedProfile.name] = 0
                else:
                    pass
            else:
                with open(f"{cwd}/profiles.json","r") as f:
                    profiles = json.load(f)
                for profile in profiles["profiles"]:
                    if profile["name"] == self.selectedProfile.name:
                        ver=profile["version"]
                        loader=profile["loader"]
                        name=profile["name"]
                        jvm=profile["jvm"]
                if loader == "FABRIC":
                    if not mc.fabric.is_minecraft_version_supported(ver):
                        a=1
                        QMessageBox.warning(self,"Unsupported",f"Minecraft version {ver} is not supported by Fabric!")
                if loader == "FORGE":
                    if not mc.forge.find_forge_version(ver):
                        a=1
                        QMessageBox.warning(self,"Unsupported",f"Minecraft version {ver} is not supported by Forge!")
                if a==0:
                    self.launch_thread = LaunchGame(ver,options,name,loader,jvm)
                    self.launch_thread.detect_crash.connect(self.showmessage)
                    self.launch_thread.confirm_legacy.connect(self.install_legacy_forge)
                    self.launch_thread.start()
                    
                else:
                    try:
                        ex.runningprofiles[self.selectedProfile.name] = ex.runningprofiles[self.selectedProfile.name] -1
                    except:
                        ex.runningprofiles[self.selectedProfile.name] = 0
        else:
            QMessageBox.warning(self, 'No Profile Selected', 'Please select a profile before launching.')

    def install_legacy_forge(self):
        legacy_forge_installed = os.path.exists(f"{cwd}/.minecraft/1.8.9-forge1.8.9-11.15.1.2318-1.8.9")

        if legacy_forge_installed:
            return True

        reply = QMessageBox.question(self, 'Confirmation', 'Legacy Forge support is not installed. Do you want to install it? It requires 1.03GB of disk space. It is required for forge 1.12.2 - 1.5.2')

        if reply == QMessageBox.StandardButton.Yes:
            download_dialog = DownloadAndExtractLegacyForge()
            download_dialog.exec()


            return True

        return False

    def settings(self):
        dialog = AccountManagementDialog(self)
        dialog.exec()

    def addProfile(self):
        dialog = AddProfileDialog(self)
        if dialog.exec():
            # Refresh the profile buttons
            for i in range(self.profileGrid.count()):
                try:
                    widget = self.profileGrid.itemAt(i).widget()
                    if isinstance(widget, ProfileButton):
                        self.profileGrid.removeWidget(widget)
                        widget.deleteLater()
                except:
                    pass

            with open(f"{cwd}/profiles.json","r") as f:
                self.profiles = json.load(f)
            for i, profile in enumerate(self.profiles["profiles"]):
                if profile["icon_type"] == "default":
                    if os.path.exists(f"{cwd}/icons/profiles/"+profile["icon"]):
                        button = ProfileButton(profile["name"], f"{cwd}/icons/profiles/"+profile["icon"],self.profileGrid, self)
                    else:
                        button = ProfileButton(profile["name"], f"{cwd}/icons/profiles/minecraft.png", self.profileGrid, self)
                else:
                    if os.path.exists(profile["icon"]):
                        button = ProfileButton(profile["name"], profile["icon"],self.profileGrid, self)
                    else:
                        button = ProfileButton(profile["name"], f"{cwd}/icons/profiles/minecraft.png",self.profileGrid, self)
                button.clicked.connect(lambda checked, p=profile["name"]: self.selectProfile(p))
                self.profileGrid.addWidget(button, i // 4, i % 4)
class RepairThread(QThread):
    # Define a signal that sends a string
    repair_done = pyqtSignal(str,str)

    def __init__(self, version, mcdir, callback, name,loader):
        super().__init__()
        self.version = version
        self.mcdir = mcdir
        self.callback = callback
        self.name = name
        self.loader = loader

    def run(self):
        premium_account = False
        with open(f"{cwd}/accounts.json", "r", encoding="utf-8") as f:
            accounts = json.load(f)
        for account in accounts["accounts"]:
            index = accounts["accounts"].index(account)
            try:
                refresh_token = account["refresh_token"]
            except:
                refresh_token = None
            if refresh_token:
                premium_account = True
        if self.loader == "VANILLA":
            if premium_account:
                mc.install.install_minecraft_version(self.version,self.mcdir,self.callback)
                self.repair_done.emit("Done",f'Successfully repaired {self.name}!')
            else:
                self.repair_done.emit("Error",f'Unfortunately, you cannot download minecraft without having a premium account added, Please add at least a single microsoft account to play!')
        elif self.loader == "FABRIC":
            if premium_account:
                mc.install.install_minecraft_version(self.version, f"{mcdir}", callback=self.callback)
                mc.fabric.install_fabric(self.version, mcdir,callback=self.callback)
            else:
                self.repair_done.emit("Error",f'Unfortunately, you cannot download minecraft without having a premium account added, Please add at least a single microsoft account to play!')

        elif self.loader == "FORGE":
            if premium_account:
                forge_version = mc.forge.find_forge_version(self.version)
                if mc.forge.supports_automatic_install(forge_version):
                    mc.install.install_minecraft_version(self.version, f"{mcdir}", callback=self.callback)
                    mc.forge.install_forge_version(forge_version, f"{mcdir}", callback=self.callback)
            else:
                self.repair_done.emit("Error",f'Unfortunately, you cannot download minecraft without having a premium account added, Please add at least a single microsoft account to play!')

class LaunchGame(QThread):
    # Define a signal that sends a string
    detect_crash = pyqtSignal(str,str)
    confirm_legacy = pyqtSignal()
    def __init__(self,ver,options,name,loader,jvm):
        super().__init__()
        self.ver = ver
        self.mcdir = mcdir
        self.options = options
        self.loader = loader
        self.jvm = jvm
        self.name = name

    def run(self):
        def set_status(status: str):
            print(status)
            if status == "Installation complete":
                ex.launchButton.setText("Launch")
        def set_progress(progress: int):
            if current_max != 0:
                print(f"{progress}/{current_max}")
                ex.launchButton.setText(f"{progress}/{current_max}")

        def set_max(new_max: int):
            global current_max
            current_max = new_max


        callback = {
            "setStatus": set_status,
            "setProgress": set_progress,
            "setMax": set_max
        }
        
        versions = mc.utils.get_installed_versions(f"{mcdir}")
        keys = []
        premium_account = False
        with open(f"{cwd}/accounts.json", "r", encoding="utf-8") as f:
            accounts = json.load(f)
        for account in accounts["accounts"]:
            index = accounts["accounts"].index(account)
            try:
                refresh_token = account["refresh_token"]
            except:
                refresh_token = None
            if refresh_token:
                premium_account = True
        if self.loader == "VANILLA":
            for dict in versions:   
                keys.append(dict["id"])
            if not self.ver in keys:
                if premium_account:
                    mc.install.install_minecraft_version(self.ver, f"{mcdir}", callback=callback)
                else:
                    self.detect_crash.emit("Error",f'Unfortunately, you cannot download minecraft without having a premium account added, Please add at least a single microsoft account to play!')
            try:
                cmd = mc.command.get_minecraft_command(self.ver,f"{mcdir}",self.options)
                cmd[cmd.index("--gameDir")+1] = f"{cwd}/profiles/{self.name}"
                if not self.jvm == "BI":
                    cmd[0] = self.jvm
            except:
                cmd = ["java","--version"]
            os.makedirs(f"{cwd}/profiles/{self.name}",exist_ok=True)
            os.chdir(f"{cwd}/profiles/{self.name}")
            exitcode = subprocess.run(cmd)
            try:
                ex.runningprofiles[self.name] = ex.runningprofiles[self.name] -1
            except:
                ex.runningprofiles[self.name] = 0
            if not exitcode.returncode == 0:
                self.detect_crash.emit("Crash",f'Instance {self.name} crashed with exit code {exitcode.returncode}!')
        elif self.loader == "FABRIC":
            loader = mc.fabric.get_latest_loader_version()
            versions = mc.utils.get_installed_versions(mcdir)
            vername = f"fabric-loader-{loader}-{self.ver}" 
            keys = []
            for dict in versions:
                keys.append(dict["id"])
            if not vername in keys:
                if premium_account:
                    mc.install.install_minecraft_version(self.ver, f"{mcdir}", callback=callback)
                    mc.fabric.install_fabric(self.ver, mcdir,callback=callback)
                else:
                    self.detect_crash.emit("Error",f'Unfortunately, you cannot download minecraft without having a premium account added, Please add at least a single microsoft account to play!')
            try:
                cmd = mc.command.get_minecraft_command(vername,f"{mcdir}",self.options)
                cmd[cmd.index("--gameDir")+1] = f"{cwd}/profiles/{self.name}"
                if not self.jvm == "BI":
                    cmd[0] = self.jvm
            except:
                cmd = ["java","--version"]  
            os.makedirs(f"{cwd}/profiles/{self.name}",exist_ok=True)
            os.chdir(f"{cwd}/profiles/{self.name}")
            exitcode = subprocess.run(cmd)
            try:
                ex.runningprofiles[self.name] = ex.runningprofiles[self.name] -1
            except:
                ex.runningprofiles[self.name] = 0
            if not exitcode.returncode == 0:
                self.detect_crash.emit("Crash",f'Instance {self.name} crashed with exit code {exitcode.returncode}!')      
        elif self.loader == "FORGE":
            forge_version = mc.forge.find_forge_version(self.ver)
            versions = mc.utils.get_installed_versions(mcdir)
            keys = []
            keys2= []
            for dict in versions:
                if "forge" in dict["id"].lower():
                    if dict["id"].lower().startswith(f"{self.ver}-forge"):
                        keys.append(dict["id"])
                keys2.append(dict["id"])
            a=0
            b=0
            if keys == []:
                if premium_account:
                    if mc.forge.supports_automatic_install(forge_version):
                        mc.install.install_minecraft_version(self.ver, f"{mcdir}", callback=callback)
                        mc.forge.install_forge_version(forge_version, f"{mcdir}", callback=callback)
                    else:
                        if not os.path.exists(f"{cwd}/.minecraft/versions/1.8.9-forge1.8.9-11.15.1.2318-1.8.9"):
                            self.confirm_legacy.emit()
                            a=1
                else:
                    b=1
                    self.detect_crash.emit("Error",f'Unfortunately, you cannot download minecraft without having a premium account added, Please add at least a single microsoft account to play!')
            if not a==1:
                if not self.ver in keys2:
                    if b==0:
                        if premium_account:
                            mc.install.install_minecraft_version(self.ver, f"{mcdir}", callback=callback)
                        else:
                            self.detect_crash.emit("Error",f'Unfortunately, you cannot download minecraft without having a premium account added, Please add at least a single microsoft account to play!')

                keys = []
                for dict in versions:
                    if "forge" in dict["id"].lower():
                        if dict["id"].lower().startswith(f"{self.ver}-forge"):
                            keys.append(dict["id"])
                try:
                    cmd = mc.command.get_minecraft_command(keys[0],f"{mcdir}",self.options)
                    cmd[cmd.index("--gameDir")+1] = f"{cwd}/profiles/{self.name}"
                    if not self.jvm == "BI":
                        cmd[0] = self.jvm
                except:
                    cmd = ["java","--version"]
                
                os.makedirs(f"{cwd}/profiles/{self.name}",exist_ok=True)
                os.chdir(f"{cwd}/profiles/{self.name}")
                exitcode = subprocess.run(cmd)
                try:
                    ex.runningprofiles[self.name] = ex.runningprofiles[self.name] -1
                except:
                    ex.runningprofiles[self.name] = 0
                if not exitcode.returncode == 0:
                    self.detect_crash.emit("Crash",f'Instance {self.name} crashed with exit code {exitcode.returncode}!')      

if __name__ == '__main__':
    try:
        import pyi_splash # type: ignore
        pyi_splash.update_text('FINISHING...')
    except:
        pass
    if len(sys.argv) > 1:
        test = sys.argv[1]
    else:
        test = "notest"
    if not test == "test":
        restart = 1
        while restart == 1:
            restart = 0
            app = QApplication(sys.argv)
            app.setStyle('Fusion')  # Set the application style to Fusion
            app.setPalette(QPalette(QColor(30, 30, 30)))  # Set the application palette to dark
            ex = Launcher()
            ex.show()
            exitcode = app.exec()
            del app
            del ex
        sys.exit(exitcode)
    else:
        print("Works :D")