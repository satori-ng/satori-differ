import time
from satoricore.image import SatoriImage, _META_SECTION

class DiffMeta(dict):
	"""docstring for  DiffMeta"""

	def __init__(self, source_im, dest_im):
		super(DiffMeta, self).__init__()

		try:
			self['src'] = source_im.get_class("system", section=_META_SECTION)
			self['src_uuid'] = source_im.get_class("uuid", section=_META_SECTION)
		except:
			pass

		try:
			self['dst'] = dest_im.get_class("system", section=_META_SECTION)
			self['dst_uuid'] = dest_im.get_class("uuid", section=_META_SECTION)
		except:
			pass

		try:
			self['src_type'] = source_im.__name__
		except AttributeError:
			self['src_type'] = type(source_im).__name__

		try:
			self['dst_type'] = dest_im.__name__
		except AttributeError:
			self['dst_type'] = type(dest_im).__name__

		self['tstamp'] = time.time()
		self['date'] = "{date} {tz} sec".format(
				date=time.ctime(),
				tz=time.timezone,
			)
