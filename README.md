# Reporter

Yet another ptchina news bot that fetches news from a provider and posts a snippet of it on a configurable board of a
configurable [jschan](https://gitgud.io/fatchan/jschan) imageboard.

Posts usually contain the title, the description, and an image of the article.

The posts are not authenticated (it doesn't require or support posting through an account)
but can include a name and/or a tripcode.

Currently, it only supports a Google News RSS feed as a provider.

## Getting Started

1. (Optional) Create and activate a virtual environment
2. Run `pip install -r requirements.txt` to install the dependencies
3. Tweak the `example.ini` file or create a new one following the template
4. Run `python reporter/main.py <config-file>.ini` to start the bot