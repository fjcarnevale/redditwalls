from google.appengine.ext import ndb
from google.appengine.api import images

import logging
import urllib
import urllib2

from reddit import RedditPost
from Imgur import Imgur

class Wallpaper(ndb.Model):
	name = ndb.StringProperty()
	height = ndb.IntegerProperty()
	width = ndb.IntegerProperty()
	reddit_link = ndb.StringProperty()
	image_link = ndb.StringProperty()

	@staticmethod
	def get_by_id(wall_id):
		return wallpaper_key(wall_id).get()

	@staticmethod
	def from_post(post):
		url = post.link_url

		if Imgur.is_imgur_link(url):
			if Imgur.is_image(url):
				info = Imgur.ImageInfo.from_url(url)
				w = Wallpaper(key=wallpaper_key(post.name))
				w.name = post.name
				w.reddit_link = post.post_url
				w.image_link = info.link
				w.put()
				return w
			else:
				# TODO handle albums
				pass
		else:
			pass # don't upload new stuff for now
			# Try and upload from the url
			#info = Imgur.upload_image_from_url(url)

			#if info is not None:
			#	logging.info('Uploaded image id:%s\tdeletehash:%s' % (info.img_id, info.deletehash))
			#	w = Wallpaper(key=wallpaper_key(post.name))
			#	w.name = post.name
			#	w.reddit_link = post.post_url
			#	w.image_link = info.link
			#	w.put()
			#	return w

		return None				

def wallpaper_key(name):
		"""Generates datastore key for name"""
		return ndb.Key('Wallpaper',name)

def create_wallpapers(posts):
	"""Creates and commits wallpapers from the given reddit posts"""
	wallpapers = []

	for post in posts:
		# see if this wallpaper exists
		wallpaper = Wallpaper.get_by_id(post.name)

		if not wallpaper:
			wallpaper = Wallpaper.from_post(post)
		
		if wallpaper is not None:
			wallpapers.append(wallpaper)

	return wallpapers

