import configparser
import hashlib
import logging
import sys
from datetime import datetime, timedelta
from random import randint
from threading import Thread, Event

import requests

import config
from provider.gnews import GNewsProvider
from provider.models import Article


class Reporter(Thread):
    """
    Reporter is responsible for publishing articles to the imageboard.
    """

    def __init__(self):
        super().__init__()
        self.daemon = True
        self.__stp = Event()

        self.provider = GNewsProvider(
            cfg.feed_url,
            user_agent=cfg.user_agent,
            max_history_size=cfg.max_history_size
        )

        self.start()

    @staticmethod
    def fetch_file(article: Article) -> tuple[str, bytes, str]:
        """
        Fetches the file from the article and returns a tuple of the filename, file content and the content type
        :param article: The article to fetch the file from
        :return: A tuple of the filename, file content and the content type
        """
        res = requests.get(article.image, hooks={'response': [lambda r, *args, **kwargs: r.raise_for_status()]},
                           headers={'Referer': article.url, 'User-Agent': cfg.user_agent}, )
        tp = res.headers['Content-Type']
        return f'{hashlib.sha256(res.content).hexdigest()}.{tp.split("/")[1]}', res.content, tp

    @staticmethod
    def create_thread(sub: str = "", msg: str = "", files: list[tuple[str, bytes, str]] = None) -> None:
        """
        Creates a thread on the imageboard.
        :param sub: Subject of the thread
        :param msg: The message of the thread
        :param files: The files to upload, a list of tuples of the filename, the file content and the content type
        (see fetch_file)
        :return: None
        """

        thread_form = (
            ('name', (None, cfg.poster_name)),
            ('subject', (None, sub if len(sub) <= cfg.max_subject_len else sub[:cfg.max_subject_len - 3] + '...')),
            ('message', (None, msg if len(msg) <= cfg.max_message_len else msg[:cfg.max_message_len - 3] + '...')),
        )

        for file in files[:cfg.max_files]:
            thread_form = (*thread_form, ('file', file))

        res = requests.post(
            url=f'{cfg.ib_url}/forms/board/{cfg.ib_board}/post',
            headers={'Referer': f'{cfg.ib_url}/{cfg.ib_board}/index.html', 'User-Agent': cfg.user_agent},
            hooks={'response': [lambda r, *args, **kwargs: r.raise_for_status()]},
            files=thread_form
        )
        if res != 200:
            raise Exception(f'Failed to create thread: {res}')

    def run(self) -> None:
        def random_interval():
            return cfg.tick + randint(0, cfg.tick_rand)

        interval = random_interval()
        logging.info(f'First article scheduled: {datetime.now() + timedelta(seconds=interval)}')
        while not self.__stp.wait(interval):
            try:
                # Get a new article
                a = self.provider.get_random_article()
                # Create a new thread
                self.create_thread(sub=a.title, msg=f'>{a.description}\n\n{a.url}', files=[self.fetch_file(a)])
            except Exception as e:
                logging.error(f'Exception while publishing, skipping article: {e}')
                pass

            logging.info("Successfully published article")
            # Schedule the next article
            interval = random_interval()
            logging.info(f'Next article scheduled: {datetime.now() + timedelta(seconds=interval)}')

    def stop(self) -> None:
        self.__stp.set()


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
