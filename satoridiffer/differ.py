#!/usr/bin/env python
from pprint import pprint
import argparse
import os

from satoricore.serialize import load_image
from satoricore.image import SatoriImage
from satoricore.crawler import BaseCrawler

from hooker import EVENTS, hook

EVENTS.append([
    "differ.on_start", "differ.pre_open", "differ.with_open",
    "differ.post_close", "differ.on_end",
])

from satoricore.extensions import *  # noqa

from satoridiffer.diffmeta import DiffMeta

_DIFFS_SECTION = 'diffs'

@hook('differ.pre_open')
def check_contents(file_path, file_type, source, destination, results):
    if not source.is_dir(file_path) or not destination.is_dir(file_path):
        # print (file_path)
        return
    s_cont = source.listdir(file_path)
    d_cont = destination.listdir(file_path)

    source_only = s_cont - d_cont
    dest_only = d_cont - s_cont

    # print (source_only, dest_only)
    if source_only:
        results.set_attribute(file_path, source_only, 'contents.diff')

    if dest_only:
        results.set_attribute(file_path, dest_only, 'contents.diff')


def diff(source, destination, entrypoints, results):
    crawler = BaseCrawler(entrypoints, [], source)


    for file_path, file_type in crawler():
        EVENTS['differ.pre_open'](
            file_path, file_type, source, destination, results,
        )

        if not EVENTS['differ.with_open']:
            continue

        with source.open(file_path) as fd:
            EVENTS['differ.with_open'](
                file_path, file_type, source, destination, results, fd,
            )

        EVENTS['differ.post_close'](
            file_path, file_type, source, destination, results
        )

    EVENTS['differ.on_end']()
    return results

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
        help='Store the differences in the tested Satori Image',
        action='store_true',
    )

    parser.add_argument(
        '-o', '--output',
        help='The Image file to store the differences',
    )

    parser.add_argument(
        '-q', '--quiet',
        help=("Does not show Errors"),
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


# def initialize_results(source, destination, results_image):
#     pass
def diff_name(existing):
    i = 1
    while True:
        name = 'diff_%d' % i
        if name not in existing:
            return name


if __name__ == '__main__':

    parser = _setup_argument_parser()
    args = parser.parse_args()

    if args.original_image == '.':
        source = os
    else:
        image_path = args.original_image
        source = load_image(image_path)

    if args.tested_image == '.':
        source = os
    else:
        image_path = args.tested_image
        destination = load_image(image_path)

    if not args.entrypoints:
        try :
            args.entrypoints = source.get_entrypoints()
        except:
            args.entrypoints = destination.get_entrypoints()

    results = SatoriImage()
    try:
        results.add_section(_DIFFS_SECTION)
    except KeyError:
        pass
        
    existing_diffs = results.get_classes(_DIFFS_SECTION)
    name = diff_name(existing_diffs)
    diff_meta = DiffMeta(source, destination)
    results.add_class(name, section=_DIFFS_SECTION, data=diff_meta)
    pprint(diff_meta)

    # print(args.entrypoints)
    diff_obj = diff(source, destination, args.entrypoints, results)
    pprint(diff_obj)