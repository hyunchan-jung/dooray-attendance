from utils import *

import sys
from time import sleep
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from subprocess import CREATE_NO_WINDOW

SERVICE = Service(ChromeDriverManager().install())
SERVICE.creationflags = CREATE_NO_WINDOW
AGENT = 'Mozilla/5.0 (Windows NT 4.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
        'Chrome/37.0.2049.0 Safari/537.36'


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
