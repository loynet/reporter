import time
from random import randrange

import requests
from bs4 import BeautifulSoup
import feedparser
import logging

from .commons import History
from .models import Article


class GNewsProvider:
    """
    A provider for Google News RSS feeds with support for consent page and redirects. It keeps track of the last N
    articles returned to avoid returning the same articles multiple times.
    """

    def __init__(self, url: str, user_agent: str = "", max_history_size: int = 10):
        # Ensure that the URL is valid
        if not url.startswith('https://news.google.com/rss/topics/'):
            raise ValueError('URL must be a valid RSS Google News URL')

        self.url = url
        self.history = History(max_history_size)

        # Create a session, used mainly to avoid the consent page
        self.__session = requests.Session()
        if user_agent != "":
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

    def get_random_article(self, max_tries: int = 3) -> Article:
        """
        Get a random article from the feed. It will try at most max_tries times to get an article that has not been
        returned before.
        :param max_tries: The maximum number of tries
        :return: The article
        """
        articles = feedparser.parse(self.url)['entries']
        for i in range(min(max_tries, len(articles))):
            # Pick a random article
            logging.info(f'Trying to pick random article {i + 1}/{max_tries}')
            try:
                # We use the url as a unique identifier for the article, which is probably better than using the title
                url = articles[randrange(len(articles))]['link']
                if self.history.has(url):  # Filter duplicates
                    logging.info('Article already seen, trying again')
                    continue
                article = self.get_article(url)
            except Exception as e:
                logging.info(f'Failed to get article: {e}')
                time.sleep(3)
                continue

            self.history.add(article.url)
            return article

        raise Exception('Unable to get article')

    def get_article(self, url: str) -> Article:
        """
        Get an article from the feed. This method will not check if the article has been returned before.
        :param url: The URL of the article
        :return: The article
        """
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

        return Article.from_html(str(soup))
