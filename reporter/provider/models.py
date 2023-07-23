from bs4 import BeautifulSoup


class OGArticle:
    def __init__(self, title: str, url: str, description: str, image: str):
        self.title: str = title
        self.url: str = url
        self.description: str = description
        self.image = image

    def __str__(self):
        return f'TITLE={self.title}\nURL={self.url})\nDESCRIPTION={self.description}\nIMAGE_URL={self.image}'

    @classmethod
    def from_html(cls, r: str) -> 'OGArticle':
        """
        Create an Article from an HTML string, the HTML must contain the Open Graph meta tags-
        :param r: The HTML string
        :return: An Article
        """
        soup = BeautifulSoup(r, 'html.parser')
        if soup.find('meta', property='og:type')['content'] != 'article':
            raise ValueError('og:type must be article')

        return cls(
            title=soup.find('meta', property='og:title')['content'],
            url=soup.find('meta', property='og:url')['content'],
            description=soup.find('meta', property='og:description')['content'],
            image=soup.find('meta', property='og:image')['content']
        )
