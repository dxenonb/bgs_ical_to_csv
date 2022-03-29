from ics import Calendar
import csv
import requests

url = "https://www.meetup.com/BuffaloGameSpace/events/ical/"
r = requests.get(url)
#cal = Calendar.from_ical(r.content)
cal = Calendar(r.text)

with open('cal_parsed.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_ALL)
    writer.writerow(
        [
            'kind',
            'name',
            'date',
            'repeat_count',
            'days_between',
            'start_time',
            'end_time',
            'location'
        ]
    )
    for event in cal.events:
        if event.status == "CONFIRMED":
            writer.writerow(
                [
                    "kind", 
                    event.name, 
                    event.begin.date(), 
                    "1", 
                    "1", 
                    event.begin.time().strftime("%-I:%M%p"),
                    event.end.time().strftime("%-I:%M%p"), 
                    event.location
                ]
            )




