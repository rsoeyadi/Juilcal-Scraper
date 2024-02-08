import os
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
email: str = os.environ.get("USERNAME")
password: str = os.environ.get("PASSWORD")
supabase: Client = create_client(url, key)

class Event:
    def __init__(self, title, dateTime, venue, link, tags):
        self.title = title
        self.date_time = dateTime
        self.venue = venue
        self.link = link
        self.tags = tags

# def signupToDb(): # only need this if user account needs to be recreated for some reason
#     supabase: Client = create_client(url, key)
#     res = supabase.auth.sign_up({
#     "email": email,
#     "password": password,
#     })

def signInToDb():
    supabase.auth.sign_in_with_password({
        "email": email, 
        "password": password
    })

def connectToDb():
    signInToDb()
    return supabase

def getHtml(link):
    r = requests.get(link)
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def main():
    supabase = connectToDb()
    # delete everything first
    supabase.table('Events').delete().neq('id', 9999999).execute() 
    supabase.table('Last Updated').delete().neq('id', 9999999).execute() 

    nextButtonExists = True
    linkSuffix = ""
    while nextButtonExists: # begin scraping!
        soup = getHtml('https://www.juilliard.edu/stage-beyond/performance/calendar?start_date_from=09/01/23&start_date_thru=&' + linkSuffix)
        eventsGroup = soup.find('ul', {'class' : 'event-groups'}) # these are all the events
        for eventGroup in eventsGroup.find_all('li', { 'class' : 'event-group'}): # events are grouped together by date
            for event in eventGroup.find('ul', { 'class' : 'event-group-events'}).find_all('li'):
                eventClasses = event.get('class')
                if 'event-cta' in eventClasses: continue # it's a cta, skip!
                title_div = event.find('div', {'class': 'title-subtitle'})
                if title_div and title_div.find('span'):
                    title = title_div.find('span').text
                else:
                    title = None  

                if title_div and title_div.find('a'):
                    link = "https://juilliard.edu" + title_div.find('a')['href'].split('?')[0]
                else:
                    link = None  

                venue_div = event.find('div', {'class': 'field--name-field-venue'})
                venue = venue_div.text if venue_div else None  

                tags_div = event.find('div', {'class': 'field--name-field-event-tags'})
                tags = []
                if tags_div:
                    tagsHtml = tags_div.find_all('div', {'class': 'field__item'})
                    for html in tagsHtml:
                        tags.append(html.get_text())
                tags = ','.join(tags)  # Serializing the tags as a single string value

                time_element = event.find('time')
                dateTime = time_element['datetime'] if time_element else None 

                res = Event(title, dateTime, venue, link, tags)
                data, count = supabase.table('Events').insert({"title": res.title, "dateTime": res.date_time, "venue" : res.venue, "link" : res.link, "tags" : res.tags}).execute()
                print(data)

        loadMoreButton = soup.find('a', {'title' : 'Load more results'})
        if loadMoreButton:
            linkSuffix = loadMoreButton['href']
        else:
            nextButtonExists = False
            formattedDatetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            supabase.table('Last Updated').insert({"lastUpdated": formattedDatetime}).execute()

main()