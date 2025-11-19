import ctypes
import os
import platform
import webbrowser


def shutdown():
    system = platform.system()
    if system == "Windows":
        os.system("shutdown /s /t 0")
    elif system == "Linux":
        os.system("sudo poweroff")
    else:
        raise NotImplementedError("Операционная система не поддерживается")


def reboot():
    system = platform.system()
    if system == "Windows":
        os.system("shutdown /r /t 0")
    elif system == "Linux":
        os.system("sudo reboot")
    else:
        raise NotImplementedError("Операционная система не поддерживается")


def lock():
    ctypes.windll.user32.LockWorkStation()


def open_link(url):
    webbrowser.open(url)
