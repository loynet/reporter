import time
from random import randrange

import requests
from bs4 import BeautifulSoup
import feedparser
import logging

from .commons import History
from .models import OGArticle


class GNewsProvider:
    def __init__(self, url, user_agent=None, max_history_size=10):
        # Ensure that the URL is valid
        if not url.startswith('https://news.google.com/rss/topics/'):
            raise ValueError('URL must be a valid RSS Google News URL')

        self.url = url
        self.history = History(max_history_size)

        # Create a session, used mainly to avoid the consent page
        # TODO maybe this should be also used for the RSS feed
        self.__session = requests.Session()
        if user_agent:
            self.__session.headers.update({'User-Agent': user_agent})

    @staticmethod
    def __is_consent_page(s: BeautifulSoup) -> bool:
        return bool(s.find('form', action='https://consent.google.com/save'))

    def __handle_consent(self, s: BeautifulSoup) -> BeautifulSoup:
        form_data = {}
        # Get all consent forms
        forms = s.findAll('form', action='https://consent.google.com/save')
        for f in forms:  # Search for the one with the "Reject all" button
            if f.findAll('button', attrs={'aria-label': 'Reject all'}):
                # Extract the form data
                for i in f.findAll('input'):
                    form_data[i['name']] = i['value']
                break

        if not form_data:
            raise Exception('Unable to find the appropriate consent form')

        # Submit the form
        res = self.__session.post(url='https://consent.google.com/save', data=form_data)
        if res.status_code != 200:
            raise Exception(f'Unable to submit form: {res.status_code}')

        return BeautifulSoup(res.text, 'html.parser')

    @staticmethod
    def __is_redirect_page(s: BeautifulSoup) -> bool:
        # TODO this is not completely fool proof
        return bool(s.find('c-wiz'))

    def __handle_redirect(self, s: BeautifulSoup) -> BeautifulSoup:
        # Extract the redirect URL
        url = s.findAll('a')
        if not url:
            raise Exception('Unable to find redirect URL')

        # Follow the redirect
        res = self.__session.get(url[0]['href'])
        if res.status_code != 200:
            raise Exception(f'Unable to follow redirect: {res.status_code}')

        return BeautifulSoup(res.text, 'html.parser')

    def get_random_article(self, max_tries=3) -> OGArticle:
        articles = feedparser.parse(self.url)['entries']
        for i in range(min(max_tries, len(articles))):
            # Pick a random article
            logging.info(f'Trying to pick random article {i + 1}/{max_tries}')
            try:
                article = self.get_article(articles[randrange(len(articles))]['link'])
                # TODO there's an opportunity for optimization here, we could check if the article is
                #  in the history before getting it
                if self.history.has(article.title):
                    logging.info('Article already seen, trying again')
                    continue
            except Exception as e:
                logging.info(f'Failed to get article: {e}')
                time.sleep(3)
                continue

            self.history.add(article.title)
            return article

        raise Exception('Unable to get article')

    def get_article(self, url) -> OGArticle:
        if not url.startswith('https://news.google.com/rss/articles/'):
            raise ValueError('URL must be a valid RSS Google News URL')

        res = self.__session.get(url)
        if res.status_code != 200:
            raise Exception(f'Unable to get article: {res.status_code}')

        soup = BeautifulSoup(res.text, 'html.parser')
        if self.__is_consent_page(soup):
            logging.info('Consent form found, rejecting cookies')
            soup = self.__handle_consent(soup)

        if self.__is_redirect_page(soup):
            logging.info('Redirect page found, following redirect manually')
            soup = self.__handle_redirect(soup)

        return OGArticle.from_html(str(soup))
