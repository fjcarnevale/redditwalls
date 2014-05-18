import webapp2
import handlers

application = webapp2.WSGIApplication([
	('/', handlers.Index),
	('/results', handlers.Results),
	('/favorite', handlers.Favorite),
	('/favorites', handlers.DisplayFavorites),
], debug=True)




























