#! /usr/bin/env python3
from archiver import archive, archive_search, update_archive, is_item_id
import argparse

def update(args):
    update_archive()

def get_search(args):
    for url in args.urls:
        #unquote it
        url = url.replace('"','')
        archive_search(url)

def get(args):
    for id in args.ids:
        if is_item_id(id):
            print('### Now archiving {}'.format(id))
            archive(id)
        else:
            print('#!# MALFORMED ITEM_ID: {}'.format(id))

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

update_help = 'updates all existing archives.'
parser_update = subparsers.add_parser('update', help=update_help)
parser_update.set_defaults(func=update)

get_help = 'download/update the specified list of item_ids.'
parser_get = subparsers.add_parser('get', help=get_help)
parser_get.add_argument('ids', nargs='+',help=get_help)
parser_get.set_defaults(func=get)

get_search_help='download/update every item_id in the search urls. Quote the URLs with "". See note in archiver.py/archive_search on proper URLs.'
parser_search = subparsers.add_parser('get_search', help=get_search_help)
parser_search.add_argument('urls',nargs='+',help=get_search_help)
parser_search.set_defaults(func=get_search)

args = parser.parse_args()
args.func(args)
