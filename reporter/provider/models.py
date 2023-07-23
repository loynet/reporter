from bs4 import BeautifulSoup


class Article:
    """
    A class representing an article with a title, a URL, a description and an image URL.
    """

    def __init__(self, title: str, url: str, description: str, image: str):
        self.title: str = title
        self.url: str = url
        self.description: str = description
        self.image = image

    def __str__(self):
        return f'TITLE={self.title}\nURL={self.url})\nDESCRIPTION={self.description}\nIMAGE_URL={self.image}'

    @classmethod
    def from_html(cls, r: str) -> 'Article':
        """
        Create an Article from an HTML string, the HTML must contain the Open Graph meta tags
        :param r: The HTML string
        :return: An Article
        """
        soup = BeautifulSoup(r, 'html.parser')
        if soup.find('meta', property='og:type')['content'] != 'article':
            raise ValueError('og:type must be article')

        # Garantees that the article has the required tags, returning a ValueError otherwise
        title = soup.find('meta', property='og:title')
        if not title:
            raise ValueError('og:title not found')
        url = soup.find('meta', property='og:url')
        if not url:
            raise ValueError('og:url not found')
        description = soup.find('meta', property='og:description')
        if not description:
            raise ValueError('og:description not found')
        image = soup.find('meta', property='og:image')
        if not image:
            raise ValueError('og:image not found')

        return cls(
            title=title['content'],
            url=url['content'],
            description=description['content'],
            image=image['content']
        )
