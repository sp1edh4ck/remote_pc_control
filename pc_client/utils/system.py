import os
import platform


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
