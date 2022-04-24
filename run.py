#! /usr/bin/env python

from archiver import archive, archive_all
import argparse
import json
import os

# def update(args):
#     update_archive()

def get(args):
    for id in args.ids:
        archive(id)
        
def get_search(args):
    for text in args.text:
        #unquote it
        url = url.replace('"','')
        archive_all(url)

def update(args):
    for root, dirs, files in os.walk("./archive"):
        if ('story.json' in files):
            archive_info = json.loads(open(root + "/story.json").read())
            if 'deleted' not in archive_info['info']:
                archive(str(archive_info['info']['id']), force_update=args.force, full_update=args.full)

parser = argparse.ArgumentParser(description='Scrapes Writing.com')
subparsers = parser.add_subparsers()

update_help = 'updates all existing archives.'
parser_update = subparsers.add_parser('update', help=update_help)
parser_update.add_argument('--force', action='store_true', help='Force update even if no new chapters')
parser_update.add_argument('--full', action='store_true', help='Perform full refresh')
parser_update.set_defaults(func=update)

get_help = 'download/update the specified list of item_ids.'
parser_get = subparsers.add_parser('get', help=get_help)
parser_get.add_argument('ids', nargs='+',help=get_help)
parser_get.set_defaults(func=get)

get_search_help='download/update every item_id with this text. Quote the text with ""'
parser_search = subparsers.add_parser('get_search', help=get_search_help)
parser_search.add_argument('urls',nargs='+',help=get_search_help)
parser_search.set_defaults(func=get_search)

args = parser.parse_args()
if hasattr(args, "func"):
    args.func(args)
else:
    print("Please specify an action of: {update, get, get_search}")
