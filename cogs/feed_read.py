import feedparser as fp

def read_feed(user, shelf):
    RSS_URL = f'https://www.goodreads.com/review/list_rss/{user}?shelf={shelf}'
    feed = fp.parse(RSS_URL)
    return feed.entries
