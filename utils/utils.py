import os
import sys
import json
from win10toast_click import ToastNotifier

USER_PATH = os.path.expanduser('~')
PATH = os.path.join(USER_PATH, '.dooray')
TOASTER = ToastNotifier()


def show_toast(msg, callback_func=None):
    TOASTER.show_toast(
        title='dooray_attendance',
        msg=msg,
        icon_path='',
        duration=3,
        threaded=True,
        callback_on_click=callback_func
    )


def raise_error(msg=None, driver=None):
    if driver is not None:
        try:
            driver.quit()
        finally:
            pass

    os.startfile(PATH)
    if msg is None:
        show_toast('Input ID, PW in settings.json with notepad')
    else:
        show_toast(msg)
    sys.exit(0)


class Settings:
    def __init__(self):
        self.id = None
        self.pw = None
        self.domain = None
        self.working_time = None

        self.load_settings()

    def load_settings(self):
        os.makedirs(PATH, exist_ok=True)
        if 'settings.json' not in os.listdir(PATH):
            json.dump({
                'ID': '',
                'PW': '',
                'domain': '',
                'WorkingTime(hours)': 9,
            }, open(os.path.join(PATH, 'settings.json'), 'w'), indent=4)
            raise_error()

        info = json.load(open(os.path.join(PATH, 'settings.json')))
        self.id, self.pw, self.domain, self.working_time = map(info.get, ['ID', 'PW', 'domain', 'WorkingTime(hours)'])
        if '' in [self.id, self.pw, self.domain, self.working_time]:
            raise_error()

    def encryption_pw(self):
        # TODO: Check dooray login and encrypt password in settings.json
        pass

    def decryption_pw(self):
        # TODO: Decrypt password in settings.json
        pass
