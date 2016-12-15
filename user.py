from google.appengine.ext import ndb

from Imgur import Imgur

class User(ndb.Model):
  username = ndb.StringProperty()
  favorites = ndb.StringProperty(repeated=True)
  album = ndb.StringProperty()
  subreddits = ndb.StringProperty(repeated=True)
  access_token = ndb.StringProperty()
  access_expiration = ndb.IntegerProperty()
  refresh_token = ndb.StringProperty()

  @staticmethod
  def create_user(username, access_token, refresh_token, access_expiration, favorites=[], album=''):
    user = User(key=User.user_key(username))
    user.username = username
    user.favorites = favorites
    user.album = album
    user.access_token = access_token
    user.access_expiration = access_expiration
    user.refresh_token = refresh_token

    if album == '':
      print 'creating new album'
      acct = Imgur.Account(username, access_token, 0, refresh_token)
      new_album = Imgur.Album.create_new_album(
        title = 'Redditwalls Favorites',
        description = 'Redditwalls Favorites',
        privacy = 'public',
        layout = 'grid',
        cover = '',
        img_ids = '',
        acct = acct)

      user.album = new_album.album_id

    user.put()
    return user

  @staticmethod
  def user_key(name):
    """Generates datastore key for name"""
    return ndb.Key('User',name)

  @staticmethod
  def get_by_id(user_id):
    return User.user_key(user_id).get()

  def to_imgur_account(self):
    return Imgur.Account(self.username, self.access_token, self.access_expiration, self.refresh_token)
  
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
    




