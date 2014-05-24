import webapp2
import handlers

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
}

application = webapp2.WSGIApplication([
	('/', handlers.Index),
	('/results', handlers.Results),
	('/favorite', handlers.Favorite),
	('/favorites', handlers.DisplayFavorites),
	('/oauth', handlers.OAuthHandler)
], config=config, debug=True)




























