# build script : pyinstaller main.py --onefile --name dooray-attendance --noconsole --add-data "utils;images" --icon=images/dooray.ico --clean

from utils import *

import rcc
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QAction, QStyle
from PyQt5.QtGui import QIcon
from apscheduler.schedulers.background import BackgroundScheduler

ICON = [':/images/0.ico', ':/images/1.ico', ':/images/2.ico']
TEST_ICON = ['images/0.ico', 'images/1.ico', 'images/2.ico']


class Application:
    def __init__(self, mode=None):
        self.settings = Settings()
        self.auth_info = {
            'id': self.settings.id,
            'pw': self.settings.pw,
            'domain': self.settings.domain
        }
        self.icon_set = TEST_ICON if mode == 'test' else ICON
        self.scheduler = BackgroundScheduler(timezone='Asia/Seoul')
        self.scheduler.start()

        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon(self.app)
        self.menu = QMenu()

        self.quit_action = QAction('Exit', self.app)
        self.quit_action.triggered.connect(self.app.quit)
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.setIcon(QIcon(self.icon_set[0]))
        self.set_tooltip('-', '-')
        self.tray.show()

        self.check_attendance()
        self.scheduler.add_job(self.check_attendance, 'interval', minutes=20)

    def check_attendance(self):
        attendance_time = get_attendance_time(self.auth_info)
        if attendance_time[0] != '-':
            if attendance_time[1] == '-':
                # TODO: 퇴근 스케줄러 실행(attendance_time[0] + timedelta(hours=self.settings.working_time))
                self.tray.setIcon(QIcon(self.icon_set[1]))
                self.set_tooltip(attendance_time[0], attendance_time[1])
            else:
                self.tray.setIcon(QIcon(self.icon_set[2]))
                self.set_tooltip(attendance_time[0], attendance_time[1])
                # TODO: 날짜 변경여부 체크 스케줄러 실행
        else:
            # TODO: 아직 출근 안했을 때
            self.tray.setIcon(QIcon(self.icon_set[0]))
            self.set_tooltip(attendance_time[0], attendance_time[1])

    def set_tooltip(self, t_start=None, t_end=None):
        t_start = t_start.strftime('%H:%M:%S') if isinstance(t_start, datetime) else t_start
        t_end = t_end.strftime('%H:%M:%S') if isinstance(t_end, datetime) else t_end
        self.tray.setToolTip(f'출근: {t_start}\n퇴근: {t_end}')

    def exec(self):
        self.app.exec()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        app = Application(mode='test')
    else:
        app = Application()

    sys.exit(app.exec())
