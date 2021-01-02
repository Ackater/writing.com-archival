import os
import json

path = "./archive"

results = {}

for root, dirs, files in os.walk(path):
    if ('story.json' in files):
        archive = json.loads(open(root + "/story.json").read())
        info = {
            #'folder': root[10:],
            #'id': archive['info']['id'],
            'author':  archive['info']['author_name'],
            'pretty_title':  archive['info']['pretty_title'],
            'brief_description':  archive['info']['brief_description'],
            'created':  archive['info']['created'],
            'modified':  archive['info']['modified'],
            'chapters': len(archive['chapters'])
        }
        results[root[10:]] = info

file = open('storylist.json','w')
file.write(json.dumps(results, indent=4, sort_keys=True, separators=(',',':')))
file.close()
