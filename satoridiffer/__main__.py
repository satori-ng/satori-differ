#!/usr/bin/env python
from pprint import pprint
import argparse
import os, sys
import random
from string import ascii_letters, digits

from satoricore.image import SatoriImage
from satoricore.crawler import BaseCrawler
from satoricore.logger import logger, set_debug_logger

from satoricore.common import get_image_context_from_arg
from satoricore.file import load_image

from satoridiffer.diffmeta import DiffMeta
from hooker import EVENTS, hook

from satoricore.file.json import SatoriJsoner
from satoricore.file.pickle import SatoriPickler

EVENTS.append([
	"differ.on_start", "differ.pre_open", "differ.with_open",
	"differ.post_close", "differ.on_end",
])

from satoricore.extensions import *  # noqa

_DIFFS_SECTION = 'diffs'
CHECKED_FILES = set()


@hook('differ.on_start')
def set_diff_meta(parser, args, source, destination, results, diff_name):
	diff_meta = DiffMeta(source, destination)
	results.add_class(diff_name, section=_DIFFS_SECTION, data=diff_meta)
	# pprint(diff_meta)
	logger.info("DIFF metadata added for '{}'".format(diff_name))


def diff_directory(file_path, source, destination, results):
	try:
		s_cont = set(source.listdir(file_path))
		d_cont = set(destination.listdir(file_path))
	except PermissionError:
		logger.warning("Permission Denied for listing '{}'. Skipping..."
			.format(file_path)
			)
		return
	source_only = s_cont - d_cont
	dest_only = d_cont - s_cont

	logger.debug("Filepath: " + file_path)
	logger.debug("Source Only:" + str(source_only))
	logger.debug("Dest Only:" + str(dest_only))
	for diff_only in (
			(source_only, "src_only"),
			(dest_only, "dst_only"),
		):
		logger.debug(diff_only[1])
		if diff_only[0]:
			try:
				diff_dict = results.get_attribute(file_path, DIFF_NAME)
				logger.debug(diff_dict)
			except FileNotFoundError:
				diff_dict = {}
				results.set_attribute(file_path,
						diff_dict,
						DIFF_NAME,
						force_create=True,
					)
			diff_dict[diff_only[1]] = list(diff_only[0])
	
	# logger.debug(results)
	# print (s_cont, d_cont)
	common_files = s_cont & d_cont
	# print(common_files)
	for f in common_files:	# Use thread map?
		new_file_path = file_path + '/' + f
		diff_file(new_file_path, source, destination, results)


def diff_file(file_path, source, destination, results):
	if source.is_dir(file_path) and destination.is_dir(file_path):
		diff_directory(file_path, source, destination, results)
	CHECKED_FILES.add(file_path)
	try:
		EVENTS['differ.pre_open'](
			file_path, source, destination, results, DIFF_NAME
		)
	except Exception as e:
		logger.error(e)
		logger.error("File '{}' not found in destination"
				.format(file_path)
			)
			# Store difference in existence

	if EVENTS['differ.with_open']:
		try:
			with source.open(file_path) as fd:	# TODO: When it returns I will stuff it in the right place
				EVENTS['differ.with_open'](
					file_path, file_type, source, destination, results, DIFF_NAME, fd,
				)

			EVENTS['differ.post_close'](
					file_path, file_type, source, destination, results, DIFF_NAME
				)
		except IOError:
			logger.warning("'open()' System Call not supported on {}".format(file_path))


def diff_images(source, destination, entrypoints, results):

	for entrypoint in entrypoints:
		diff_file(entrypoint, source, destination, results)



# def diff_images(source, destination, entrypoints, results,
# 				diff_name, reverse=False):

# 	crawler = BaseCrawler(entrypoints, [],
# 			image=source if not reverse else destination
# 		)

# 	global CHECKED_FILES

# 	for file_path, file_type in crawler():
# 		if file_path in CHECKED_FILES: 
# 			continue
# 		CHECKED_FILES.add(file_path)

# 		try:
# 			EVENTS['differ.pre_open'](
# 				file_path, file_type, source, destination, results, diff_name
# 			)
# 		except:
# 			# logger.error("File '{}' not found in destination"
# 			# 		.format(file_path)
# 			# 	)
# 				# Store difference in existence
# 			continue





def _setup_argument_parser():
	parser = argparse.ArgumentParser()

	parser.add_argument(
		'-e', '--excluded-dirs',
		help='Exclude files under specified locations.',
		action='append',
	)

	parser.add_argument(
		'-l', '--load-extensions',
		help='Load the following extensions',
		action='append',
		default=[],
	)

	parser.add_argument(
		'-i',
		help='Stores the new Diff section and data in the Tested Satori Image',
		action='store_true',
	)

	parser.add_argument(
		'-o', '--output',
		help='The Image file to store the differences',
	)

	# parser.add_argument(
	# 	'-q', '--quiet',
	# 	help=("Does not show Errors"),
	# 	default=False,
	# 	action='store_true',
	# )

	parser.add_argument(
		'-a', '--append',
		help=("Append the diff results to the output Image"),
		default=False,
		action='store_true',
	)

	parser.add_argument(
		'-d', '--debug',
		help=("Shows debug messages"),
		default=False,
		action='store_true',
	)

	parser.add_argument(
		'-t', '--threads',
		help=("Number of threads to use"),
		default=4,
		type=int,
	)

	parser.add_argument(
		'original_image',
		help='The Satori Image to treat as Original',
	)

	parser.add_argument(
		'tested_image',
		help='The Satori Image to be tested',
	)

	parser.add_argument(
		'--entrypoints',
		help='Start iteration using these directories.',
		nargs='+',
	)

	return parser


def get_diff_name(existing):
	existing = list(existing)
	def get_diff_id(diff_name):
		'''
			Get the id value from diff_name of format: d{id}_{tag}
		'''
		return int(diff_name[1:].split('_')[0])

	def new_name(id_):
		# return a d{id}_{tag}
		rand = ''.join(random.choices(ascii_letters + digits, k=6))
		return "d{id}_{tag}".format(
			id=id_,
			tag=rand,   # Add random string to make it greppable
		)
	if not existing: existing.append('d0_0000')
	i = get_diff_id(existing[-1])
	return new_name(i+1)


DIFF_NAME = ""
def main():
	parser = _setup_argument_parser()
	args = parser.parse_args()

	if args.debug: set_debug_logger()

	source_context = get_image_context_from_arg(args.original_image)
	logger.warning("Loaded image '{}'".format(args.original_image))
	destination_context = get_image_context_from_arg(args.tested_image)
	logger.warning("Loaded image '{}'".format(args.tested_image))

 	# if not args.output:

	try:
		results = load_image(args.output)
		if args.append:
			logger.warn("SatoriImage '{}' loaded to archive results".format(args.output))
		else:
			with open(args.output, 'wb') as delete:
				delete.write(b'')
			logger.warn("SatoriImage '{}' overwritten".format(args.output))

	except (TypeError, FileNotFoundError) as te:
		logger.warning("No output image selected")
		logger.info("Using an Empty SatoriImage to store results")
		results = SatoriImage()
	except ValueError:
		logger.error("Output image file '{}' is not a SatoriImage".format(args.output))
		logger.warning("Using an Empty SatoriImage to store results".format(args.output))
		results = SatoriImage()
	assert (results is not None)

	try:
		logger.info("Adding DIFF section in SatoriImage")
		results.add_section(_DIFFS_SECTION)
	except KeyError:
		logger.warning("DIFF Section in SatoriImage already exists")


	existing_diffs = results.get_classes(_DIFFS_SECTION)
	if existing_diffs:
		logger.info("Existing DIFFs in SatoriImage: {}"
				.format(list(existing_diffs))
			)

	global DIFF_NAME
	logger.warning("New DIFF name is '{}'".format(DIFF_NAME))

	with source_context as source:
		with destination_context as destination:
			if not args.entrypoints:
				# s_entrypoints
				try:
					s_epoints = source.get_entrypoints()
					logger.info("Original Image entrypoints: {}".format(s_epoints))
				except:
					logger.warning("Entrypoints for source cannot be specified.")
					d_epoints = set('/')

				try:
					d_epoints = destination.get_entrypoints()
					logger.info("Tested Image entrypoints: {}".format(d_epoints))
				except:
					logger.warning("Entrypoints for destination cannot be specified.")
					d_epoints = set('/')

				common_entrypoints = s_epoints & d_epoints
				if not common_entrypoints:
					logger.critical("No common entrypoints found. Exiting...")
					sys.exit(-1)
				else:
					logger.info("Common Entrypoints are {}"
							.format(str(common_entrypoints))
						)
					args.entrypoints = common_entrypoints
			logger.warning("Operating for entrypoints: {}"
					.format(str(args.entrypoints))
				)

			EVENTS['differ.on_start'](parser=parser, args=args, source=source,
					destination=destination, results=results, diff_name=DIFF_NAME)
			logger.warning("Diff Process Started...")
			diff_images(source, destination, args.entrypoints, results)

	logger.warning("Diff Process Finished!")

	EVENTS['differ.on_end'](results)

	if not args.output:
		print(results)
	else:
		image_serializer = SatoriJsoner()
		# image_serializer = SatoriPickler()
		if args.output.endswith(image_serializer.suffix):
			image_serializer.suffix = ''
		image_serializer.write(results, args.output)
		logger.warn("Stored to file '{}'".format(image_serializer.last_file))

if __name__ == '__main__':
	main()
"""

tr "'" "\"" | jq

"""
