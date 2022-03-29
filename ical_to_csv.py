from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime
import os
import pytz
import requests


url = "https://www.meetup.com/BuffaloGameSpace/events/ical/"

r = requests.get(url)

cal = Calendar.from_ical(r.content)

print(cal)
