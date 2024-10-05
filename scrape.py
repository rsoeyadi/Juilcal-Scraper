import os
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
from supabase import create_client, Client
import shutil
import hashlib

# Load environment variables
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
email: str = os.environ.get("USERNAME")
password: str = os.environ.get("PASSWORD")
supabase: Client = create_client(url, key)

def signupToDb():  # only need this if user account needs to be recreated for some reason
    res = supabase.auth.sign_up({
        "email": email,
        "password": password,
    })

class Event:
    def __init__(self, title, dateTime, venue, link, tags, dayOfWeek):
        self.title = title
        self.date_time = dateTime
        self.venue = venue
        self.link = link
        self.tags = tags
        self.dayOfWeek = dayOfWeek

def signInToDb():
    supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

def getHtml(link):
    r = requests.get(link)
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def get_day_of_week(date_str):
    date_obj = datetime.fromisoformat(date_str)
    return date_obj.strftime('%A')  # Get the full weekday name

def generate_id(title, dateTime):
    composite_key = f"{title}_{dateTime}"
    return hashlib.md5(composite_key.encode()).hexdigest()

def create_tables():
    # SQL command to create the Events table
    create_events_table = """
    CREATE TABLE IF NOT EXISTS Events (
        id TEXT PRIMARY KEY,
        title TEXT,
        dateTime TEXT,
        venue TEXT,
        link TEXT,
        tags TEXT,
        dayOfWeek TEXT
    );
    """

    # SQL command to create the Last Updated table
    create_last_updated_table = """
    CREATE TABLE IF NOT EXISTS "Last Updated" (
        id SERIAL PRIMARY KEY,
        lastUpdated TIMESTAMP
    );
    """

    # Execute the SQL commands
    supabase.rpc('sql', {"query": create_events_table})
    supabase.rpc('sql', {"query": create_last_updated_table})

def main():
    signInToDb()
    create_tables()  # Create tables if they don't exist

    # Delete all rows from tables before inserting new data
    supabase.table('Events').delete().neq('id', 9999999999).execute()
    supabase.table('Last Updated').delete().neq('id', 9999999999).execute()

    nextButtonExists = True
    linkSuffix = ""
    while nextButtonExists:  # Begin scraping!
        soup = getHtml('https://www.juilliard.edu/stage-beyond/performance/calendar?start_date_from=09/01/23&start_date_thru=&' + linkSuffix)
        eventsGroup = soup.find('ul', {'class': 'event-groups'})  # These are all the events
        for eventGroup in eventsGroup.find_all('li', {'class': 'event-group'}):  # Events are grouped together by date
            for event in eventGroup.find('ul', {'class': 'event-group-events'}).find_all('li'):
                eventClasses = event.get('class')
                if 'event-cta' in eventClasses:
                    continue  # It's a CTA, skip!

                title_div = event.find('div', {'class': 'title-subtitle'})
                title = title_div.find('span').text if title_div and title_div.find('span') else None
                link = "https://juilliard.edu" + title_div.find('a')['href'].split('?')[0] if title_div and title_div.find('a') else None
                venue_div = event.find('div', {'class': 'field--name-field-venue'})
                venue = venue_div.text if venue_div else None
                tags_div = event.find('div', {'class': 'field--name-field-event-tags'})
                tags = ','.join([html.get_text() for html in tags_div.find_all('div', {'class': 'field__item'})]) if tags_div else None
                time_element = event.find('time')
                dateTime = time_element['datetime'] if time_element else None
                dayOfWeek = get_day_of_week(dateTime) if dateTime else None

                res = Event(title, dateTime, venue, link, tags, dayOfWeek)
                event_id = generate_id(title, dateTime)
                data = supabase.table('Events').insert({
                    "id": event_id,
                    "title": res.title,
                    "dateTime": res.date_time,
                    "venue": res.venue,
                    "link": res.link,
                    "tags": res.tags,
                    "dayOfWeek": res.dayOfWeek
                }).execute()

                print(data)

        loadMoreButton = soup.find('a', {'title': 'Load more results'})
        if loadMoreButton:
            print("\n Loading more events...")
            linkSuffix = loadMoreButton['href']
        else:
            nextButtonExists = False
            formattedDatetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            supabase.table('Last Updated').insert({"lastUpdated": formattedDatetime}).execute()

main()
