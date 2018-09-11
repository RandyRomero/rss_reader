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
import re
from pprint import pprint

# will be changed when I add database with users, because we need to track this time for every user
last_time_user_gets_his_news = None


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


# Get link to image from html string with nested tags
def get_img_source(htmlstr):
    soup = bs(htmlstr, 'lxml')
    image = soup.find('img')
    return image.get('src', None) if image else None


# Converting time from strings to timestamp
def get_timestamp(date):
    try:
        date_temp = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
        return date_temp.timestamp()
    except ValueError:
        # Converting time from iso format (like this 2018-08-02T13:32:37-04:00) to timestamp
        d = dateutil.parser.parse(date)
        d = d.replace(tzinfo=pytz.utc) - d.utcoffset()  # lead up given time to UTC 00:00
        return d.timestamp()  # save as timestamp


def parse_rss(link, mode):

    """
    Function that takes one link to the rss feed and picks up specific data from it, saves each news as a dictionary,
    push these dictionaries to the list
    :param link: link to rss feed
    :return: list with dictionaries
    """

    one_feed = []
    news_counter = 0
    print('Parsing feed: ', link)
    rss = feedparser.parse(link)  # Get file from internet, open it with xml-parser

    for entry in rss.entries:
        # print('news_counter:', news_counter)
        if mode == 'count':
            if get_timestamp(entry.published) < last_time_user_gets_his_news:
                return news_counter
            else:
                news_counter += 1
                continue

        post = {'title': entry.title,
                'published': get_timestamp(entry.published)}

        # Try to get link to image from one of a place where it can be
        try:
            pic = entry.enclosures[0].href
        except (IndexError, AttributeError):
            pic = get_img_source(entry.summary)

        post['image'] = pic if pic else url_for('static', filename="400x400.jpg")

        link = entry.link
        post['link'] = link
        domain_name = re.search(r'://(.+?)/', link).group(1)
        post['domain_name'] = domain_name if domain_name else 'unknown'

        one_feed.append(post)

    return one_feed


def make_big_feed():
    """ Construct feed with all news from all rss-feeds sorted by time of publishing, but return only N news at once """
    mixed_feed = []

    # Put all news together in one list
    for link in rss_links.values():
        mixed_feed.extend(parse_rss(link, 'get_news'))

    # Sort news posts by time of publishing
    new_mixed_feed = sorted(mixed_feed, reverse=True, key=lambda k: k['published'])

    # Return only some part of news at once
    for x in range(0, len(new_mixed_feed), app.config['NEWS_TO_RETURN_AT_ONCE']):
        print('news counter', x)
        yield new_mixed_feed[x:x+app.config['NEWS_TO_RETURN_AT_ONCE']]


def get_big_feed():
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


get_big_feed_closure = get_big_feed()


@app.route('/')
@app.route('/index')
def start():
    return render_template('index.html')


# Function that figures out which rss feed to return, gets it from another function, convert to json and returns
@app.route('/get-feed')
def start_parse_rss():
    global last_time_user_gets_his_news
    global get_big_feed_closure
    # get argument from request where coded what rss_feed page asks from server
    rss_source = str(request.args.get('rsource'))
    add_news = int(request.args.get('addNews'))
    print('add news:', add_news)
    print('rss_source:', rss_source)

    # If you need to return all rss feeds in one
    if rss_source == 'all':
        if add_news:
            print('adding news')
            return get_big_feed_closure()
        else:
            print('making new feed')
            # Resetting closure to get refreshed feed
            get_big_feed_closure = get_big_feed()
            last_time_user_gets_his_news = datetime.timestamp(datetime.now())
            return get_big_feed_closure()
    # if you need to return posts only from one particular source
    feed = parse_rss(rss_links[rss_source], 'get_news')
    return json.dumps(feed, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)


@app.route('/fresh-news-counter')
def get_news_counter():
    """Launch parsing of rss feeds to count number of news that have
    appeared since last time server returned news to this user"""
    counter = 0
    for link in rss_links.values():
        news_number = parse_rss(link, 'count')
        try:
            counter += news_number
        except TypeError:
            print(news_number)

    return str(counter)

