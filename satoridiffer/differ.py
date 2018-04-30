#!/usr/bin/env python
import argparse

from satoricore.image import SatoriImage
from satoricore.crawler import BaseCrawler

from hooker import EVENTS, hook

EVENTS.append([
    "differ.on_start", "differ.pre_open", "differ.with_open",
    "differ.post_close", "differ.on_end",
])

from satoricore.extensions import *  # noqa

@hook('differ.pre_open')
def check_contents(file_path, file_type, source, destination, results):
    if not source.is_dir(file_path) or not destination.is_dir(file_path):
        print (file_path)
        return
    s_cont = source.listdir(file_path)
    d_cont = destination.listdir(file_path)

    source_only = s_cont - d_cont
    dest_only = d_cont - s_cont

    print (source_only, dest_only)
    if source_only:
        results.set_attribute(file_path, source_only, 'contents.diff')

    if dest_only:
        results.set_attribute(file_path, dest_only, 'contents.diff')


def diff(source, destination, entrypoints):
    crawler = BaseCrawler(entrypoints, [], source)

    results = SatoriImage()

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
        'entrypoints',
        help='Start iteration using these directories.',
        nargs='+',
    )

    parser.add_argument(
        'original_image',
        help='The Satori Image to treat as Original',
    )

    parser.add_argument(
        'tested_image',
        help='The Satori Image to be tested',
    )

    return parser

if __name__ == '__main__':
    import os
    from satoricore.serialize import load_image

    parser = _setup_argument_parser()
    # args = parser.parse_args()

    image_path = os.path.expanduser('../satori-core/test_image1.json.gz')
    source = load_image(image_path)
    image_path = os.path.expanduser('../satori-core/test_image3.json.gz')
    destination = load_image(image_path)

    diff_obj = diff(source, destination, ['/tmp/dir'])
    from pprint import pprint
    pprint(diff_obj)