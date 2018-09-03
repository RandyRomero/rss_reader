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
from pprint import pprint

NEWS_TO_RETURN_AT_ONCE = 20

rss_links = {'ferra-articles': 'https://www.ferra.ru/export/articles-rss.xml',
             'ferra-news': 'https://www.ferra.ru/export/news-rss.xml',
             'techradar': 'https://www.techradar.com/rss',
             'verge': 'https://www.theverge.com/rss/index.xml',
             'ubkreview': 'https://www.ultrabookreview.com/feed/',
             'bi': 'https://www.businessinsider.com/sai/rss?IR=T',
             'tproger': 'https://tproger.ru/feed/',
             '3dnews-hard': 'https://3dnews.ru/news/rss/',
             'techspot': 'https://www.techspot.com/backend.xml'}

# TODO Auto-update

# TODO Parse all rss feeds simultaneously one post by one and yield only amount that fits in page, than parse and
# yield next N posts when user scroll the page


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


def make_big_feed():
    """ Construct feed with all news from all rss-feeds sorted by time of publishing, but return only N news at once """
    mixed_feed = []

    # Put all news together in one list
    for link in rss_links.values():
        mixed_feed.extend(parse_rss(link))

    # Sort news posts by time of publishing
    new_mixed_feed = sorted(mixed_feed, reverse=True, key=lambda k: k['published'])

    # Return only some part of news at once
    for x in range(0, len(new_mixed_feed), NEWS_TO_RETURN_AT_ONCE):
        print('news counter', x)
        yield new_mixed_feed[x:x+NEWS_TO_RETURN_AT_ONCE]


def return_feed():
    """ Closure in order to make a list with all news sorted, but to return to client only by several items at once """

    # A list of news items. We need to preserve it in order to create it once during the first call, and to
    # return these items from this already existing list
    big_feed_gen = None

    def nested_return_feed():
        nonlocal big_feed_gen
        if big_feed_gen:
            try:
                return json.dumps(next(big_feed_gen), indent=4, sort_keys=True, separators=(',', ': '),
                                  ensure_ascii=False)
            except StopIteration:
                return '', 204
        else:
            big_feed_gen = make_big_feed()
            return json.dumps(next(big_feed_gen), indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
    return nested_return_feed


return_feed_closure = return_feed()


@app.route('/')
@app.route('/index')
def start():
    return render_template('index.html')


# Function that figures out which rss feed to return, gets it from another function, convert to json and returns
@app.route('/getfeed')
def start_parse_rss():

    # get argument from request where coded what rss_feed page asks from server
    rss_source = request.args.get('rsource')

    # If you need to return all rss feeds in one
    if rss_source == 'all':
        return return_feed_closure()

    # if you need to return posts only from one particular source
    feed = parse_rss(rss_links[rss_source])
    return json.dumps(feed, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)


