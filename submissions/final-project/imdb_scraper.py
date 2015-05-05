# imdb scraper

import os
import sys
import time
import logging
import requests
from BeautifulSoup import BeautifulSoup
import re

start_year = 2000
end_year = 2015
first_stage_complete = True
second_stage_complete = True
datadir = 'data/'
base_url = "http://www.imdb.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"
regex = re.compile('[^A-Za-z0-9\s]')
money_re = re.compile('[^0-9]')

# BEGIN YEAR PAGE SCRAPING
def get_year_page(year,index):
	url = base_url + 'search/title?sort=moviemeter,asc&start=' + str(index) + '&title_type=feature&year=' + str(year) + ',' + str(year)
	headers = {'User-Agent': user_agent}
	response = requests.get(url, headers=headers)
	html = response.text.encode('utf-8')
	return html

def parse_year_page(html):
	movie_urls = []
	last_index = 1
	soup = BeautifulSoup(html)
	table = soup.find('table', {'class':'results'})

	movies = table.findAll('tr', {'class':'even detailed'}) + table.findAll('tr', {'class':'odd detailed'})
	for m in movies:
		index = m.find('td', {'class':'number'}).find(text=True).strip('.')
		last_index = index
		title = m.find('td', {'class':'title'})
		link = title.find('a', href=True)['href']
		movie_urls.append(link)
	return movie_urls, last_index
# END YEAR PAGE SCRAPING

#BEGIN BUSINESS PAGE SCRAPING
def get_business_page(movie_id):
	url = base_url + 'title/' + movie_id + '/business?ref_=tt_dt_bus'
	headers = {'User-Agent': user_agent}
	response = requests.get(url, headers=headers)
	html = response.text.encode('utf-8')
	return html

#returns (budget, revenue)
def parse_business_page(movie_id):
	html = get_business_page(movie_id)
	soup = BeautifulSoup(html)
	content = soup.find('div', {'id':'tn15content'}).findAll(text=True)
	cleaned_content = []
	for i in content:
		if len(i) > 5 and len(i) < 50:
			cleaned_content.append(i.strip())
	if cleaned_content[0].lower() != 'budget':
		return 0,0
	else:
		raw_budget = cleaned_content[1].replace('&#163;','')
		budget = float(money_re.sub('', raw_budget))
		gross_found = False
		weekend_gross_found = False
		max_gross = 0
		for i in cleaned_content:
			if not gross_found:
				if i.lower() == 'opening weekend':
					gross_found = True
			elif not weekend_gross_found:
				if i.lower() == 'weekend_gross_found':
					weekend_gross_found = True
				else:
					if '&#163;' in i or '$' in i:
						cleaned_i = i.replace('&#163;','')
						idx = len(cleaned_i)
						try:
							idx = cleaned_i.index(' ')
						except:
							pass
						cleaned_i = cleaned_i[:idx]
						try:
							new_gross = float(money_re.sub('', cleaned_i))
						except ValueError:
							new_gross = 0
						if new_gross > max_gross:
							max_gross = new_gross
			else:
				pass
		return budget, max_gross
#END BUSINESS PAGE SCRAPING

#BEGIN CAST SCRAPING
def get_cast_page(movie_id):
	url = base_url + 'title/' + movie_id + '/fullcredits?ref_=tt_cl_sm'
	headers = {'User-Agent': user_agent}
	response = requests.get(url, headers=headers)
	html = response.text.encode('utf-8')
	return html

def parse_cast_page(movie_id):
	html = get_cast_page(movie_id)
	cast_list = []
	soup = BeautifulSoup(html)
	info = soup.find('div', {'id':'fullcredits_content'})
	not_actors = info.findAll('table', {'class':'simpleTable simpleCreditsTable'})
	not_actors = not_actors[:2]
	actors = info.find('table', {'class':'cast_list'})
	if actors == None:
		return []
	odd_actors = actors.findAll('tr', {'class': 'odd'})
	even_actors = actors.findAll('tr', {'class': 'even'})
	if odd_actors == None and even_actors:
		return []
	elif odd_actors == None:
		count = 0
		for t in even_actors:
			if count > 20:
				break
			name = regex.sub('', t.find('td', {'itemprop':'actor'}).find('span', {'itemprop':'name'}).find(text=True))
			cast_list.append(name)
	elif even_actors == None:
		count = 0
		for t in odd_actors:
			if count > 20:
				break
			name = regex.sub('', t.find('td', {'itemprop':'actor'}).find('span', {'itemprop':'name'}).find(text=True))
			cast_list.append(name)
	else:
		count = 0
		for t in odd_actors:
			if count > 10:
				break
			name = regex.sub('', t.find('td', {'itemprop':'actor'}).find('span', {'itemprop':'name'}).find(text=True))
			cast_list.append(name)
			count += 1
		count = 0
		for t in even_actors:
			if count > 10:
				break
			count += 1
			name = regex.sub('', t.find('td', {'itemprop':'actor'}).find('span', {'itemprop':'name'}).find(text=True))
			cast_list.append(name)
	for t in not_actors:
		name = regex.sub('', t.find('td', {'class':'name'}).find('a', href=True).find(text=True))
		cast_list.append(name)
	return cast_list
#END CAST SCRAPING

# BEGIN INDIVIDUAL MOVIE SCRAPING
def get_movie_page(movie_id):
	url = base_url + 'title/' + movie_id + '/'
	headers = {'User-Agent': user_agent}
	response = requests.get(url, headers=headers)
	html = response.text.encode('utf-8')
	return html

# movie format = [id, title, year, rating, budget, revenue, profit, [cast]]
def parse_movie_page(link):
	movie_id = link.replace('/title/', '').replace('/', '').strip()
	html = get_movie_page(movie_id)
	soup = BeautifulSoup(html)
	overview = soup.find('div', {'class':'article title-overview'})
	if overview != None:
		title_area = overview.find('h1', {'class':'header'})
		title = regex.sub('',title_area.find('span', {'itemprop':'name'}).find(text=True))
		year = regex.sub('',title_area.find('span', {'class':'nobr'}).find('a', href=True).find(text=True))

		rating_area = overview.find('div', {'class':'star-box giga-star'})
		rating = rating_area.find('div', {'class':'star-box-details'}).find('span', {'itemprop':'ratingValue'}).find(text=True)
		#hardcode url for cast and box office info
		budget, revenue = parse_business_page(movie_id)
		cast = parse_cast_page(movie_id)
		movie = (movie_id, title, year, rating, budget, revenue, revenue-budget, cast)
		return movie
	else:
		return None
# END INDIVIDUAL MOVIE SCRAPING

def parse_imdb(start_year, end_year, datadir, first_stage_complete, second_stage_complete):
	movie_urls = []
	movie_info = []
	if not first_stage_complete:
		for year in range (start_year,end_year):
			print year
			last_index = 1
			while last_index < 500:
				html = get_year_page(year, last_index)
				(m, i) = parse_year_page(html)
				movie_urls += m
				last_index = int(i) + 1
				time.sleep(1.5)

		with open(os.path.join(datadir, 'link_list.csv'), "w") as h:
			for u in movie_urls:
				h.write(u+'\n')
	if not second_stage_complete:
		if first_stage_complete:
			#get from data/
			with open(os.path.join(datadir, 'link_list.csv'), "r") as h:
				for u in h:
					movie_urls.append(u)
		
		with open(os.path.join(datadir, 'movie_info2.csv'), "w") as h:
			count = 0
			for u in movie_urls:
				count += 1
				if count % 300 == 0:
					print count
				next_movie = parse_movie_page(u)
				time.sleep(1.5)
				movie_info.append(next_movie)
				for i in range(0,len(next_movie)):
					if i == len(next_movie):
						cast_list = next_movie[i]
						for j in range(0,len(cast_list)):
							if j == len(cast_list):
								h.write(next_movie[i])
							else:
								h.write(str(next_movie[i])+',')
					else:
						h.write(str(next_movie[i])+',')
				h.write('\n')
	else:
		with open(os.path.join(datadir, 'movie_info2.csv'), "r") as h:
			for u in h:
				next_movie = []
				cast_list = []
				movie_stuff = u.split(',')
				for i in range(0,len(movie_stuff)):
					if i < 7:
						next_movie.append(movie_stuff[i])
					else:
						name = movie_stuff[i].replace('u\'', '').replace('\'','').replace('[','').replace(']','').replace('\\n','').lstrip().rstrip()
						cast_list.append(name)
				cast_list = set(cast_list)
				cast_list = list(cast_list)
				next_movie.append(cast_list)
				if float(next_movie[4]) < 10**9 and float(next_movie[4]) > 0 and not float(next_movie[3]) == 0 and not float(next_movie[5]) == 0:
					movie_info.append(next_movie)
				else:
					pass #print next_movie
	return movie_info

#parse_business_page('tt0280590')
#parse_imdb(start_year, end_year, datadir, first_stage_complete, second_stage_complete)