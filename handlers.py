import os
import urllib2

from google.appengine.ext import ndb

import jinja2
import webapp2
from webapp2_extras import sessions

from wallpaper import Wallpaper
from user import User
from Imgur import Imgur
import wallpaper
import user
import reddit

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

imgur_login = 'https://api.imgur.com/oauth2/authorize?client_id=&response_type=token&state='

# Sourced from https://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

class Index(BaseHandler):
	""" Handles requests to the main page """
	def get(self):
		username = self.session.get('username', '')
		template_values = {}

		if username != '':
			user = User.get_by_id(username)

			if user is not None:
				template_values['username'] = username
				template_values['logout_url'] = '/?logout=true' #TODO fix log out
			else:
				self.session['username'] = ''

		else:
			template_values['login_url'] = Imgur.get_login_url(response_type='code')

		template = JINJA_ENVIRONMENT.get_template('html/index.html')
		self.response.write(template.render(template_values))

class Results(BaseHandler):
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

		username = self.session.get('username')
		if username is not None and username != '':
			user = User.get_by_id(username)
			if user is not None:
				template_values['favorites'] = user.favorites
		
		template = JINJA_ENVIRONMENT.get_template('html/results.html')
		self.response.write(template.render(template_values))

class Favorite(BaseHandler):
	""" Handles favoriting of wallpapers """
	def get(self):
		wall_id = self.request.get('wall_id')
		action = self.request.get('action')
		username = self.session.get('username', '')

		# check that wallpaper exists
		wall = Wallpaper.get_by_id(wall_id)
		if wall is not None:
			user = User.get_by_id(username)
			if user is not None:

				acct = user.to_imgur_account()
				album = Imgur.Album.from_id(user.album)

				if action == 'add':				
					user.add_favorite(wall_id)
					album.add_image(Imgur.extract_imgur_id(wall.image_link), acct)
				else:
					user.remove_favorite(wall_id)
					img_id = Imgur.extract_imgur_id(wall.image_link)
					print 'Removing %s' % img_id
					album.remove_image(img_id, acct)

		self.response.write(action + ' ' + wall_id)

class DisplayFavorites(BaseHandler):
	""" Handles requests for the favorites page """
	def get(self):

		username = self.session.get('username', '')

		if(username):
			favorites = User.get_by_id(username).favorites

			walls = []
			for fav in favorites:
				walls.append(Wallpaper.get_by_id(fav))
			
			thumbnails = {}
			for wall in walls:
				thumbnails[wall.name] = Imgur.thumbnail(wall.image_link, 'medium')

			template_values = { 'username':username,
						'logout_url':'/?logout=true', # TODO fix logout URL
						'wallpapers':walls,
						'thumbnails':thumbnails
					  }

			template = JINJA_ENVIRONMENT.get_template('html/favorites.html')
			self.response.write(template.render(template_values))
	
class OAuthHandler(BaseHandler):
	""" Handles oauth callbacks """
	def get(self):
		code = self.request.get('code', '')

		# TODO just use username returned from original request
		acct = Imgur.Account.from_authorization_code(code)

		if acct is None:
			# If we couldn't retrieve the account, nothing more we can do here
			return self.redirect('/')

		user = User.get_by_id(acct.username)

		if user is None:
			User.create_user(acct.username, acct.access_token, acct.refresh_token, acct.access_expiration)

		self.session['username'] = acct.username

		return self.redirect('/')


def get_wallpapers(subreddits = ['wallpapers'],sort = 'top',time = 'week',limit = 30, after = ''):	
	"""Creates wallpapers based on reddit posts"""
	posts = reddit.get_posts(subreddits,sort,limit,time,after)
	wallpapers = wallpaper.create_wallpapers(posts)
	return wallpapers








        
