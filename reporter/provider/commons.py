import logging


class History:
    """
    Keep track of the number of times that a key has been seen in a size-limited history. The history is kept in a FIFO
    manner, so the oldest entry is removed when the history is full.
    """

    def __init__(self, max_size: int):
        if max_size < 1:
            raise ValueError('Max size must be greater than 0')
        self.max_size: int = max_size

        # Keep track of the number of times a title has been seen
        self.history: dict[str, int] = {}
        # Keep track of the order of the entries in the history to remove in a FIFO manner
        self.__queue: list[str] = []

    def add(self, key: str) -> None:
        """
        Add a new entry to the history. If the entry is already present, increment the counter.
        :param key: The key to add to the history
        :return: None
        """
        if key in self.history:
            self.history[key] += 1
            return

        logging.debug(f'Added new entry to history')
        self.history[key] = 1
        self.__queue.append(key)

        # Remove the oldest entry if the history is full
        if len(self.history) > self.max_size:
            logging.debug(f'Removed oldest entry from history')
            del self.history[self.__queue.pop(0)]

    def has(self, key: str) -> bool:
        """
        Check if a key is in the history.
        :param key: The key to check
        :return: True if the key is in the history, False otherwise
        """
        logging.debug(f'Checking if {key} is in history')
        return key in self.history
