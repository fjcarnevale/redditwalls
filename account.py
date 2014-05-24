from google.appengine.ext import ndb
from google.appengine.api import images

import urllib
import urllib2

from reddit import RedditPost
from Imgur import Imgur

class Account(ndb.Model):
	username = ndb.StringProperty()
	favorites = ndb.StringProperty(repeated=True)
	album = ndb.StringProperty()
	
	def __init__( username, favorites = [], album = ''):
		self.username = username
		self.favorites = favorites
		self.album = album

	@staticmethod
	def account_key(name):
		"""Generates datastore key for name"""
		return ndb.Key('Account',name)

	@staticmethod
	def get_by_id(user_id):
		return Account.account_key(user_id).get()
	
	def add_favorite(self, wall_id):
		if not wall_id in self.favorites:
			self.favorites.append(wall_id)
			self.put()

	def remove_favorite(self, wall_id):
		try:
			self.favorites.remove(wall_id)
			self.put()
		except ValueError, e:
			# The wall id wasn't a favorite, just return
			pass
		




