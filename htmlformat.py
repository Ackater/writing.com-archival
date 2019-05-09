from jinja2 import Template, Environment, PackageLoader
from defs import ChapterInfo, StoryInfo
from datetime import datetime
import re
import sys

#Load templates from ./templates/
env = Environment(loader=PackageLoader(__name__,'templates'))

def formatChapter(chapterInfo, descent,existingdescents):
    previouschapter = descent[:-1]

    #Jinja doesn't support 'in' in if statements
    existsdescentfor = list(range(1+len(chapterInfo.choices)))
    for i in range(len(chapterInfo.choices)):
        existsdescentfor[i] = (descent + str(i+1)) in existingdescents

    emptychoices = chapterInfo.choices == []
        
    template = env.get_template('chapter.html')

    return template.render(emptychoices=emptychoices,
                           existingdescents=existsdescentfor,
                           previouschapter=previouschapter,
                           chapterInfo=chapterInfo,
                           descent=descent,
                           date="{:%B %d, %Y}".format(datetime.now()))

def formatIntro(storyInfo):
    template = env.get_template('intro.html')
    return template.render(storyInfo=storyInfo)

''' imput: equal len lists of strings for chapter descent strings and associated chapter names'''
def formatOutline(storyTitle, descents,names):
    template = env.get_template('outline.html')
    return template.render(num=range(len(names)),
                           names=names,
                           descents=descents,
                           title=storyTitle)

