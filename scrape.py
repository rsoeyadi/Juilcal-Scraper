import os
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
from supabase import create_client, Client
import shutil

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
email: str = os.environ.get("USERNAME")
password: str = os.environ.get("PASSWORD")
supabase: Client = create_client(url, key)

class Event:
    def __init__(self, title, dateTime, venue, link, tags, imgLink, dayOfWeek):
        self.title = title
        self.date_time = dateTime
        self.venue = venue
        self.link = link
        self.tags = tags
        self.imgLink = imgLink
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

def saveImage(id, url):
    headers ={
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    res = requests.get(url,headers=headers)
    with open("../client/public/img/" + str(id) + '.jpg', 'wb') as f:
        f.write(res.content)

def get_day_of_week(date_str):
    date_obj = datetime.fromisoformat(date_str)
    return date_obj.strftime('%A')  # Get the full weekday name

def main():
    if os.path.exists("../client/public/img"):
        shutil.rmtree('../client/public/img') # clear this out!
    os.makedirs("../client/public/img")
    signInToDb()
    # delete everything first
    supabase.table('Events').delete().neq('id', 9999999999).execute() 
    supabase.table('Last Updated').delete().neq('id', 9999999999).execute() 

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
                dayOfWeek = get_day_of_week(dateTime) if dateTime else None

                imgSoup = getHtml(link)
                imgLinkHtml = imgSoup.find('div', { 'class' : 'event-hero-banner__image' }).find('picture').find('img')
                if imgLinkHtml:
                    imgLink = "https://juilliard.edu" + imgLinkHtml['src']
                else: 
                    imgLink = None

                res = Event(title, dateTime, venue, link, tags, imgLink, dayOfWeek)
                data, count = supabase.table('Events').insert({"title": res.title, "dateTime": res.date_time, "venue" : res.venue, "link" : res.link, "tags" : res.tags, "imgLink" : res.imgLink, "dayOfWeek": res.dayOfWeek }).execute()
                id = data[1][0]['id'] # for naming the images uniquely
                saveImage(id, imgLink)
                print(data)

        loadMoreButton = soup.find('a', {'title' : 'Load more results'})
        if loadMoreButton:
            linkSuffix = loadMoreButton['href']
        else:
            nextButtonExists = False
            formattedDatetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            supabase.table('Last Updated').insert({"lastUpdated": formattedDatetime}).execute()

main()
