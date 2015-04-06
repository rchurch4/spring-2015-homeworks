#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import requests
from BeautifulSoup import BeautifulSoup


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
loghandler = logging.StreamHandler(sys.stderr)
loghandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(loghandler)

base_url = "http://www.tripadvisor.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"



def get_city_page(city, state, datadir):
    """ Returns the URL of the list of the hotels in a city. Corresponds to
    STEP 1 & 2 of the slides.

    Parameters
    ----------
    city : str

    state : str

    datadir : str


    Returns
    -------
    url : str
        The relative link to the website with the hotels list.

    """
    # Build the request URL
    url = base_url + "city=" + city + "&state=" + state
    # Request the HTML page
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    with open(os.path.join(datadir, city + '-tourism-page.html'), "w") as h:
        h.write(html)

    # Use BeautifulSoup to extract the url for the list of hotels in
    # the city and state we are interested in.

    # For example in this case we need to get the following href
    # <li class="hotels twoLines">
    # <a href="/Hotels-g60745-Boston_Massachusetts-Hotels.html" data-trk="hotels_nav">...</a>
    soup = BeautifulSoup(html)
    li = soup.find("li", {"class": "hotels twoLines"})
    city_url = li.find('a', href=True)
    return city_url['href']


def get_hotellist_page(city_url, page_count, city, datadir='data/'):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.

    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.
    city : str
        The name of the city that we are interested in.
    datadir : str, default is 'data/'
        The directory in which to save the downloaded html.

    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """
    url = base_url + city_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    # Save the webpage
    with open(os.path.join(datadir, city + '-hotelist-' + str(page_count) + '.html'), "w") as h:
        h.write(html)
    return html

def get_hotel_info_page(hotel_name, page_url, datadir='data/'):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.

    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.
    city : str
        The name of the city that we are interested in.
    datadir : str, default is 'data/'
        The directory in which to save the downloaded html.

    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """
    url = base_url + page_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    hotel_name = hotel_name.replace(' ', '-').replace('/','').strip()
    # Save the webpage
    with open(os.path.join(datadir, hotel_name + '.html'), "w") as h:
        h.write(html)
    return html

def get_hotel_info(html):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.

    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.

    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """

    soup = BeautifulSoup(html)
    # Extract hotel name, star rating and number of reviews
    hotel_box = soup.find('form', id='REVIEW_FILTER_FORM').find('div', 'content wrap trip_type_layout')
    if not hotel_box:
        log.info("couldn't find extra info")
        sys.exit(0)

    new_info = []
    traveler_rating = hotel_box.find('div', 'col2of2 composite')
    ratings = traveler_rating.findAll('div', 'wrap row')
    for r in ratings:
        count = float(r.find('span', 'compositeCount').find(text = True).replace(',', ''))

        new_info.append(count)

    trip_type = hotel_box.find('div', 'trip_type')
    types = trip_type.findAll('div', 'value')
    for t in types:
        count = float(t.find(text=True).replace(',', ''))
        new_info.append(count)

    summary_box = hotel_box.find('div', id = 'SUMMARYBOX')
    summaries = summary_box.findAll('span', 'rate sprite-rating_s rating_s')
    for s in summaries:
        img = s.find('img')['alt']
        img = float(img[:img.index(' ')])
        new_info.append(img)

    return new_info

def parse_hotellist_page(html):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.

    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.

    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """

    new_hotels = []
    soup = BeautifulSoup(html)
    # Extract hotel name, star rating and number of reviews
    hotel_boxes = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'})
    if not hotel_boxes:
        log.info("#################################### Option 2 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing_info jfy'})
    if not hotel_boxes:
        log.info("#################################### Option 3 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing easyClear  p13n_imperfect'})

    for hotel_box in hotel_boxes:
        hotel_name_url = hotel_box.find("a", {"target" : "_blank"})
        hotel_name = hotel_name_url.find(text=True).strip()
        hotel_url = hotel_name_url['href'].strip()
        log.info("Hotel name: %s" % hotel_name.strip())

        stars = hotel_box.find("img", {"class" : "sprite-ratings"})
        if stars:
            stars = float(stars['alt'].split()[0])
            log.info("Stars: %s" % stars)

        num_reviews = hotel_box.find("span", {'class': "more"}).findAll(text=True)
        if num_reviews:
            num_reviews = float([x for x in num_reviews if "review" in x][0].strip().split()[0].replace(',', ''))
            log.info("Number of reviews: %s " % num_reviews)

        log.info("Hotel url: %s" % hotel_url)


        newest_hotel = [hotel_name, hotel_url, stars, num_reviews]
        new_hotels.append(newest_hotel)

    # Get next URL page if exists, otherwise exit
    div = soup.find("div", {"class" : "pgLinks"})
    # check if this is the last page
    if div.find('span', {'class' : 'guiArw pageEndNext'}):
        log.info("We reached last page")
        return (None, new_hotels)
    else:
        # If not, return the url to the next page
        hrefs = div.findAll('a',{'class':'guiArw sprite-pageNext '}, href= True)
        #print hrefs
        # for href in hrefs:
        #     if 'guiArw sprite-pageNext ' in href:
        #         print 'Found'
        log.info("Next url is %s" % hrefs[0]['href'])
        return (hrefs[0]['href'], new_hotels)


def scrape_hotels(city, state, datadir='data/'):
    """Runs the main scraper code

    Parameters
    ----------
    city : str
        The name of the city for which to scrape hotels.

    state : str
        The state in which the city is located.

    datadir : str, default is 'data/'
        The directory under which to save the downloaded html.
    """

    # Get current directory
    current_dir = os.getcwd()
    # Create datadir if does not exist
    if not os.path.exists(os.path.join(current_dir, datadir)):
        os.makedirs(os.path.join(current_dir, datadir))

    # Get URL to obtaint the list of hotels in a specific city
    city_url = get_city_page(city, state, datadir)
    c = 0

    hotels = []
    while(True):
        c += 1
        html = get_hotellist_page(city_url, c, city, datadir)
        (new_url, new_hotels) = parse_hotellist_page(html)
        city_url = new_url
        hotels += new_hotels
        if city_url == None:
            break

    for h in hotels:
        html = get_hotel_info_page(h[0], h[1], datadir)
        h += get_hotel_info(html)

    return hotels


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape tripadvisor')
    parser.add_argument('-datadir', type=str,
                        help='Directory to store raw html files',
                        default="data/")
    parser.add_argument('-state', type=str,
                        help='State for which the hotel data is required.',
                        required=True)
    parser.add_argument('-city', type=str,
                        help='City for which the hotel data is required.',
                        required=True)

    args = parser.parse_args()
    hotels = scrape_hotels(args.city, args.state, args.datadir)
