import os
import sys
import json
from datetime import datetime, timedelta
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from subprocess import CREATE_NO_WINDOW

from win10toast_click import ToastNotifier
from apscheduler.schedulers.background import BlockingScheduler

USER_PATH = os.path.expanduser('~')
PATH = os.path.join(USER_PATH, '.dooray')

TOASTER = ToastNotifier()
SERVICE = Service(ChromeDriverManager().install())
SERVICE.creationflags = CREATE_NO_WINDOW

AGENT = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
        'Chrome/37.0.2049.0 Safari/537.36'


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


def load_setting():
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
    ID, PW, domain, working_time = map(info.get, ['ID', 'PW', 'domain', 'WorkingTime(hours)'])
    if '' in [ID, PW, domain, working_time]:
        raise_error()

    return ID, PW, domain, working_time


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


def go_attendance_page(driver):
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
    return driver


def start_attendance(driver):
    # TODO: run attendance
    driver.quit()


def end_attendance():
    driver = init_driver()
    driver = go_attendance_page(driver)

    end_at = driver.find_elements(By.CLASS_NAME, 'check-time')[1].text
    if end_at != '-':
        show_toast('이미 퇴근')
        driver.quit()
        sys.exit(0)

    # driver.find_elements(By.CLASS_NAME, 'check-button.eZWsHA.m.primary')[1].click()
    sleep(1)
    show_toast('퇴근 성공')
    driver.quit()
    sys.exit(0)


def get_attendance_time():
    driver = init_driver()
    driver = go_attendance_page(driver)

    if driver.find_elements(By.CLASS_NAME, 'check-time')[0].text == '-':
        show_toast('클릭해서 출근', lambda: start_attendance(driver))
        sleep(2)
        driver.quit()
        return

    year, month, day = map(int, driver.find_element(By.CLASS_NAME, 'current__date').text.split('.')[:-1])
    hour, minute, second = map(int, driver.find_elements(By.CLASS_NAME, 'check-time')[0].text.split(':'))
    attendance_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

    driver.quit()

    return attendance_time


if __name__ == '__main__':
    ID, PW, domain, working_time = load_setting()

    while True:
        attendance_time = get_attendance_time()
        if attendance_time is not None:
            attendance_end_time = attendance_time + timedelta(hours=working_time, minutes=1)
            show_toast(f'퇴근시간: {attendance_end_time}')
            break
        sleep(120)

    scheduler = BlockingScheduler(timezone='Asia/Seoul')
    scheduler.add_job(end_attendance, 'date', run_date=attendance_end_time)
    scheduler.start()
