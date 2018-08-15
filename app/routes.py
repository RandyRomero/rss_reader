#!python3
# -*- coding: utf-8 -*-
# some kind of backend which takes ajax-request, reads certains rss feeds and return specific information from
# them as json with list of posts

import json
import feedparser
from flask import request, render_template, url_for
from app import app
from datetime import datetime
import dateutil.parser  # pip install python-dateutil // is needed to convert date from iso to datetime object
import pytz
from bs4 import BeautifulSoup as bs

rss_links = {'ferra-articles': 'https://www.ferra.ru/export/articles-rss.xml',
             'ferra-news': 'https://www.ferra.ru/export/news-rss.xml',
             'techradar': 'https://www.techradar.com/rss',
             'verge': 'https://www.theverge.com/rss/index.xml',
             'ubkreview': 'https://www.ultrabookreview.com/feed/',
             'bi': 'https://www.businessinsider.com/sai/rss?IR=T',
             'tproger': 'https://tproger.ru/feed/',
             '3dnews-hard': 'https://3dnews.ru/news/rss/',
             'techspot': 'https://www.techspot.com/backend.xml'}


# Get link to image from html string with nested tags
def get_img_source(htmlstr):
    soup = bs(htmlstr, 'lxml')
    image = soup.find('img')
    return image.get('src', None) if image else None


# Converting time from strings to timestamp
def get_timestamp(date):
    try:
        date_temp = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
        print(date)
        print(date_temp)
        return date_temp.timestamp()
    except ValueError:
        # Converting time from iso format (like this 2018-08-02T13:32:37-04:00) to timestamp
        d = dateutil.parser.parse(date)
        d = d.replace(tzinfo=pytz.utc) - d.utcoffset()  # lead up given time to UTC 00:00
        print(d)
        return d.timestamp()  # save as timestamp


def parse_rss(link):

    one_feed = []

    # add some visual highlight
    print(5 * '\n')
    line = '*'
    for i in range(10):
        print(line)
        line = ' ' + line
    print('RSS FEED: ', link)
    for i in range(10):
        line = line[1:]
        print(line)

    rss = feedparser.parse(link)  # Get file from internet, open it with xml-parser

    for entry in rss.entries:
        post = {}
        print('Title: ', entry.title)
        post['title'] = entry.title

        post['published'] = get_timestamp(entry.published)

        author = entry.get('author', None)
        if author:
            print('Author: ', author)
        post['author'] = author

        # Try to get link to image from one of the place where it can be
        try:
            pic = entry.enclosures[0].href
        except IndexError:
            pic = get_img_source(entry.summary)
        post['image'] = pic if pic else url_for('static', filename="400x400.jpg")
        print(post['image'])

        post['link'] = entry.link

        print('\nNext item\n')
        one_feed.append(post)

    return one_feed


@app.route('/')
@app.route('/index')
def start():
    return render_template('index.html')


# Function that figures out which rss feed to return, gets it from another function, convert to json and returns
@app.route('/getfeed')
def start_parse_rss():

    rss_source = request.args.get('rsource')

    # If you need to return all rss feeds in one
    if rss_source == 'all':
        mixed_feed = []
        for link in rss_links.values():
            mixed_feed.extend(parse_rss(link))
        new_mixed_feed = sorted(mixed_feed, reverse=True, key=lambda k: k['published'])
        return json.dumps(new_mixed_feed, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)

    # if you need to return posts only of one feed
    feed = parse_rss(rss_links[rss_source])
    return json.dumps(feed, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)


