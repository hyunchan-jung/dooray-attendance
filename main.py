import os
import sys
import json
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from subprocess import CREATE_NO_WINDOW

from win10toast import ToastNotifier
from apscheduler.schedulers.background import BlockingScheduler

TOASTER = ToastNotifier()
SERVICE = Service(ChromeDriverManager().install())
SERVICE.creationflags = CREATE_NO_WINDOW

AGENT = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                 'Chrome/37.0.2049.0 Safari/537.36'


def show_toast(msg):
    TOASTER.show_toast(
        title='dooray',
        msg=msg,
        icon_path='',
        duration=5,
        threaded=True
    )


def load_setting():
    base_path = os.path.expanduser('~')
    path = os.path.join(base_path, '.dooray')
    os.makedirs(path, exist_ok=True)

    def error():
        os.startfile(path)
        show_toast('input ID, PW in info.json with notepad')
        sys.exit(0)

    if 'info.json' not in os.listdir(path):
        json.dump({
            'ID': '',
            'PW': '',
            'domain': 'agilegrowth',
            'WorkingTime(hours)': 9,
            'UpdateTime(minutes)': 10
        }, open(os.path.join(path, 'info.json'), 'w'), indent=4)
        error()

    info = json.load(open(os.path.join(path, 'info.json')))
    ID, PW, domain, working_time, update_time = \
        map(info.get, ['ID', 'PW', 'domain', 'WorkingTime(hours)', 'UpdateTime(minutes)'])
    if ID == '' or PW == '' or domain == '':
        error()

    return ID, PW, domain, working_time, update_time


def main(ID, PW, domain, working_time):
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={AGENT}')
    options.add_argument('headless')
    driver = webdriver.Chrome(service=SERVICE, options=options)
    driver.set_window_size(1920, 1080)
    driver.get('https://dooray.com/orgs')
    sleep(1)

    elem = driver.find_element(By.ID, 'subdomain')
    elem.send_keys(domain)
    sleep(1)

    elem = driver.find_element(By.CLASS_NAME, 'btn.btn-primary.btn-lg.next-btn')
    if elem.get_attribute('disabled') == 'true':
        show_toast('일치하는 도메인 정보 없음')
        driver.quit()
    elem.click()

    elem_id, elem_pw = driver.find_elements(By.CLASS_NAME, 'input-box > input')

    elem_id.send_keys(ID)
    elem_pw.send_keys(PW)
    elem_pw.send_keys(Keys.ENTER)
    sleep(2)

    driver.find_element(By.CLASS_NAME, 'icon-gnb-menu').click()
    driver.find_element(By.CLASS_NAME, 'icon-service-icon-manage-work-schedule').click()
    sleep(2)

    year, month, day = map(int, driver.find_element(By.CLASS_NAME, 'current__date').text.split('.')[:-1])

    start_at, end_at = map(lambda x: x.text, driver.find_elements(By.CLASS_NAME, 'check-time'))
    is_start, is_end = map(lambda x: x != '-', [start_at, end_at])

    if not is_start:
        show_toast('출근안함')
        driver.quit()
    elif is_end:
        show_toast('이미퇴근함')
        driver.quit()
        sys.exit(0)

    def get_time(str_time):
        hour, minute, second = map(int, str_time.split(':'))
        timedelta = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        return timedelta

    time_diff = (datetime.now() - get_time(start_at)).total_seconds() / 3600

    if time_diff >= working_time:
        driver.find_elements(By.CLASS_NAME, 'check-button.eZWsHA.m.primary')[1].click()
        sleep(1)
        show_toast('퇴근성공')
        driver.quit()
        sys.exit(0)


if __name__ == '__main__':
    ID, PW, domain, working_time, update_time = load_setting()

    main(ID, PW, domain, working_time)

    scheduler = BlockingScheduler(timezone='Asia/Seoul')
    scheduler.add_job(main, 'interval', minutes=update_time, id='job', args=[ID, PW, domain, working_time])
    scheduler.start()
