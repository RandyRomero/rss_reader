#!python3
# -*- coding: utf-8 -*-
# some kind of backend which takes ajax-request, reads certain rss feeds and return specific information from
# them as json with list of posts

import json
import feedparser
from flask import request, render_template, url_for
from app import app
import datetime as dt
import dateutil.parser  # pip install python-dateutil // to convert date from iso to datetime object
import pytz
from bs4 import BeautifulSoup as bs
import re

# will be changed when I add database with users, because we need to track this time for every user
last_time_user_gets_his_news = dt.datetime.timestamp(dt.datetime.now())


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
        date_temp = dt.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
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
    :param mode: what to do - parse all feeds to the end or parse only news that appeared since last returning of
    a feed to client or just count new news
    :return: list with dictionaries
    """

    one_feed = []
    news_counter = 0
    app.logger.info(f'Parsing feed: {link}')
    rss = feedparser.parse(link)  # Get file from internet, open it with xml-parser

    for entry in rss.entries:
        if mode == 'count':
            if get_timestamp(entry.published) < last_time_user_gets_his_news:
                return news_counter
            else:
                news_counter += 1
                continue

        if mode == 'latest':
            news_item_date = get_timestamp(entry.published)

            # Stop reading RSS if current news is already older than time when user last got the news feed
            if news_item_date < last_time_user_gets_his_news:
                return one_feed

        post = {'title': entry.title,
                'published': get_timestamp(entry.published)}

        # Try to get link to image from one of a place where it can be
        try:
            pic = entry.enclosures[0].href
        except(IndexError, AttributeError):
            pic = get_img_source(entry.summary)

        post['image'] = pic if pic else url_for('static', filename="400x400.jpg")

        link = entry.link
        post['link'] = link
        domain_name = re.search(r'://(.+?)/', link).group(1)
        post['domain_name'] = domain_name if domain_name else 'unknown'

        one_feed.append(post)

    if mode != 'latest':
        return one_feed
    else:
        print('There are no new news at all.')
        return []


def make_news_feed(mode):
    """
    :return: list of news sorted by date of publishing
    """
    mixed_feed = []

    # Put all news together in one list
    for link in rss_links.values():
        mixed_feed.extend(parse_rss(link, mode))

    # Sort news posts by time of publishing
    return sorted(mixed_feed, reverse=True, key=lambda k: k['published'])


def get_feed_generator():
    new_mixed_feed = make_news_feed('parse_all')
    # Return only some part of news at once
    for x in range(0, len(new_mixed_feed), app.config['NEWS_TO_RETURN_AT_ONCE']):
        app.logger.debug(f'There are {x+app.config["NEWS_TO_RETURN_AT_ONCE"]} news on the page now')
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
            big_feed_gen = get_feed_generator()
            return json.dumps(next(big_feed_gen), indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
    return nested_return_feed


get_big_feed_closure = get_big_feed()


@app.route('/')
@app.route('/index')
def start():
    return render_template('index.html')


# Function that figures out which rss feed to return, gets it from another function, convert to json and returns
@app.route('/get-feed')
def get_all_news():
    global last_time_user_gets_his_news
    global get_big_feed_closure
    # get argument from request where coded what rss_feed page asks from server
    rss_source = str(request.args.get('rsource'))
    add_news = request.args.get('addNews')

    # If you need to return all rss feeds in one
    if rss_source == 'all':
        app.logger.debug(f'add news: {add_news}')
        if add_news == 'add old news':
            app.logger.debug('adding news')
            return get_big_feed_closure()
        elif add_news == 'refresh news':
            app.logger.debug('making new feed')
            # Resetting closure to get refreshed feed
            get_big_feed_closure = get_big_feed()
            last_time_user_gets_his_news = dt.datetime.timestamp(dt.datetime.now())
            return get_big_feed_closure()
    # if you need to return posts only from one particular source
    feed = parse_rss(rss_links[rss_source], 'get_news')
    return json.dumps(feed, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)


@app.route('/get-latest-news')
def get_latest_news():
    """
    :return: list of news that have appeared since user get news last time
    """
    global last_time_user_gets_his_news
    latest_news = make_news_feed('latest')
    last_time_user_gets_his_news = dt.datetime.timestamp(dt.datetime.now())
    return json.dumps(latest_news, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
