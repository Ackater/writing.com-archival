class ChapterInfo:
    def __init__(self):
        self.title = ""
        self.content = ""
        self.author_id = ""
        self.author_name = ""
        self.is_author_past = False
        self.choices = [] #list of choices titles in choice order.
        
class StoryInfo:
    def __init__(self):
        self.author_id = ""
        self.author_name = ""
        self.description = ""
        self.pretty_title= ""
        self.brief_description = ""
        self.image_url = ""

class ServerRefusal(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)
