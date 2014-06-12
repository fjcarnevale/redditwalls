from urlparse import urlparse
from collections import defaultdict
import urllib
import urllib2
import json
import exceptions
import logging
import traceback
import time

api_base = 'https://api.imgur.com'
image_endpoint = api_base + '/3/image'
album_endpoint = api_base + '/3/album'
auth_endponit  = api_base + '/oauth2/authorize'
token_endpoint = api_base + '/oauth2/token'
client_id = 'a1625eb9cf145b1'
client_secret = '7f028de499b790ecccb10e2eefecb5aa6c0ad614'
app_auth_val = 'Client-ID %s' % client_id
extensions = ['.jpg','.jpeg','.gif','.png']

class InvalidImgurUrlException(Exception):
   pass

class RequestWithMethod(urllib2.Request):
    """Workaround for using DELETE with urllib2"""
    def __init__(self, url, method, data=None, headers={},\
        origin_req_host=None, unverifiable=False):
        self._method = method
        urllib2.Request.__init__(self, url, data, headers,\
                 origin_req_host, unverifiable)

    def get_method(self):
        if self._method:
            return self._method
        else:
            return urllib2.Request.get_method(self) 

def album_or_image(url):
	""" Determines if the url is an imgur album or image """
	if is_album(url):
		return 'album'
	elif is_image(url):
		return 'image'
	else:
		raise InvalidImgurUrlException("Fa. Optional parameter of ids[] is an array of image ids to add to the album (if you're authenticated with an account).iled to parse Imgur url")
   
def is_album(url):
	""" Checks if the url points to an imgur album """
	return is_imgur_link(url) and '/a/' in url
   
def is_image(url):
	""" Checks if the url points to an imgur image """
	return is_imgur_link(url) and not '/a/' in url
   
def is_imgur_link(url):
	""" Checks if url points to imgur """
	return 'imgur.com' in url

def is_image_link(url):
	""" Basic guess at whether the url links to an image """
	return any(ext in url for ext in extensions)
   
def extract_imgur_id(url):
	""" Extracts the imgur id from an imgur url """

	pos = url.rfind('/')
   
	if pos >= 0:
		id_str = url[pos+1:]

	pos = id_str.rfind('.')
	if pos > 0:
	 	id_str = id_str[:pos]

		return id_str

	else:
		raise InvalidImgurUrlException("Failed to parse Imgur url")

def api_call(endpoint, payload=None, auth_val=app_auth_val, method=None):
	"""Executes an imgur api call to the image endpoint"""

	req = urllib2.Request(endpoint)

	if method is not None:
		print 'Using method %r' % method
		req.get_method = lambda: method

	if payload is not None:
		req.add_data(urllib.urlencode(payload))
			
	req.add_header('Authorization', auth_val)

	try:	
		return urllib2.urlopen(req)
	except urllib2.HTTPError, e:
		logging.error('HTTPError = ' + str(e.code))
	except urllib2.URLError, e:
		logging.error('URLError = ' + str(e.reason))
	except Exception:
		logging.error('generic exception: ' + traceback.format_exc())

def upload_image_from_url(url, album='', name='', title='', description=''):
	""" Uploads an image from a url """

	# Check that we can probably upload this
	if not is_image_link(url):
		logging.warning('This does not appear to be an image url: %s' % url)
		return None

	logging.info('Uploading image from %s' % url)

	# TODO implement other parameters
	payload = {'image':url, 'type':'URL'}
	response = api_call(image_endpoint, payload)
	
	if response is None or response.getcode() != 200:
		return None

	result = json.loads(response.read())

	if not result['success']:
		return None

	return Image.from_json(result['data'])

def upload_image_from_file(path, album='', name='', title='', description=''):
	""" Uploads an image from a file """
	f = open(path)
	content = f.read()

	# TODO implement other parameters
	payload = {'image':content, 'type':'file'}
	response = api_call(image_endpoint, payload)

	if response is None or response.getcode() != 200:
		return None
	
	result = json.loads(response.read())

	if not result['success']:
		return None

	return Image.from_json(result['data'])

def delete_image(deletehash):
	""" Deletes an image """
	url = image_endpoint + '/' + deletehash

	req = RequestWithMethod(url,'DELETE')
	req.add_header('Authorization', app_auth_val)	
	response = urllib2.urlopen(req)

	if response.getcode() == 200:
		result = json.loads(response.read())
		return result['success']

def thumbnail(link, size = "small"):
	""" Creates a thumbnail url """
	if size in Image.thumbnail_sizes:
		pos = link.rfind('.')
		url = link[:pos]
		ext = link[pos:]
		return url + Image.thumbnail_sizes[size] + ext

def get_login_url(response_type = 'token', state = ''):
	url = auth_endponit
	url += '?client_id=%s' % client_id
	url += '&response_type=%s' % response_type
	#url += '&state=%s' % state

	#TODO implement state
	# including state seems to mess up the callback URL
	# with state=# and no & before the access_token

	return url

class Account():
	def __init__(
			self,
			username,
			access_token,
			access_expiration,
			refresh_token):

		self.username = username
		self.access_token = access_token
		self.access_expiration = access_expiration
		self.refresh_token = refresh_token

	def refresh_tokens(self):
		payload = {
			'client_id':client_id,
			'client_secret':client_secret,
			'grant_type':'refresh_token',
			'refresh_token':self.refresh_token
			}

		response = api_call(token_endpoint,payload)

		if response is not None:
			data = response.read()
			print data			
			content = json.loads(data)

			self.access_expiration = int(time.time()) + int(content['expires_in'])
			self.access_token = content['access_token']
			self.refresh_token = content['refresh_token']

	def is_access_expired(self):
		return time.time() > self.access_expiration
		
	def get_auth(self):
		if self.is_access_expired():
			logging.info('Access expired for user %s, refreshing tokens' % self.username)
			self.refresh_tokens()

		return 'Bearer %s' % self.access_token

	@staticmethod
	def from_refresh_token(refresh_token):
		payload = {
			'client_id':client_id,
			'client_secret':client_secret,
			'grant_type':'refresh_token',
			'refresh_token':refresh_token
			}

		response = api_call(token_endpoint,payload)

		if response is not None:
			data = response.read()

			content = json.loads(data)

			access_expiration = int(time.time()) + int(content['expires_in'])

			return Account(
				content['account_username'],
				content['access_token'],
				access_expiration,
				content['refresh_token'])
			

	@staticmethod
	def from_authorization_code(code):
		payload = {
			'client_id':client_id,
			'client_secret':client_secret,
			'grant_type':'authorization_code',
			'code':code
			}

		response = api_call(token_endpoint,payload)

		if response is not None:
			content = json.loads(response.read())

			if not 'username' in content:
				return Account.from_refresh_token(content['refresh_token'])

			access_expiration = int(time.time()) + int(content['expires_in'])

			return Account(
				content['username'],
				content['access_token'],
				access_expiration,
				content['refresh_token'])
			
class Image():
	""" Class to handle information about imgur images """

	thumbnail_sizes = { 'small':'t',
			'medium':'m',
			'large':'l',
			'huge':'h'}

	def __init__(
			self,
			img_id = '',
			title = '',
			description = '',
			datetime = '',
			mime_type = '',
			animated = False,
			width = 0,
			height = 0,
			size = 0,
			views = 0,
			bandwidth = 0,
			favorite = False,
			nsfw = False,
			section = '',
			deletehash = '',
			link = ''):

		self.img_id = img_id
		self.title = title
		self.description = description
		self.datetime = datetime
		self.mime_type = mime_type
		self.animated = animated
		self.width = width
		self.height = height
		self.size = size
		self.views = views
		self.bandwidth = bandwidth
		self.favorite = favorite
		self.nsfw = nsfw
		self.section = section
		self.deletehash = deletehash
		self.link = link
			
	@staticmethod
	def from_json(data):
		""" Builds an Image from json """
		str_dict =  defaultdict(str,data)
		int_dict =  defaultdict(int,data)
		bool_dict = defaultdict(bool,data)

		return Image(
			img_id = str_dict['id'],
			title = str_dict['title'],
			description = str_dict['description'],
			datetime = str_dict['datetime'],
			mime_type = str_dict['type'],
			animated = bool_dict['animated'],
			width = int_dict['width'],
			height = int_dict['height'],
			size = int_dict['size'],
			views = int_dict['views'],
			bandwidth = int_dict['bandwidth'],
			favorite = bool_dict['favorite'],
			nsfw = bool_dict['nsfw'],
			section = str_dict['section'],
			deletehash = str_dict['deletehash'],
			link = str_dict['link'])

	@staticmethod
	def from_id(img_id):
		""" Builds an Image based on a id """
		endpoint = image_endpoint + '/' + img_id
	
		response = api_call(endpoint)
		
		parsed = json.loads(response.read())

		if not parsed['success']:
			return None
			
		return Image.from_json(parsed['data'])

	@staticmethod
	def from_url(url):
		"""Gets image info from a url"""

		if not is_imgur_link(url):
			return None

		img_id = url[url.rfind('/')+1:]

		if '.' in img_id:
			img_id = img_id[:img_id.rfind('.')]

		return Image.from_id(img_id)

class Album():
	""" Class to handle information about imgur albums """

	def __init__(
			self,
			album_id = '',
			title = '',
			description = '',
			datetime = 0,
			cover = '',
			cover_width = 0,
			cover_height = 0,
			account_url = '',
			privacy = '',
			layout = '',
			views = 0,
			images_count = 0,
			images = [],
			deletehash = '',
			link = ''):

		self.album_id = album_id
		self.title = title
		self.description = description
		self.datetime = datetime
		self.cover = cover
		self.cover_width = cover_width
		self.cover_height = cover_height
		self.account_url = account_url
		self.privacy = privacy
		self.layout = layout
		self.views = views
		self.images_count = images_count
		self.images = images
		self.deletehash = deletehash
		self.link = link
		
	# Adds images to the album
	# img_ids	- image ids
	# acct		- Account of user
	#
	# returns 	- True for success, False otherwise
	def add_image(self, img_ids, acct):
		payload = {'ids':img_ids}
		
		endpoint = '%s/%s/add' % (album_endpoint, self.album_id)
		auth = acct.get_auth()
		
		response = api_call(endpoint, payload, auth)
		
		if response is None:
			return False

		parsed = json.loads(response.read())

		return parsed['data'] and parsed['success']

	def remove_image(self, img_id, acct):		
		endpoint = '%s/%s/remove_images?ids=%s' % (album_endpoint, self.album_id, img_id)
		auth = acct.get_auth()
		
		response = api_call(endpoint=endpoint, auth_val=auth, method='DELETE')
		
		if response is None:
			return False

		parsed = json.loads(response.read())

		print parsed

		return parsed['data'] and parsed['success']

	@staticmethod
	def create_new_album(
				img_ids = [],
				title = '',
				description = '',
				privacy = '',
				layout = '',				
				cover = '',
				acct = None):		

		""" Creates a new album """
		payload = { 
			#'ids':img_ids,
			'title':title,
			#description':description,
			#'privacy':privacy,
			'layout':layout,
			#'cover':cover
			}
			
		auth = app_auth_val
		if acct is not None:
			auth = 'Bearer %s' % acct.access_token
			
		response = api_call(album_endpoint, payload, auth)
		
		if response is None:
			return None

		parsed = json.loads(response.read())

		if not parsed['success']:
			return None

		return Album.from_json(parsed['data'])	
		
			
	@staticmethod
	def from_json(data):
		""" Builds an Album from json """
		str_dict =  defaultdict(str,data)
		int_dict =  defaultdict(int,data)
		bool_dict = defaultdict(bool,data)

		images = []
		if 'images' in data:
			for image in data['images']:
				images.append(Image.from_json(image))

		return Album(
			album_id = str_dict['id'],
			title = str_dict['title'],
			description = str_dict['description'],
			datetime = int_dict['datetime'],
			cover = str_dict['cover'],
			cover_width = int_dict['cover_width'],
			cover_height = int_dict['cover_height'],
			account_url = str_dict['account_url'],
			privacy = str_dict['privacy'],
			images = images,
			deletehash = str_dict['deletehash'],
			link = str_dict['link'])

	@staticmethod
	def from_id(album_id):
		""" Builds an Album based on a id """
		endpoint = album_endpoint + '/' + album_id
		response = api_call(endpoint)

		if response is None:
			return None
		
		parsed = json.loads(response.read())

		if not parsed['success']:
			return None
		
		return Album.from_json(parsed['data'])

	@staticmethod
	def from_url(url):
		"""Gets Album from a url"""
		if not is_imgur_link(url):
			return None

		album_id = url[url.rfind('/')+1:]

		if '#' in album_id:
			album_id = album_id[:album_id.rfind('#')]

		return Album.from_id(album_id)




















