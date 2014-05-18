import os
import urllib2

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

from wallpaper import Wallpaper
from account import Account
from Imgur import Imgur
import wallpaper
import account
import reddit

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Index(webapp2.RequestHandler):
	""" Handles requests to the main page """
	def get(self):
		user = users.get_current_user()
		template_values = {}
		if(user):
			template_values['username'] = user.nickname()
			template_values['logout_url'] = users.create_logout_url('/')	
		else:
			template_values['login_url'] = users.create_login_url('/')

		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))

class Results(webapp2.RequestHandler):
	""" Handles requests for wallpapers """
	def get(self): 
		wallpapers = get_wallpapers(
				subreddits = self.request.get('sub', allow_multiple=True),
				sort=self.request.get('sort'),
				time=self.request.get('time'),				
				after=self.request.get('after'))

		thumbnails = {}

		for wall in wallpapers:
			thumbnails[wall.name] = Imgur.thumbnail(wall.image_link, 'medium')

		template_values = { 'wallpapers':wallpapers, 'thumbnails':thumbnails }

		user = users.get_current_user()
		if user:
			account = Account.get_by_id(user.user_id())
			if not account:
				account = Account(key=Account.account_key(user.user_id()))
				account.put()

			template_values['favorites'] = account.favorites
		
		template = JINJA_ENVIRONMENT.get_template('results.html')
		self.response.write(template.render(template_values))

class Favorite(webapp2.RequestHandler):
	""" Handles favoriting of wallpapers """
	def get(self):
		wall_id = self.request.get('wall_id')
		action = self.request.get('action')

		# check that wallpaper exists
		if Wallpaper.get_by_id(wall_id):
			user = users.get_current_user()
			if user:
				account = Account.get_by_id(user.user_id())

				if not account:
					account = Account(key=Account.account_key(user.user_id()))
					account.put()

				if action == 'add':				
					account.add_favorite(wall_id)
				else:
					account.remove_favorite(wall_id)

		self.response.write(action + ' ' + wall_id)

class DisplayFavorites(webapp2.RequestHandler):
	""" Handles requests for the favorites page """
	def get(self):
		user = users.get_current_user();
		if(user):
			favorites = Account.get_by_id(user.user_id()).favorites

			walls = []
			for fav in favorites:
				walls.append(Wallpaper.get_by_id(fav))
			
			thumbnails = {}
			for wall in walls:
				thumbnails[wall.name] = Imgur.thumbnail(wall.image_link, 'medium')

			template_values = { 	'username':user.nickname(),
						'logout_url':users.create_logout_url('/'),
						'wallpapers':walls,
						'thumbnails':thumbnails
					  }

			template = JINJA_ENVIRONMENT.get_template('favorites.html')
			self.response.write(template.render(template_values))
	

def get_wallpapers(subreddits = ['wallpapers'],sort = 'top',time = 'week',limit = 30, after = ''):	
	"""Creates wallpapers based on reddit posts"""
	posts = reddit.get_posts(subreddits,sort,limit,time,after)
	wallpapers = wallpaper.create_wallpapers(posts)
	return wallpapers








        
