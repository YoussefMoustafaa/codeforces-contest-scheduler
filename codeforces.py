from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


service = Service(executable_path='chromedriver.exe')
driver = webdriver.Chrome(service=service)
driver.get('https://codeforces.com/contests')


driver.implicitly_wait(5)


def convert_to_time(str):

    input_format = "%b/%d/%Y %H:%M"

    dt = datetime.strptime(str, input_format)
    end_time = dt + timedelta(hours=2)

    global iso_format
    iso_format = "%Y-%m-%dT%H:%M:%S"

    start_time = dt.strftime(iso_format)
    end_time = end_time.strftime(iso_format)

    return start_time, end_time


# locate the table and rows
table = driver.find_element(By.CLASS_NAME, 'datatable')

rows = table.find_elements(By.TAG_NAME, 'tr')
rows.pop(0)   # Remove the header row


# a class to store contest details
class Contest:
    def __init__(self, title : str, start_time, end_time):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return f'{self.title} - {self.start_time}'



contests_list = []

for row in rows:
    contest_title = row.find_element(By.CLASS_NAME, 'left').text
    contest_date = row.find_element(By.XPATH, ".//a[@target='_blank']").text

    print(contest_title)
    print(contest_date)
    start_date, end_date = convert_to_time(contest_date)
    contest = Contest(contest_title, start_date, end_date)
    contests_list.append(contest)




SCOPES = ["https://www.googleapis.com/auth/calendar"]

creds = None

if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

try:
    service = build('calendar', 'v3', credentials=creds)

    for contest in contests_list:

        # the problem here is that when searching for events with the 'Z' time zone, it adds +3 hours for the time zone
        # and it skips the contest time, so we decrease the time for search by 3 hours to get the exact time
        start_utc = datetime.strptime(contest.start_time, iso_format)
        start_utc = start_utc - timedelta(hours=3)
        start_utc = start_utc.strftime(iso_format)

        event_result = (service.events().list(calendarId='primary',
                                              timeMin=start_utc + 'Z',
                                              maxResults=1,
                                              singleEvents=True,
                                              orderBy='startTime').execute())
        
        events = event_result.get('items', [])

        event_exists = False

        for event in events:
            if event['summary'] == contest.title and event['start'].get('dateTime', '').split('+')[0] == contest.start_time:
                event_exists = True
                print(f'Event {contest.title} - {contest.start_time} already exists.')
                break

        if not event_exists:
            event = {
                'summary': contest.title,
                'location': '',
                'description': '',
                'start': {
                    'dateTime': contest.start_time,
                    'timeZone': 'Africa/Cairo',
                },
                'end': {
                    'dateTime': contest.end_time,
                    'timeZone': 'Africa/Cairo',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }

            event = service.events().insert(calendarId='primary', body=event).execute()
            print(f'Event created: {event.get("htmlLink")}')

except HttpError as error:
    print(f'An error occurred: {error}')


driver.quit()