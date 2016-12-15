from google.appengine.api import urlfetch
import urllib
import urllib2
import json

class RedditPost:
  def __init__(self,name, post_url, link_url):
    self.name = name
    self.post_url = post_url
    self.link_url = link_url
     

def get_posts(subreddits,sort='top',limit = 20,time = 'week', after = ''):
  subreddit_string = ""

  for sub in subreddits:
    subreddit_string += sub + "+"

  subreddit_string = subreddit_string[:-1]

  url = "http://www.reddit.com/r/%s/%s.json?t=%s&limit=%r&after=%s" % (subreddit_string,sort,time,limit,after)

  response = urlfetch.fetch(url=url,deadline=15)

  posts = []

  if response.status_code == 200:
    data = json.loads(response.content)
  
    for child in data['data']['children']:
      posts.append(
        RedditPost(
          child['data']['name'],
          child['data']['permalink'],
          child['data']['url']))

  return posts












