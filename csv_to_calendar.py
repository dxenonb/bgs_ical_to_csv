import datetime
from datetime import timedelta
from pathlib import Path
import csv
import os
import sys
import json

ical_limit = datetime.date.today() + timedelta(weeks=8)

default_preface = ''
# for the moment, going to maintain this message manually in Discord.
# default_preface = '''
# Our current event schedule is a Game Dev Meetup/Showcase, every two weeks, alternating in person and virtual.
# '''.strip()

# Ommitting from message for now:
# **__*Upcoming Events*__**
# {preface}

calendar_message_format = '''
**__*Upcoming Virtual Events*__**
{virtual_events}
Links for joining will be posted near the time of the event. Keep a lookout in  #general!
***__Upcoming In-Person Events__***
{in_person_events}
:people_holding_hands: Vaccination is required to attend any in person event unless otherwise stated.
{after_note}
RSVP on meetup!
https://www.meetup.com/BuffaloGameSpace/
'''.strip()

events_csv_header = [
    'kind',
    'name',
    'date',
    'repeat_count',
    'days_between',
    'start_time',
    'end_time',
    'location'
]

# shorten/change some locations
location_map = {
    'Buffalo Game Space (2495 Main Street, Suite #454, Buffalo, NY 14214)': 'BGS, 2495 Main St., Suite #454'
}

emoji = {
    'kind': 'calendar_spiral',
    'showcase': 'night_with_stars',
    'location': 'pushpin',
    'jam': 'video_game',
    'workshop': 'tools',
    'santa': 'santa'
}

class Event:
    def __init__(self, kind, title, date, start_time, end_time, location=None):
        self.kind = kind
        self.title = title
        self.date = date if isinstance(date, datetime.date) else datetime.date(*date)
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.virtual = location is None
    def line_item_args(self):
        # default to just sending the strings through
        emoji_string = emoji.get(self.kind, f':{self.kind}:')
        location_string = location_map.get(self.location, self.location)
        return (emoji_string, self.title, self.date, self.start_time, self.end_time, location_string)

def ordinal_date(date):
    d = date.day
    # https://stackoverflow.com/a/5891598
    # CC BY-SA 3.0: https://creativecommons.org/licenses/by-sa/3.0/
    return str(d) + ('th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th'))

def line_item(emoji, title, date, start_time, end_time, after_line=None):
    date_string = date.strftime("%A, %B {S}").replace('{S}', ordinal_date(date))
    main = f':{emoji}: **{title}** • {date_string} • {start_time} - {end_time}'
    return main if after_line is None else f'{main}\n*{after_line}*'

def line_items(items):
    return '\n'.join('> {}'.format(i.replace('\n', '\n> ')) for i in items)

def format_calendar(preface, in_person, virtual):
    after_note = ''

    virtual_events = line_items(line_item(*i) for i in virtual).strip()
    in_person_events = line_items(line_item(*i) for i in in_person).strip()

    return calendar_message_format.format(
        preface=preface, 
        virtual_events=virtual_events, 
        in_person_events=in_person_events, 
        after_note=after_note
    )

def try_read_stdin():
    if not os.isatty(sys.stdin.fileno()):
        return sys.stdin.readlines()
    else:
        return None

def parse_events(lines):
    events = []
    reader = csv.DictReader(lines)
    for row in reader:
        year, month, day = map(int, row['date'].strip().split('-'))
        date = datetime.date(year, month, day)
        repeat_count = int(row['repeat_count']) if row['repeat_count'] is not None else 1
        days_between = int(row['days_between']) if repeat_count != 1 else 0
        location = row['location'].strip() or None
        for i in range(0, repeat_count):
            event = Event(row['kind'], row['name'], date, row['start_time'], row['end_time'], location)
            events.append(event)
            date = date + timedelta(days=days_between)
    return events

def main():
    try:
        preface = Path('preface.txt').read_text()
    except IOError:
        preface = default_preface
    
    automated_run = False
    contents = try_read_stdin()
    if contents is None:
        with open('events.csv', newline='') as file:
            events = parse_events(file)
    else:
        automated_run = True
        events = parse_events(contents)
        # keep only a certain window of events
        events = [i for i in events if i.date <= ical_limit]
                
    # now unused:
    # tri_main = f":{emoji['location']}: Buffalo Game Space @ Tri Main Center, 2495 Main Street, Suite #454"
    # showcase = 'Game Dev Meetup / Showcase'
    # first_showcase = datetime.date(2021, 10, 7)
    
    events.sort(key=lambda e: e.date)

    virtual = (i.line_item_args() for i in events if i.virtual)
    in_person = (i.line_item_args() for i in events if not i.virtual)

    message = format_calendar(preface, in_person, virtual)

    if automated_run:
        print(json.dumps({
            'content': message
        }))
    else:
        print('== REVIEW & COPY INTO DISCORD: ==')
        print(message)
        print('== END ==')
    

if __name__ == '__main__':
    main()
