from ics import Calendar
import csv
import requests
import platform

url = "https://www.meetup.com/BuffaloGameSpace/events/ical/"
r = requests.get(url)
#cal = Calendar.from_ical(r.content)
cal = Calendar(r.text)

event_kinds = {
    'Jam' : 'jam',
    'BGS Project Night' : 'project',
    'BGS Game Development' : 'showcase',
    'Workshop' : 'workshop',
    'Arcade' : 'arcade'
}

time_format = "%-I:%M%p"
if platform.system() == 'Windows':
    # windows doesn't support `-`
    time_format = "%I:%M%p"

with open('cal_parsed.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',' )
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
        kind = "kind"
        if event.status == "CONFIRMED":
            for key in event_kinds.keys():
                if event.name.__contains__(key):
                    kind = event_kinds[key]
            writer.writerow(
                [
                    kind, 
                    event.name, 
                    event.begin.date(), 
                    "1", 
                    "1", 
                    event.begin.time().strftime(time_format),
                    event.end.time().strftime(time_format), 
                    event.location
                ]
            )




