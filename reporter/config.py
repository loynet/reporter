import logging
import re
from configparser import ConfigParser


class Config:
    """
    The config class is used to parse the config file and provide the values to the rest of the program
    """

    def __init__(self, path: str):
        parser = ConfigParser()
        parser.read(path)

        self.user_agent = parser.get('general', 'user_agent')
        self.ib_url: str = parser.get('destination', 'url')
        self.ib_board: str = parser.get('destination', 'board')
        self.feed_url: str = parser.get('source', 'url')

        # Optional

        # Tick is used to determine how often the feed is checked and a thread is created
        self.tick = parser.getint('general', 'tick', fallback=60 * 60)  # 1 hour
        if self.tick < 1:
            raise ValueError('Tick must be greater than 0')

        # Random tick is used to provide a random offset to the tick
        self.tick_rand = parser.getint('general', 'tick_rand', fallback=60 * 30)  # 30 minutes
        if self.tick_rand < 0:
            raise ValueError('Tick randomization must be at least 0')

        # The maximum number of tries to get a good article to post
        self.max_tries: int = parser.getint('general', 'max_tries', fallback=10)
        if self.max_tries < 1:
            raise ValueError('Max tries must be greater than 0')

        # The maximum number of articles to keep in history
        self.max_history_size: int = parser.getint('general', 'max_history_size', fallback=10)
        if self.max_history_size < 1:
            raise ValueError('Max history size must be greater than 0')

        # The name of the poster
        self.poster_name: str = parser.get('destination', 'poster_name', fallback='')

        # The maximum length of the subject while creating a thread
        self.max_subject_len: int = parser.getint('destination', 'max_subject_len', fallback=50)
        if self.max_subject_len < 1:
            raise ValueError('Max subject length must be greater than 0')

        # The maximum length of the message while creating a thread
        self.max_message_len: int = parser.getint('destination', 'max_message_len', fallback=1000)
        if self.max_message_len < 1:
            raise ValueError('Max message length must be greater than 0')

        # The maximum number of files to upload while creating a thread
        self.max_files: int = parser.getint('destination', 'max_files', fallback=4)
        if self.max_files < 0:
            raise ValueError('Max files must be at least 0')

        # Non-configurable
        self.html_re = re.compile('<.*?>')

        logging.debug(f'Config: {self.__dict__}')
