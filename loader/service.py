import os
import sys
import time

import servicemanager
import win32event
import win32service
import win32serviceutil

SERVICE_NAME = "MyProtectAgent"
SERVICE_DISPLAY_NAME = "Enterprise Protection Agent"


class MyService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY_NAME

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg(f"{SERVICE_NAME} started")
        self.main()

    def main(self):
        while self.running:
            time.sleep(5)


def is_service_installed():
    try:
        status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)
        return True
    except:
        return False


def auto_install_and_start():
    """Устанавливает и запускает службу автоматически, без команд в консоли."""
    exe = sys.executable
    script = os.path.abspath(__file__)
    cmd = f'"{exe}" "{script}"'
    print("Служба не найдена — устанавливаю...")
    win32serviceutil.InstallService(
        pythonClassString=f"{__name__}.{MyService.__name__}",
        serviceName=SERVICE_NAME,
        displayName=SERVICE_DISPLAY_NAME,
        startType=win32service.SERVICE_AUTO_START,
        exeName=exe,
        exeArgs=f'"{script}"'
    )
    print("Служба установлена")
    win32serviceutil.StartService(SERVICE_NAME)
    print("Служба запущена успешно")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        win32serviceutil.HandleCommandLine(MyService)
        sys.exit(0)
    if not is_service_installed():
        auto_install_and_start()
        print("Готово. Приложение будет работать как Windows-служба.")
        sys.exit(0)
    else:
        print("Служба уже установлена. Завершаю.")
