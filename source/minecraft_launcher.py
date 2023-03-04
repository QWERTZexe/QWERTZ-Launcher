import os, sys
import minecraft_launcher_lib
import subprocess
import tkinter as tk
import microsoftlogin
from tkinter import messagebox
import tkinter.ttk as ttk
import ctypes
from PIL import Image, ImageTk
from tkinter import font, filedialog
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QUrl, QLocale
import json, shutil
app = QApplication(sys.argv)
cwd = os.path.dirname(sys.argv[0])
mods_folder = ""
# This line sets the language of the webpage to the system language
QWebEngineProfile.defaultProfile().setHttpAcceptLanguage(QLocale.system().name().split("_")[0])
w = microsoftlogin.LoginWindow()
app.exec()
ctypes.windll.shcore.SetProcessDpiAwareness
beab = 0
version = ""
user = ""
with open(f"{cwd}\\secrets.txt","r") as f:
    secrets =f.read().splitlines()
    user = secrets[1]
    token = secrets[0]
    uuid = secrets[2]
    print(f"{user}\n{uuid}\n{token}")
def askopenfile():
    dire =filedialog.askdirectory(title="SELECT MODS FOLDER")
    inputtxt2.delete("1.0", "end")  # if you want to remove the old data
    inputtxt2.insert("end",dire)
def getopts():
    global inputtxt3
    global user, version, inputtxt2, beab, uuid, token, version_select, loader, fastserver
    version = version_select.get()
    fastserver = inputtxt3.get("1.0", "end").splitlines()
    fastserver = fastserver[0]
   # user = inputtxt2.get("1.0", "end").splitlines()
    beab = 1

    if version == "":
        root.destroy()
        sys.exit()
    else:
        loader = "VANILLA"
        print(version)
        print(user)
        root.destroy()
def getoptsfabric():
    global user, version, inputtxt3, inputtxt2, beab, uuid, token, version_select, loader, fastserver
    version = version_select.get()
    mods_folder = inputtxt2.get("1.0", "end").splitlines()
    mods_folder = mods_folder[0]
    fastserver =inputtxt3.get("1.0", "end").splitlines()
    fastserver = fastserver[0]
    beab = 1
    if version == "":
        root.destroy()
        sys.exit()
    else:
        loader = "FABRIC"
        try:
            shutil.rmtree(f"{mods_directory}")
        except:
            pass
        if not mods_folder == "":
            try:
                shutil.copytree(f'{mods_folder}', f'{mods_directory}')
                print(version)
                print(user)
                root.destroy()
            except:
                messagebox.showerror("QWERTZ LAUNCHER",f"Invalid mods folder! ({mods_folder})")
        else:
            root.destroy()
def getoptsforge():
    global user, version, inputtxt3, inputtxt2, beab, uuid, token, version_select, loader, fastserver
    version = version_select.get()
    mods_folder = inputtxt2.get("1.0", "end").splitlines()
    mods_folder = mods_folder[0]
    fastserver =inputtxt3.get("1.0", "end").splitlines()
    fastserver = fastserver[0]
    beab = 1
    if version == "":
        root.destroy()
        sys.exit()
    else:
        loader = "FORGE"
        try:
            shutil.rmtree(f"{mods_directory}")
        except:
            pass
        if not mods_folder == "":
            try:
                shutil.copytree(f'{mods_folder}', f'{mods_directory}')
                print(version)
                print(user)
                root.destroy()
            except:
                messagebox.showerror("QWERTZ LAUNCHER",f"Invalid mods folder! ({mods_folder})")
        else:
            root.destroy()

def resize_image(event):
    new_width = event.width
    new_height = event.height
    image = copy_of_image.resize((root.winfo_width(), root.winfo_height()))
    photo = ImageTk.PhotoImage(image)
    background_label.config(image = photo)
    background_label.image = photo #avoid garbage collection
def mainscreen():
    global root, inputtxt2, background_label, copy_of_image, version_select, inputtxt3
    root = tk.Tk()
    root.title("QWERTZ LAUNCHER")
    #image2 =tk.Image(f"{cwd}\\background.png")
    image = Image.open(f"{cwd}\\background.png")
    copy_of_image = image.copy()
    photo = ImageTk.PhotoImage(image)
    background_label = tk.Label(root, image=photo)
    background_label.place(x=0,y=0)
    background_label.bind('<Configure>', resize_image)
    versions = minecraft_launcher_lib.utils.get_available_versions(minecraft_directory)
    version_list = []

    for i in versions:
        if "." in i["id"] and not "fabric" in i["id"] and not "forge" in i["id"]:
            version_list.append(i["id"])

    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("500x500")
    root.state("zoomed")
    subwidget = tk.Frame(root)
    subwidget.pack(side="right")
    label5 = tk.Label(subwidget,text=f"LAUNCH INTO SERVER")
    label5.pack()
    inputtxt3 = tk.Text(subwidget,
                    height = 1,
                    width = 10)
    inputtxt3.pack()
    label = tk.Label(root,text="MODS FOLDER")
    label.pack(pady=(180,0))
    button = tk.Button(text='Browse', command=askopenfile)
    button.pack()
    inputtxt2 = tk.Text(root,
                    height = 1,
                    width = 60)
    inputtxt2.pack()
    label2 = tk.Label(root,text="VERSION")
    label2.pack(pady=(50,0))

            # Get the code from the url
            # Do the login
    version_select = ttk.Combobox(root, values=version_list)
    version_select.pack(pady=(0,0))
    version_select.current(0)

    btnIco = tk.Button(root, text="LAUNCH",bg='green', command=getopts)
    helv36 = font.Font(family='Helvetica', size=36, weight='bold')
    btnIco["font"] = helv36
   # label4["font"] = helv36
    btnIco.pack()
    btnIco3 = tk.Button(root, text="LAUNCH FORGE",bg='orange', command=getoptsforge)
    helv36 = font.Font(family='Helvetica', size=36, weight='bold')
    btnIco3["font"] = helv36
   # label4["font"] = helv36
    btnIco3.pack()
    btnIco2 = tk.Button(root, text="LAUNCH FABRIC",bg='red', command=getoptsfabric)
    helv36 = font.Font(family='Helvetica', size=36, weight='bold')
    btnIco2["font"] = helv36
   # label4["font"] = helv36
    btnIco2.pack()

    label4 = tk.Label(root,text=f"Logged in as: {user}")
    label4.place(x=1,y=1)

    root.mainloop()
    os.system("cls")
minecraft_directory = f"{cwd}\\installations\\.minecraft"
mods_directory = f"{minecraft_directory}\\mods\\"
os.chdir(cwd)
print(mods_directory)
mainscreen()
if beab == 0:
    sys.exit()
def getcommand(usr,ver):
    global minecraft_directory, mods_directory, current_max, uuid, token,loader
    current_max = 0


    def set_status(status: str):
        print(status)
        pass

    def set_progress(progress: int):
        if current_max != 0:
            pass
            print(f"{progress}/{current_max}")

    def set_max(new_max: int):
        global current_max
        current_max = new_max


    callback = {
        "setStatus": set_status,
        "setProgress": set_progress,
        "setMax": set_max
    }
    if loader == "VANILLA":
        versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
        print(versions)
        # sys.exit()
        keys = []
        for dict in versions:
            keys.append(dict["id"])
        if not ver in keys:
            minecraft_launcher_lib.install.install_minecraft_version(ver, minecraft_directory, callback=callback)
        print(f"{usr}\n{uuid}\n{token}")
        options ={
            "username": usr,
            "uuid": uuid,
            "token": token
        }
        minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(ver, minecraft_directory, options)
        return minecraft_command
    elif loader == "FABRIC":
        if not minecraft_launcher_lib.fabric.is_minecraft_version_supported(ver):
            print("This version is not supported by fabric")
            messagebox.showwarning("QWERTZ LAUNCHER",f"This version ({ver}) is not supported by Fabric!")
            return None
        else:
            loader = minecraft_launcher_lib.fabric.get_latest_loader_version()
            versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
            vername = f"fabric-loader-{loader}-{ver}" 
            print(vername)
            print(versions)
            # sys.exit()
            keys = []
            for dict in versions:
                keys.append(dict["id"])
            if not vername in keys:
                minecraft_launcher_lib.fabric.install_fabric(ver, minecraft_directory, callback=callback)
            print(f"{usr}\n{uuid}\n{token}")
            options ={
                "username": usr,
                "uuid": uuid,
                "token": token
            }
            
            
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(vername, minecraft_directory, options)
            return minecraft_command
    elif loader == "FORGE": 
        forge_version = minecraft_launcher_lib.forge.find_forge_version(ver)
        if forge_version is None:
            messagebox.showwarning("QWERTZ LAUNCHER",f"This Minecraft Version ({ver}) is not supported by Forge!")
            return None
        else:
            versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
            print(forge_version)
            print(versions)
            # sys.exit()
            forgever = forge_version
            forge_version = forge_version.split("-")
            keys = []
            for dict in versions:
                if "forge" in dict["id"]:
                    if dict["id"].startswith(ver):
                        if forge_version[1] in dict["id"]:
                            keys.append(dict["id"])
                            break
            if keys == []:
                if minecraft_launcher_lib.forge.supports_automatic_install(forgever):
                    minecraft_launcher_lib.forge.install_forge_version(forgever, minecraft_directory, callback=callback)
                else:
                    print(f"Forge {forgever} can't be installed automatic.")
                    messagebox.showwarning("QWERTZ LAUNCHER",f'Forge {ver} cant be installed automatic. The Forge Installer will now start. This is your minecraft path: "{minecraft_directory}"')
                    minecraft_launcher_lib.forge.run_forge_installer(forgever,minecraft_directory, callback=callback)
                keys = []
                for dict in versions:
                    if "forge" in dict["id"]:
                        if dict["id"].startswith(ver):
                            if forge_version[1] in dict["id"]:
                                keys.append(dict["id"])
                                break
            print(f"{usr}\n{uuid}\n{token}")
            options ={
                "username": usr,
                "uuid": uuid,
                "token": token
            }
            
            try:
                minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(keys[0], minecraft_directory, options)
                return minecraft_command
            except:
                return None
minecraft_command = getcommand(user,version)
print(minecraft_command)
if not fastserver == "":
    minecraft_command.append("--server")
    minecraft_command.append(fastserver)
if not minecraft_command == None:

    re = subprocess.run(minecraft_command)
else:
    re = "-1"
print("MINECRAFT ENDED!")
while True:
    try:
        if not re.returncode == "0":
            messagebox.showerror("QWERTZ LAUNCHER",f"Minecraft has crashed with exit code: {str(re.returncode)}! We are very sorry!")
        else:
            messagebox.showinfo("QWERTZ LAUNCHER","Minecraft has exited!")
    except:
         pass
    beab = 0
    mainscreen()
    if beab == 0:
        sys.exit()
    minecraft_command = getcommand(user,version)
    if not fastserver == "":
        minecraft_command.append("--server")
        minecraft_command.append(fastserver)
    if not minecraft_command == None:
        re = subprocess.run(minecraft_command)
    