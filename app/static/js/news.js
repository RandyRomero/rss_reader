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
        // this.feedUrl = 'http://node.dev.puzankov.com/rss/data';
        this.feedUrl = 'http://127.0.0.1:5000/getfeed';
        this.arcticlesList = $('.articles');
        this.articleTmpl = $('.article-tmpl');
        this.init();
    };

    RSSReader.prototype.init = function() {
        this.getFeed('all');
    };

    // Function that tracks if user at the and of a page. If so, it call function to render new news
    // and turn off the handler which activates this trackScroll function

    RSSReader.prototype.trackScroll = function(event) {
        let heightOfPage = document.documentElement.scrollHeight;
        let currentScroll = pageYOffset;
        let heightOfWindow = document.documentElement.clientHeight;
        console.log(`currentScroll: ${currentScroll}, heightOfWindow: ${heightOfWindow}, heightOfPage ${heightOfPage}`);
        console.log((currentScroll + heightOfWindow) >= (heightOfPage - 200));
        if ((currentScroll + heightOfWindow) >= (heightOfPage - 200)) {
            console.log('adding more news');
            console.dir(this);
            $(window).off('scroll', this.scrollListener);
            this.getFeed('all');
        }
    };

    RSSReader.prototype.renderFeed = function(dataList) {
        let _self = this,
            listHtml = [];
        dataList.forEach(function (item) {
            listHtml.push(_self.renderItem(item));
        });

        this.arcticlesList.append(listHtml);
    };

    RSSReader.prototype.onGetData = function(response) {
        this.renderFeed(response);
    };

    RSSReader.prototype.getFeed = function(feedId) {
        console.log('Sending ajax-request to get more news...');
        $.ajax({
            url: this.feedUrl,
            data: { rsource: feedId},
            method: 'GET',
            dataType: 'json'
        }).done((response) => {
            this.onGetData(response);
            this.scrollListener = this.trackScroll.bind(this);
            $(window).on('scroll', this.scrollListener);
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

    window.rssReader = new RSSReader();
});
