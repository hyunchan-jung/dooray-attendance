from utils import *

import os
import sys
import requests
from time import sleep
from datetime import datetime, timedelta
from zipfile import ZipFile

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from subprocess import CREATE_NO_WINDOW

USER_PATH = os.path.expanduser('~')
PATH = os.path.join(USER_PATH, '.dooray')

CHROMIUM_PATH = os.path.join(PATH, 'chrome-win/chrome.exe')
DRIVER_PATH = os.path.join(PATH, 'chromedriver_win32/chromedriver.exe')

SERVICE = Service(executable_path=DRIVER_PATH)
SERVICE.creationflags = CREATE_NO_WINDOW
AGENT = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
        'Chrome/37.0.2049.0 Safari/537.36'


def download_browser_and_driver():
    base_url = 'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Win_x64%2F1000027%2F'
    chromium_zip = 'chrome-win.zip'
    driver_zip = 'chromedriver_win32.zip'
    chromium_url = base_url + f'{chromium_zip}?alt=media'
    driver_url = base_url + f'{driver_zip}?alt=media'

    def download_file(url, file):
        res = requests.get(url)
        download_fp = os.path.join(PATH, file)
        with open(download_fp, 'wb') as f:
            f.write(res.content)
        ZipFile(download_fp).extractall(PATH)
        os.remove(download_fp)

    if not os.path.exists(CHROMIUM_PATH):
        download_file(chromium_url, chromium_zip)
    if not os.path.exists(DRIVER_PATH):
        download_file(driver_url, driver_zip)


def init_driver():
    options = webdriver.ChromeOptions()
    options.binary_location = CHROMIUM_PATH
    options.add_argument(f'user-agent={AGENT}')
    options.add_argument('disable-gpu')
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('headless')
    driver = webdriver.Chrome(service=SERVICE, options=options)
    driver.set_window_size(1920, 1080)
    return driver


def move_attendance_page(driver, auth_info):
    driver.get('https://dooray.com/orgs')
    sleep(1)

    elem = driver.find_element(By.ID, 'subdomain')
    elem.send_keys(auth_info['domain'])
    sleep(1)

    elem = driver.find_element(By.CLASS_NAME, 'btn.btn-primary.btn-lg.next-btn')
    if elem.get_attribute('disabled') == 'true':
        raise_error('일치하는 도메인 정보 없음', driver)
    elem.click()

    elem_id, elem_pw = driver.find_elements(By.CLASS_NAME, 'input-box > input')

    elem_id.send_keys(auth_info['id'])
    elem_pw.send_keys(auth_info['pw'])
    elem_pw.send_keys(Keys.ENTER)
    # TODO: Authentication Error
    sleep(2)

    driver.find_element(By.CLASS_NAME, 'icon-gnb-menu').click()
    driver.find_element(By.CLASS_NAME, 'icon-service-icon-manage-work-schedule').click()
    sleep(2)
    return driver


def get_attendance_time(auth_info):
    driver = init_driver()
    driver = move_attendance_page(driver, auth_info)

    year, month, day = map(int, driver.find_element(By.CLASS_NAME, 'current__date').text.split('.')[:-1])
    attendance_time = [i.text for i in driver.find_elements(By.CLASS_NAME, 'check-time')]

    for n, time in enumerate(attendance_time):
        if time != '-':
            hour, minute, second = map(int, attendance_time[n].split(':'))
            attendance_time[n] = datetime(year, month, day, hour, minute, second)

    driver.quit()
    return attendance_time


def start_attendance(driver):
    driver.find_elements(By.CLASS_NAME, 'check-button.eZWsHA.m.primary')[0].click()
    sleep(3)
    show_toast('출근 성공')
    driver.quit()
    sys.exit(0)


def end_attendance():
    driver = init_driver()
    driver = move_attendance_page(driver)

    end_at = driver.find_elements(By.CLASS_NAME, 'check-time')[1].text
    if end_at != '-':
        show_toast('이미 퇴근')
        driver.quit()
        sys.exit(0)

    driver.find_elements(By.CLASS_NAME, 'check-button.eZWsHA.m.primary')[1].click()
    sleep(3)
    show_toast('퇴근 성공')
    driver.quit()
    sys.exit(0)


download_browser_and_driver()
