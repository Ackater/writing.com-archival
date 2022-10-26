from collections import namedtuple
from typing import Dict, Any

class StoryInfo(namedtuple('StoryInfo', ['id', 'author_id', 'author_name', 'description', 'pretty_title', 'brief_description', 'image_url', 'created', 'modified', 'last_full_update', 'keywords', 'rating', 'access'])):
    def to_dict(self) -> Dict[str, Any]:
        temp = self._asdict()
        for key in self._fields:
            if temp[key] is None:
                del temp[key]
        return temp

class Chapter(namedtuple('Chapter', ['id', 'created', 'title', 'content', 'author_id', 'author_name', 'choices', 'deleted'])):
    def to_dict(self, skip = [] ) -> Dict[str, Any]:
        temp = self._asdict()
        for key in self._fields:
            #Remove empty fields and skipped fields
            if temp[key] is None or key in skip:
                del temp[key]
        return temp

class ServerRefusal(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
