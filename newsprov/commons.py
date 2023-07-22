import logging


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
