// This code is mostly written with significant help and inspiration from Sergey Puzakov,
// thought he doesn't know it

// $(function() { ... });
// is just jQuery short-hand for
//
// $(document).ready(function() { ... });
// What it's designed to do (amongst other things) is ensure that your function is called once
// all the DOM elements of the page are ready to be used.

$(function() {
    var RSSReader = function() {
        // this.feedUrl = 'http://node.dev.puzankov.com/rss/data';
        this.feedUrl = 'http://127.0.0.1:5000/getfeed';
        this.arcticlesList = $('.articles');
        this.articleTmpl = $('.article-tmpl');
        this.init();
    };

    RSSReader.prototype.init = function() {
        this.getFeed('techradar');
    };

    RSSReader.prototype.renderFeed = function(dataList) {
        var _self = this,
            listHtml = [];
        dataList.forEach(function (item) {
            listHtml.push(_self.renderItem(item));
        });
    };

    RSSReader.prototype.onGetData = function(response) {
        this.renderFeed(response);
    };

    RSSReader.prototype.getFeed = function(feedId) {
        $.ajax({
            url: this.feedUrl,
            data: { rsource: feedId},
            method: 'GET',
            dataType: 'json'
        }).done(this.onGetData.bind(this)).fail(function(error) {
                console.log(error);
            });
    };

    RSSReader.prototype.renderItem = function(item) {
        var newItem = this.articleTmpl.clone().removeClass('article-tmpl');
        newItem.find('.post-heading').html(item.title);
        newItem.find('.excerpt').html(item.summary);
        newItem.find('.author').html(item.author);
        newItem.find('.date').html(moment().format(item.published));
        newItem.find('.action-button').attr('href', item.link);
        return newItem;
    };

    window.rssReader = new RSSReader();
});
