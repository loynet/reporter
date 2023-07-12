# This is a sample Python script.
import configparser
import hashlib
import logging
import re
import sys
from datetime import datetime, timedelta
from random import randrange, randint
from threading import Thread, Event

import feedparser
import requests as requests

import config


class Article:
    def __init__(self, title: str, link: str, summary: str, media: list[str]):
        self.title: str = title
        self.link: str = link
        self.summary: str = summary
        self.media: list[str] = media

    @classmethod
    def from_raw(cls, raw: dict) -> 'Article':
        media = [r['url'] for r in raw['media_content'] if r['url'].endswith('.jpg') or r['url'].endswith('.png')]
        return cls(title=raw['title'], link=raw['link'], summary=re.sub(cfg.html_re, '', raw['summary']), media=media)

    def __str__(self) -> str:
        return f'{self.title} ({self.link})\n{self.summary}\n {self.media}'


class History:
    def __init__(self, max_size: int):
        if max_size < 1:
            raise ValueError('Max size must be greater than 0')
        self.max_size: int = max_size

        # Keep track of the number of times a title has been seen
        self.history: dict[str, int] = {}
        # Keep track of the order of the entries in the history to remove in a FIFO manner
        self.__queue: list[str] = []

    def add(self, title: str) -> None:
        if title in self.history:
            self.history[title] += 1
            return

        logging.debug(f'Added new entry to history')
        self.history[title] = 1
        self.__queue.append(title)

        # Remove the oldest entry if the history is full
        if len(self.history) > self.max_size:
            logging.debug(f'Removed oldest entry from history')
            del self.history[self.__queue.pop(0)]

    def has(self, title: str) -> bool:
        logging.debug(f'Checking if {title} is in history')
        return title in self.history


class Reporter(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._stop = Event()
        self.history = History(cfg.max_history_size)
        self.start()

    def get_article(self) -> Article:
        articles = feedparser.parse(cfg.feed_url)['entries']
        for i in range(min(cfg.max_tries, len(articles))):
            # Pick a random article
            logging.debug(f'Trying to pick random article {i + 1}/{cfg.max_tries}')
            article = Article.from_raw(articles[randrange(len(articles))])
            # Check if the article has already been posted or if it has no media
            if self.history.has(article.title):
                continue
            return article

        # If we can't find a new article after max_tries tries, raise an exception
        raise Exception('Unable to find a good article')

    @staticmethod
    def get_files(article) -> list[tuple[str, bytes, str]]:
        def fetch_file(url) -> tuple[str, bytes, str]:
            res = requests.get(url, hooks={'response': [lambda r, *args, **kwargs: r.raise_for_status()]},
                               headers={'Referer': article.link, 'User-Agent': cfg.user_agent}, )
            tp = res.headers['Content-Type']
            return f'{hashlib.sha256(res.content).hexdigest()}.{tp.split("/")[1]}', res.content, tp

        return [fetch_file(f) for f in article.media]

    @staticmethod
    def create_thread(sub='', msg='', files=None):
        thread_form = (
            ('name', (None, cfg.poster_name)),
            ('subject', (None, sub if len(sub) <= cfg.max_subject_len else sub[:cfg.max_subject_len - 3] + '...')),
            ('message', (None, msg if len(msg) <= cfg.max_message_len else msg[:cfg.max_message_len - 3] + '...')),
        )

        for file in files[:cfg.max_files]:
            thread_form = (*thread_form, ('file', file))

        requests.post(
            url=f'{cfg.ib_url}/forms/board/{cfg.ib_board}/post',
            headers={'Referer': f'{cfg.ib_url}/{cfg.ib_board}/index.html', 'User-Agent': cfg.user_agent},
            hooks={'response': [lambda r, *args, **kwargs: r.raise_for_status()]},
            files=thread_form
        )

    def run(self) -> None:
        def random_interval():
            return cfg.tick + randint(0, cfg.tick_rand)

        interval = random_interval()
        logging.info(f'First article scheduled: {datetime.now() + timedelta(seconds=interval)}')
        while not self._stop.wait(interval):
            try:
                # Get a new article
                a = self.get_article()
                # Create a new thread
                self.create_thread(sub=a.title, msg=f'>{a.summary}\n\n{a.link}', files=self.get_files(a))
                # Add the article to the history
                self.history.add(a.title)
                # Schedule the next article
                interval = random_interval()
            except Exception as e:
                logging.error(f'Exception while publishing, skipping article: {e}')
                pass

            logging.info(f'Next article scheduled: {datetime.now() + timedelta(seconds=interval)}')

    def stop(self):
        self._stop.set()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s %(funcName)s] %(message)s (%(name)s)')

    if len(sys.argv) < 2:
        print(f'Usage: reporter.py <config_file>')
        sys.exit(1)

    try:
        cfg = config.Config(sys.argv[1])
    except configparser.Error as e:
        logging.error(f'Exception while parsing config file, exiting: {e}')
        sys.exit(1)

    Reporter().join()
