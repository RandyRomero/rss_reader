// This code is mostly written with significant help and inspiration by Sergey Puzakov,
// thought he doesn't know it

// ready - to make function that updates the timestamp on every news on a page once in a minute
// todo refresh the whole news feed instead of adding new news if there are more
// than app.config["NEWS_TO_RETURN_AT_ONCE"] new news
// todo (in progress) put counter of new news in a title every time there are some news


// $(function() { ... });
// is just jQuery short-hand for $(document).ready(function() { ... });
// What it's designed to do (amongst other things) is ensure that your function is called once
// all the DOM elements of the page are ready to be used.

$(function() {
    let RSSReader = function() {
        this.feedUrl = 'http://127.0.0.1:5000/get-feed';
        this.articlesList = $('.articles');
        this.articleTmpl = $('.article-tmpl');
        this.freshNewsButton = $('.fresh-news-counter');
        this.pageTitle = $(document).find('title');
        this.pageTitleOriginalText = this.pageTitle.text();
        this.feedID = 'all'; // feedId - name of the resource to pick the right link to rss feed
        this.newsCounterText = this.freshNewsButton.find('h2');
        this.loadingAnimationTimeout = null; // there will be save setTimeout id
        this.articlesList.on('click', this.freshNewsButton, this.manageRenderingLatestNews.bind(this));
        this.init();
    };

    RSSReader.prototype.checkUpdates = function() {
        /**
         * Recursively checking for more news
         */
        setTimeout(() => {
            this.updatePublishingTime();
            this.getNewsCounter();
            this.checkUpdates();
        } , 60000);
    };

    RSSReader.prototype.init = function() {
        /* Things to do right after initialization */
        this.getFeed('refresh news');
    };

    RSSReader.prototype.trackScroll = function() {
        /*
            It tracks whether user at the end of a page. If so, it calls function to render new news
            and turn off the handler which activates this trackScroll function
         */

        let heightOfPage = document.documentElement.scrollHeight;
        let currentScroll = pageYOffset;
        let heightOfWindow = document.documentElement.clientHeight;
        // console.log(`currentScroll: ${currentScroll}, heightOfWindow: ${heightOfWindow}, heightOfPage ${heightOfPage}`);
        // console.log((currentScroll + heightOfWindow) >= (heightOfPage - 200));
        if ((currentScroll + heightOfWindow) >= (heightOfPage - 200)) {
            console.log('adding more news as reached and of the page');

            // The .off() method removes event handlers that were attached with .on().
            $(window).off('scroll', this.scrollListener);
            this.getFeed('add old news');
        }
    };

    RSSReader.prototype.renderFeed = function(dataList, mode) {
        /*
        For every item in a given list it calls function to render the item with html template

         @param {array} dataList - list of items where each item is an object with key-value pairs that
         comprises one news
         @param {str} note - how to add news on a page - before already rendered news or after
         @return none
         */
        let _self = this,
            listHtml = [];
        dataList.forEach(function (item) {
            listHtml.push(_self.renderItem(item));
        });

        if (mode === 'append') {
            console.log('Rendering the whole page (or add older news as user scrolls down the page)');
            this.articlesList.append(listHtml);
        }
        else if (mode === 'prepend') {
            console.log('Just adding the latest news above old ones');
            this.articlesList.prepend(listHtml);
        }
    };


    RSSReader.prototype.getFeed = function(addNews) {
        /*
        @param {str} feedId - name of the resource to pick the right link to rss feed
        @param {str} addNews - mode of adding news: refresh all page or just add old news after already
         rendered news (infinite feed)
        */

        if (addNews === 'refresh news') {
            console.log('Sending ajax-request to parse all rss feeds and get a new news feed...');
        }
        else if (addNews === 'add old news') {
            console.log('Sending ajax-request to get next portion of news as user scrolls the page...')
        }
        $.ajax({
            url: this.feedUrl,
            data: { rsource: this.feedID, addNews: addNews},
            method: 'GET',
            dataType: 'json'
        }).done((response) => {
            this.renderFeed(response, 'append');
            this.scrollListener = this.trackScroll.bind(this);
            $(window).on('scroll', this.scrollListener);
            this.articlesList.addClass('articles-loaded');
            this.checkUpdates();
        })
            .fail((error) => { console.log(error);});
    };

    RSSReader.prototype.renderItem = function(item) {
        /*
        Fills in HTML-template with data from server - one news. Specifically with a heading of that news,
        with name of a source, author name, date of publishing, link to image and link to website where that
        news was published
        @param {object} item - object that comprise one news and contains data of publishing and all that stuff
        to be rendered as one news item on a page
        return {str} newItem - string which is html-code ready to be added on a page
         */

        let newItem = this.articleTmpl.clone().removeClass('article-tmpl');
        newItem.find('.post-heading').html(item.title);

        if (item['domain_name']) {
            newItem.find('.author').html(' by ' + item['domain_name']);
        }
        // Get time as a timestamp and convert it to relative string (like 4 minutes ago, 2 hours ago etc) via
        // moment.js library
        newItem.find('.date').html('Published ' + (moment.unix(item['published'])).fromNow());

        // save timestamp to get access to it later when page will be rerendering how long ago news where published
        newItem.find('.date').attr('published', item['published']);
        if (item['image']) {
            newItem.find('.pic').attr('src', item['image']);
        }

        newItem.find('.action-button').attr('href', item['link']);
        // newItem.attr('published', item['published']);
        // console.log(newItem.data());
        return newItem;
    };

    RSSReader.prototype.updateNewsTimer = function() {
        /*
        Sends server request to update the date when user pushed the button to render the latest news on his page.
        It is necessary to make server understand what news are new and what news have been already seen by user

         */
        console.log('Connecting to the server to update date when user got his news last time');
        $.ajax({
            url: 'http://127.0.0.1:5000/update-news-timer',
            method: 'POST'
        }).done(() => {
            console.log('Successfully updated date when user got news last time.')
        }).fail((error) => {
            console.log('Server was unable to update date when user got his news last time because of the' +
                'following error: ');
            console.log(error);
        })
    };


    RSSReader.prototype.animateLoadingNewsButton = function () {
        // Function that renders message on a button like "Loading...." with increasing number of dots
        // to show to the user that new news is going to be shown soon

        let _self = this;
        let loadingText = 'Loading';
        let dots = '';

        function animate() {
            // Change text in the button (which activates loading of news form server) for "Loading.." with changing
            // number of dots and recursively calls itself every 500 milliseconds to keep
            _self.newsCounterText.text(loadingText + dots);
            dots += '.';
            if (dots.length > 3) {
                dots = '';
                _self.loadingAnimationTimeout = setTimeout(animate, 500);
                return;
            }
            loadingText = 'Loading';
            _self.loadingAnimationTimeout = setTimeout(animate, 500);
        }
        animate();
    };

    RSSReader.prototype.rerenderNews = function() {
        // erases the whole news section on a webpage and renders latest news anew

        console.log('Wait for news to be downloaded from the server...');
        this.animateLoadingNewsButton();

        $.ajax({
            url: this.feedUrl,
            data: {rsource: this.feedID, addNews: 'refresh news'},
            method: 'GET',
            dataType: 'json'
        }).done((response) => {
            clearTimeout(this.loadingAnimationTimeout);
            $('.articles-loaded').html(''); // clearing out previous news
            this.renderFeed(response, 'append');
            this.freshNewsButton.addClass('tmpl');
            this.pageTitle.text(this.pageTitleOriginalText)

        }).fail((error) => { console.log(error);});
    };

    RSSReader.prototype.renderLatestNews = function() {
        /*
        Gets from server list of news that have appeared since user got news last time
        In case ajax request was successive the function calls render function to add the latest news to the page
        and hides button that activates this function
         */

        this.freshNewsButton.addClass('tmpl');
        console.log('Hiding fresh news button');
        this.updateNewsTimer();
        this.renderFeed(this.freshNews, 'prepend');
        this.updatePublishingTime();
        this.pageTitle.text(this.pageTitleOriginalText)
    };

    RSSReader.prototype.renderMoreNewsButton = function(newsCounter) {
        /*
        shows big button above news feed with the counter how much news have appeared in rss feed since user updated the
        page last time
        @param {integer} newsCounter - number of fresh news. This integer will be shown on button above news
         */

        // Show number of new news in the title of the page
        this.pageTitle.text(`${this.pageTitleOriginalText} (${newsCounter})`);

        if (this.freshNewsButton.hasClass('tmpl')) {
            this.freshNewsButton.removeClass('tmpl'); // make element visible
            this.newsCounterText.text('More news: ' + newsCounter);
            this.articlesList.prepend(this.freshNewsButton); // move button upon news feed
            return;
        }

        this.newsCounterText.text('More news: ' + newsCounter);
    };

    RSSReader.prototype.manageRenderingLatestNews = function() {
        // Decides whether to add the latest news in the beginning (if there are few of them), or erase the whole
        // news section on a webpage and render latest news anew

        if (this.freshNews.length >= 20) {
            this.rerenderNews();
            return;
        }
        this.renderLatestNews();
    };


    RSSReader.prototype.getNewsCounter = function() {
        /*
          Make ajax-request to get new news if there some
        */

        console.log('Sending ajax-request for the latest news.');
        $.ajax({
            url: 'http://127.0.0.1:5000/get-latest-news',
            method: 'GET',
            dataType: 'json'
        }).done((response) => {
            if (response.length < 1) {
                console.log('There are no new news.');
                return;
            }

            console.log('We\'ve got latest news!');
            this.renderMoreNewsButton(response.length);
            this.freshNews = response;

        }).fail((error) => { console.log(error); })
    };

    RSSReader.prototype.updatePublishingTime = function() {
        /*
        Updates published time of every news on the page. Time of publishing renders not as a date in the past, but
        how many time passed since this time in the past. That's why we need to update it regularly. And that function
        does it.
         */
        $('.article').each(function() {
            $(this).find('.date').text('Published ' + moment.unix(+($(this).find('.date').attr('published'))).fromNow());
        });
        console.log('Done updating time of publishing.');
    };

    window.rssReader = new RSSReader();
});
