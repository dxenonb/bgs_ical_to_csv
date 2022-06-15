import datetime
from datetime import timedelta
from pathlib import Path
import csv
import os
import sys
import json

events_path = 'events.csv'
preface_path = 'preface.txt'

message_paths = [
    'in_person.json',
    'virtual.json',
    'future.json',
]

ical_limit = datetime.date.today() + timedelta(weeks=8)

default_preface = ''
# for the moment, going to maintain this message manually in Discord.
# default_preface = '''
# Our current event schedule is a Game Dev Meetup/Showcase, every two weeks, alternating in person and virtual.
# '''.strip()

# Ommitting from message for now:
# **__*Upcoming Events*__**
# {preface}

virtual_message_format = '''
**__*Upcoming Virtual Events*__**

{virtual_events}

Links for joining will be posted near the time of the event. Keep a lookout in  #general!
'''.strip()

in_person_message_format = '''
***__Upcoming In-Person Events__***

{in_person_events}

:people_holding_hands: Vaccination is required to attend any in person event unless otherwise stated.
'''.strip()

future_message_format = '''
***__Future Events__***

{future_events}
{after_note}
RSVP on meetup!
<https://www.meetup.com/BuffaloGameSpace/>

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
    'arcade': 'joystick',
    'project': 'tools',
    'workshop': 'book',
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
        self.virtual = location is None or location == 'Online event'
        self.future = False
    def line_item_args(self):
        # default to just sending the strings through
        # remove any `:` in case the caller already included them, e.g. ":kind:"
        emoji_string = self.kind.replace(':', '')
        # attempt to lookup an emoji for event kind, else let `kind` fall through as the emoji
        emoji_string = emoji.get(self.kind, self.kind)
        if self.future or self.virtual:
            # do not include the after line for future events (Meetup doesnt report location accurately)
            # do not include the after line for virtual events (because we dont want to)
            location_string = None
        else:
            location_string = location_map.get(self.location, self.location)
            if location_string is not None and location_string != '' and emoji['location'] not in location_string:
                location_string = f":{emoji['location']}: {location_string}"
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
    result = []
    for item in items:
        if '\n' in item:
            # add extra space after multi line items
            result.append(item + '\n')
        else:
            result.append(item)
    # join the contents, but remove the trailing line (won't format correctly on discord)
    result = '\n'.join(result).strip()

    # move each item into a discord quote
    return result.replace('\n', '\n> ')

def format_calendar(preface, in_person, virtual, future):
    after_note = ''

    virtual_events = line_items(line_item(*i) for i in virtual).strip()
    in_person_events = line_items(line_item(*i) for i in in_person).strip()
    future_events = line_items(line_item(*i) for i in future).strip()

    v = virtual_message_format.format(
        preface=preface, 
        virtual_events=virtual_events, 
    )
    ip = in_person_message_format.format(
        in_person_events=in_person_events, 
    )
    f = future_message_format.format(
        future_events=future_events,
        after_note=after_note
    )
    return v, ip, f

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

def detect_repeats(events):
    """
        There appears to be a bug in Meetup's ICS file (ugh) - only the next instance of a repeated event shows its location.
        So, we group all repeated events as "future".
    """
    instances = {}
    for event in events:
        instances[event.title] = 1 + instances.setdefault(event.title, 0)
    for event in events:
        if not event.location and instances[event.title] > 1:
            event.future = True

def main():
    try:
        preface = Path(preface_path).read_text()
    except IOError:
        preface = default_preface
    
    automated_run = False
    contents = try_read_stdin()
    if contents is None:
        with open(events_path, newline='') as file:
            events = parse_events(file)
    else:
        automated_run = True
        events = parse_events(contents)
    
    # keep only a certain window of events
    events = [i for i in events if i.date <= ical_limit]
    
    detect_repeats(events)
    
    events.sort(key=lambda e: e.date)

    virtual = (i.line_item_args() for i in events if i.virtual and not i.future)
    in_person = (i.line_item_args() for i in events if not i.virtual and not i.future)
    future = (i.line_item_args() for i in events if i.future)

    message_parts = format_calendar(preface, in_person, virtual, future)

    if automated_run:
        for file_path, message in zip(message_paths, message_parts):
            Path(file_path).write_text(json.dumps({
                'content': message
            }))
        output_files = ', '.join(message_paths)
        print(f'Messages written to {output_files}')
    else:
        message = '\n\n'.join(message_parts)
        print('== REVIEW & COPY INTO DISCORD: ==')
        print(message)
        print('== END ==')
    

if __name__ == '__main__':
    main()
