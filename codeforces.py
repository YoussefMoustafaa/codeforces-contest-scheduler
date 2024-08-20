from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta


service = Service(executable_path='chromedriver.exe')
driver = webdriver.Chrome(service=service)
driver.get('https://codeforces.com/contests')


driver.implicitly_wait(5)


def convert_to_time(str):

    input_format = "%b/%d/%Y %H:%M"

    dt = datetime.strptime(str, input_format)
    dt = dt - timedelta(minutes=5)

    iso_format = "%Y-%m-%dT%H:%M:%S"

    iso_string = dt.strftime(iso_format)

    return iso_string



table = driver.find_element(By.CLASS_NAME, 'datatable')

rows = table.find_elements(By.TAG_NAME, 'tr')
rows.pop(0)

class Contest:
    def __init__(self, title, start_time, end_time):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time


contests_list = []

for row in rows:
    contest_title = row.find_element(By.CLASS_NAME, 'left').text
    contest_date = row.find_element(By.XPATH, "//a[@target='_blank']").text
    contest_date = convert_to_time(contest_date)
    contest_end_time = contest_date + timedelta(hours=2)
    contests_list.append(Contest(contest_title, contest_date, contest_end_time))
    print(f'title: {contest_title} - date: {contest_date}')



driver.quit()