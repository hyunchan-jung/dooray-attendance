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

BASE_PATH = os.path.expanduser('~')
PATH = os.path.join(BASE_PATH, '.dooray')

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


def raise_error(msg=None, driver=None):
    if driver is not None:
        try:
            driver.quit()
        finally:
            pass

    os.startfile(PATH)
    if msg is None:
        show_toast('input ID, PW in info.json with notepad')
    else:
        show_toast(msg)
    sys.exit(1)


def load_setting():
    os.makedirs(PATH, exist_ok=True)

    if 'info.json' not in os.listdir(PATH):
        json.dump({
            'ID': '',
            'PW': '',
            'domain': '',
            'WorkingTime(hours)': 9,
            'UpdateTime(minutes)': 10
        }, open(os.path.join(PATH, 'info.json'), 'w'), indent=4)
        raise_error()

    info = json.load(open(os.path.join(PATH, 'info.json')))
    ID, PW, domain, working_time, update_time = \
        map(info.get, ['ID', 'PW', 'domain', 'WorkingTime(hours)', 'UpdateTime(minutes)'])
    if ID == '' or PW == '' or domain == '':
        raise_error()

    return ID, PW, domain, working_time, update_time


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(f'user-agent={AGENT}')
    options.add_argument('disable-gpu')
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('headless')
    driver = webdriver.Chrome(service=SERVICE, options=options)
    driver.set_window_size(1920, 1080)
    return driver


def main(ID, PW, domain, working_time):
    driver = init_driver()
    driver.get('https://dooray.com/orgs')
    sleep(1)

    elem = driver.find_element(By.ID, 'subdomain')
    elem.send_keys(domain)
    sleep(1)

    elem = driver.find_element(By.CLASS_NAME, 'btn.btn-primary.btn-lg.next-btn')
    if elem.get_attribute('disabled') == 'true':
        raise_error('일치하는 도메인 정보 없음', driver)
    elem.click()

    elem_id, elem_pw = driver.find_elements(By.CLASS_NAME, 'input-box > input')

    elem_id.send_keys(ID)
    elem_pw.send_keys(PW)
    elem_pw.send_keys(Keys.ENTER)
    # TODO: Authentication Error
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

    driver.quit()


if __name__ == '__main__':
    ID, PW, domain, working_time, update_time = load_setting()

    main(ID, PW, domain, working_time)

    scheduler = BlockingScheduler(timezone='Asia/Seoul')
    scheduler.add_job(main, 'interval', minutes=update_time, id='job', args=[ID, PW, domain, working_time])
    scheduler.start()
