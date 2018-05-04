import time
from satoricore.image import SatoriImage, _META_SECTION

class DiffMeta(dict):
	"""docstring for  DiffMeta"""

	def __init__(self, source_im, dest_im):
		super(DiffMeta, self).__init__()
		self['source'] = source_im.get_class("system", section=_META_SECTION)
		self['destination'] = dest_im.get_class("system", section=_META_SECTION)
		self['timestamp'] = time.time()
		self['unixtime'] = "{date} {tz} sec".format(
				date=time.ctime(),
				tz=time.timezone,
			)



# a = DiffMeta('a','b')
# print (a) 
