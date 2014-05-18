from urlparse import urlparse
from collections import defaultdict
import urllib
import urllib2
import json
import exceptions
import logging
import traceback

api_base = 'https://api.imgur.com/3/'
image_endpoint = api_base + 'image'
album_endpoint = api_base + 'album'
client_id = 'a1625eb9cf145b1'
auth = ('Authorization','Client-ID %s' % client_id)
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


def api_call(endpoint, payload=None):
	"""Executes an imgur api call to the image endpoint"""

	req = urllib2.Request(endpoint)

	if payload is not None:
		req.add_data(urllib.urlencode(payload))
			
	req.add_header(auth[0], auth[1])

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
	
	if response is not None and response.getcode() == 200:
		result = json.loads(response.read())

		if result['success']:
			return ImageInfo.from_json(result['data'])


def upload_image_from_file(path, album='', name='', title='', description=''):
	""" Uploads an image from a file """
	f = open(path)
	content = f.read()

	# TODO implement other parameters
	payload = {'image':content, 'type':'file'}
	response = api_call(image_endpoint, payload)

	if response is not None and response.getcode() == 200:
		result = json.loads(response.read())

		if result['success']:
			return ImageInfo.from_json(result['data'])

def delete_image(deletehash):
	""" Deletes an image """
	url = image_endpoint + '/' + deletehash

	req = RequestWithMethod(url,'DELETE')
	req.add_header(auth[0], auth[1])	
	response = urllib2.urlopen(req)

	if response.getcode() == 200:
		result = json.loads(response.read())
		return result['success']

def thumbnail(link, size = "small"):
	""" Creates a thumbnail url """
	if size in ImageInfo.thumbnail_sizes:
		pos = link.rfind('.')
		url = link[:pos]
		ext = link[pos:]
		return url + ImageInfo.thumbnail_sizes[size] + ext

class ImageInfo():
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
		""" Builds an ImageInfo from json """
		str_dict =  defaultdict(str,data)
		int_dict =  defaultdict(int,data)
		bool_dict = defaultdict(bool,data)

		return ImageInfo(
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
		""" Builds an ImageInfo based on a id """
		url = image_endpoint + '/' + img_id
		req = urllib2.Request(url)
		req.add_header(auth[0], auth[1])	
		response = urllib2.urlopen(req)
		
		parsed = json.loads(response.read())

		if parsed['success']:
			return ImageInfo.from_json(parsed['data'])

	@staticmethod
	def from_url(url):
		"""Gets image info from a url"""

		if not is_imgur_link(url):
			return None

		img_id = url[url.rfind('/')+1:]

		if '.' in img_id:
			img_id = img_id[:img_id.rfind('.')]

		return ImageInfo.from_id(img_id)

	
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

	@staticmethod
	def create_new_album(
				img_ids = [],
				title = '',
				description = '',
				privacy = '',
				layout = '',				
				cover = ''):

		""" Creates a new album """
		payload = { 
			'ids':img_ids,
			'title':title,
			'description':description,
			'privacy':privacy,
			'layout':layout,
			'cover':cover
			}

		response = api_call(album_endpoint, payload)
		
		if response is not None:
			parsed = json.loads(response.read())

			if parsed['success']:
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
				images.append(ImageInfo.from_json(image))

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
		url = album_endpoint + '/' + album_id
		req = urllib2.Request(url)
		req.add_header(auth[0], auth[1])	
		response = urllib2.urlopen(req)
		
		parsed = json.loads(response.read())

		if parsed['success']:
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




















