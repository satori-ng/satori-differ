#!/usr/bin/env python

from satoricore.crawler import BaseCrawler

from hooker import EVENTS

EVENTS.append([
    "differ.on_start", "differ.pre_open", "differ.with_open",
    "differ.post_close", "differ.on_end",
])

from satoricore.extensions import *  # noqa


def diff(source, destination, entrypoints):
    crawler = BaseCrawler(entrypoints, [], source)

    results = {
    }

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
    print(results)


if __name__ == '__main__':
    import os
    from satoricore.serialize import load_image
    image_path = os.path.expanduser('~/work/satori/satori-core/site.json.gz')
    source = load_image(image_path)
    diff(source, os, [os.path.expanduser('~/site_backup')])
