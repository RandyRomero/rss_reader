// This code is mostly written with significant help and inspiration from Sergey Puzakov,
// thought he doesn't know it

// $(function() { ... });
// is just jQuery short-hand for
//
// $(document).ready(function() { ... });
// What it's designed to do (amongst other things) is ensure that your function is called once
// all the DOM elements of the page are ready to be used.

$(function() {
    let RSSReader = function() {
        this.feedUrl = 'http://127.0.0.1:5000/get-feed';
        this.articlesList = $('.articles');
        this.articleTmpl = $('.article-tmpl');
        this.init();
    };

    RSSReader.prototype.checkUpdates = function() {
        // Recursively checking for more news
        setTimeout(() => {
            this.getNewsCount();
            this.checkUpdates();
        } , 30000);
    };


    RSSReader.prototype.init = function() {
        this.getFeed('all', 0);
        this.checkUpdates();
    };

    // Function that tracks if user at the and of a page. If so, it call function to render new news
    // and turn off the handler which activates this trackScroll function

    RSSReader.prototype.trackScroll = function() {
        let heightOfPage = document.documentElement.scrollHeight;
        let currentScroll = pageYOffset;
        let heightOfWindow = document.documentElement.clientHeight;
        console.log(`currentScroll: ${currentScroll}, heightOfWindow: ${heightOfWindow}, heightOfPage ${heightOfPage}`);
        console.log((currentScroll + heightOfWindow) >= (heightOfPage - 200));
        if ((currentScroll + heightOfWindow) >= (heightOfPage - 200)) {
            console.log('adding more news');
            console.dir(this);
            $(window).off('scroll', this.scrollListener);
            this.getFeed('all', 1);
        }
    };

    RSSReader.prototype.renderFeed = function(dataList) {
        let _self = this,
            listHtml = [];
        dataList.forEach(function (item) {
            listHtml.push(_self.renderItem(item));
        });

        this.articlesList.append(listHtml);
    };

    RSSReader.prototype.onGetData = function(response) {
        this.renderFeed(response);
    };

    RSSReader.prototype.getFeed = function(feedId, addNews) {
        // feedId - name of the resource to pick the right link to rss feed
        // addNews - if it is 1 - we ask server to send next portion of news that already were parsed by server
        // if it is 0 - we ask server to parse feed(s) again and send a new news feed
        console.log('Sending ajax-request to get more news...');
        console.log('adding news:', addNews);
        $.ajax({
            url: this.feedUrl,
            data: { rsource: feedId, addNews: addNews},
            method: 'GET',
            dataType: 'json'
        }).done((response) => {
            this.onGetData(response);
            this.scrollListener = this.trackScroll.bind(this);
            $(window).on('scroll', this.scrollListener);
            this.articlesList.addClass('articles-loaded');
        })
            .fail((error) => { console.log(error);});
    };

    RSSReader.prototype.renderItem = function(item) {
        let newItem = this.articleTmpl.clone().removeClass('article-tmpl');
        newItem.find('.post-heading').html(item.title);
        // newItem.find('.excerpt').html(item.summary);
        if (item['domain_name']) {
            newItem.find('.author').html(' by ' + item['domain_name']);
        }
        // Get time as a timestamp and convert it to relative string (like 4 minutes ago, 2 hours ago etc) via
        // moment.js library
        newItem.find('.date').html('Published ' + (moment.unix(item['published'])).fromNow());

        if (item['image']) {
            newItem.find('.pic').attr('src', item['image']);
        }

        newItem.find('.action-button').attr('href', item['link']);
        return newItem;
    };

    RSSReader.prototype.renderMoreNewsButton = function(newsCounter) {
        // show big button above news feed with counter how much news have appeared in rss feed since user updated the
        // page last time

        if (newsCounter < 1) {
            console.log('There are no new news.');
            return;
        }
        let freshNewsButton = $('.fresh-news-counter');
        freshNewsButton.removeClass('tmpl'); // make element visible

        let counter = $('.fresh-news-counter h2');
        counter.text('More news: ' + newsCounter);
    };

    RSSReader.prototype.getNewsCount = function() {
        // Make ajax-request to get quantity of news have appeared in rss feed since user updated the
        // page last time

        console.log('Sending ajax-request to get number of fresh news...');
        $.ajax({
            url: 'http://127.0.0.1:5000/fresh-news-counter',
            method: 'GET',
            dataType: 'json'
        }).done((response) => {
            console.log('We\'ve got the counter!');
            this.renderMoreNewsButton(response);
        }).fail((error) => { console.log(error); })
    };

    window.rssReader = new RSSReader();
});
