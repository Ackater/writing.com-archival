#Fucking mutable data I wish I was in Clojure
from scraper import get_chapter_list
from aggregator import get_chapters,get_story_info_safe
from htmlformat import formatChapter, formatIntro, formatOutline
import os

def barf(filepath, text):
    with open(filepath,'w') as o:
        o.write(text)

def get_missing_chapters(canon_descents,directory,story_id):
    canon_chapters = [x + ".html" for x in canon_descents]

    os.chdir(directory)

    existing_chapters = os.listdir()
    existing_chapters = set(existing_chapters) - set(['intro.html','outline.html'])

    missing_chapters_all = list(set(canon_chapters) - existing_chapters)

    #We also need to list the chapters previous each missing chapter to update links naively lol
    missing_chapters_connections = set(list(missing_chapters_all))
    for ch in missing_chapters_all:
        c = ch[:-6] + '.html'
        if c != '.html':
            try:
                os.remove(c)
            except FileNotFoundError:
                pass
            missing_chapters_connections.add(c)

    os.chdir('../../')

    if len(canon_chapters) == len(missing_chapters_all):
        print('# {}: Downloading for the first time.'.format(story_id))
    else:
        print('# {}: Updating with {} chapters.'.format(story_id,len(missing_chapters_connections)))

    return [ x[:-5] for x in missing_chapters_connections ]

def archive(story_id):
    #Directory
    #Hard coded because the stylesheet in ./templates/style.css is referenced with a relative path
    archive_dir="archive"
    story_root = archive_dir+"/"+story_id+"/"
    
    if not os.path.exists(story_root):
        os.makedirs(story_root)

    print('# {}: Gathering info.'.format(story_id))

    #Basic info
    info = get_story_info_safe(story_id)
    barf(story_root + "intro.html",formatIntro(info))

    #Outline
    canon_descents, canon_names = get_chapter_list(story_id)
    barf(story_root + "outline.html",formatOutline(info.pretty_title,canon_descents,canon_names))

    #Missing chapters
    missing_chapters = get_missing_chapters(canon_descents,story_root,story_id)
    chapters = get_chapters(story_id, missing_chapters, threads_per_batch=15)

    #Barf chapters
    error_chapters = {}
    existingdescents = list(chapters.keys())
    for descent,chapter in chapters.items():
        if issubclass(type(chapter),Exception):
            error_chapters[descent] = chapter
        else:
            barf(story_root + descent + ".html", formatChapter(chapter,descent,existingdescents))

    if len(error_chapters) > 0:
     print('# {}: Finished with {} errors. Try again. If problem persists contact the developer.'.format(story_id,len(error_chapters)))
    else:
        print('# {}: Finished!'.format(story_id))

    return error_chapters
