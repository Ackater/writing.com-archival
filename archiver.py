from scraper import get_story_info, get_outline, get_chapter, get_all_interactives_list, get_recent_chapters
from json import dumps, loads
from defs import ServerRefusal, StoryInfo, Chapter
from htmlformat import formatIndex

import os
import threading
import requests
import time
import traceback
import session 

def archive_list(filename):
    with open(filename, 'r') as o:
        for line in o:
            #Make sure to clear newlines
            archive(line.rstrip())

def archive_all(pages = -1, oldest_first = False, force_update = False, full_update = False, premium = False, threads_per_batch = 10, start_page = 1, search_string = None):
    #2 interactive with broken outlines that do not play well with a membership's outline preview feature
    #TODO option for normal account to grab the outlines
    bad_list = ['1393778-Comic-Book-Womens-Feet', '1575204-Fantasy-Foot-Fetish-Mansion', '1832687-The-Alternate-Dimension-Wish']
    #1832687-The-Alternate-Dimension-Wish is there because of this fucking guy https://www.writing.com/main/interactive-story/item_id/1832687-The-Alternate-Dimension-Wish/map/15533221

    #TODO modify this to pass a date instead so can check the date before scraping chapter?
    interactives = get_all_interactives_list(start_page = start_page, pages = pages, oldest_first = oldest_first, search_string = search_string)
    for interactive in interactives:
        if premium and interactive in bad_list:
            continue
        complete = archive(interactive, force_update = force_update, full_update = full_update, threads_per_batch = threads_per_batch) 
        if complete is False:
            break

def archive(story_id, force_update = False, full_update = False, threads_per_batch = 10):
    archive_dir = "archive"

    print('# {}: Gathering info.'.format(story_id))

    #Basic info
    info = get_story_info(story_id)
    if info == -1:
        print('# {}: Private story. Cant scrape'.format(story_id))

    if info is False:
        print('# {}: Deleted story. Cant scrape'.format(story_id))
        return True

    story_root = archive_dir+"/"+ str(info.id) +"/"

    if session.name_in_archive:
        story_root = archive_dir+"/"+ str(info.id) + " " + str(info.pretty_title) +"/"

    chapters = {}
    error_chapters = {}
    new_recent_chapters = []
    recents = False


    #Existing archive already
    if (os.path.exists(story_root + "story.json")):
        #these are already all dicts
        old_archive = loads(open(story_root + "story.json").read())

        #save the date seperately in case we need it for the recent check
        last_modified = old_archive['info']['modified']

        #Has not been modified since last date
        if info.modified <= old_archive['info']['modified'] and force_update == False and full_update == False:
            print('# {}: No updates - has not been modified'.format(story_id))
            return True

        #import old chapters
        chapters = old_archive['chapters']

        #update info with new info
        temp_old_archive = info.to_dict()
        old_archive['info'].update(temp_old_archive)
        #Hack for missing field, maybe dlete in the future
        if 'last_full_update' not in old_archive['info']:
            old_archive['info']['last_full_update'] = 0

        #full update check
        if info.modified <= old_archive['info']['last_full_update']:
            print('# {}: No updates - has not been modified'.format(story_id))
            return True

        info = StoryInfo(**old_archive['info'])

        print('# {}: Getting recent chapters.'.format(story_id))
        recents = get_recent_chapters(story_id)

        #Count how many recent chapters we've had since the last update
        for descent, recent in recents.items():
            if not descent in chapters:
                new_recent_chapters.append(descent)
                #TODO compare dates as a way to check chapters that have been deleted and re-used

        #No modified dates, so probably something else change. Needs a full update
        #It could be a modified chapter, deleted chapter, or just info updated
        if len(new_recent_chapters) == 0 and full_update == False and force_update == False:
            print('# {}: No updates - no new recent chapter'.format(story_id))

            #save anyways to update date or info
            story = {
                'info': info._asdict(),
                'chapters': chapters
            }
            with open(story_root + 'story.json','w',encoding='utf-8') as o:
                o.write(dumps(story, indent=4, sort_keys=True, separators=(',',':')))

            return True
        elif not( len(new_recent_chapters) < len(recents) ) or force_update == True:
            # Skip the outline and use the recent chapters list if there is at least 1 recent chapter that is already grabbed
            # Clean the list otherwise
            new_recent_chapters = []

    #Grab recents if it has not been set
    if recents is False:
        print('# {}: Getting recent chapters.'.format(story_id))
        recents = get_recent_chapters(story_id)

    #Grab outline if recent chapters was not enough
    if len (new_recent_chapters ) == 0 or force_update is True or full_update is True:
        #Outline
        print('# {}: Getting outline.'.format(story_id))
        canon_descents = get_outline(story_id)

        #Filter out all the already scraped chapters unless we doing a full update
        if full_update is True :
            missing_chapters = canon_descents
        else:
            missing_chapters = list( set(canon_descents) - set(chapters.keys()) )
    else:
        #Use the list of recent chapters instead
        missing_chapters = new_recent_chapters

    #Actually scrape the chapters
    for descent, chapter in get_chapters(story_id, missing_chapters, threads_per_batch=threads_per_batch):
        if issubclass(type(chapter),Exception):
            error_chapters[descent] = chapter
            print('# {}: Warning - error with chapter {}'.format(story_id, descent))
        else:
            #update or create if not exists
            #TODO actually compare dates to use the one with the most recent date since that should be accurate (since the auto date does 12:00am)
            if descent in chapters: 
                chapters[descent].update( chapter.to_dict(skip = ['created']) )
            else: 
                chapters[descent] = chapter.to_dict()

    #Update dates from the recent items
    for descent, recent in recents.items():
        if (descent in chapters):
            chapters[descent]['created'] = recent

    #update the last_full_update field
    #if not already exist OR we're doing full update
    #Also if theres no errors
    if not os.path.exists(story_root + "story.json") or full_update is True:
        if len(error_chapters) == 0:
            temp_info = info._asdict()
            temp_info['last_full_update'] = info.modified
            info = StoryInfo(**temp_info)

    #TODO run a sanity check that each chapter has a matching choice above it, in case of edits (happens)

    story = {
        'info': info._asdict(),
        #chapters end up being not sorted
        'chapters': chapters
    }

    if not os.path.exists(story_root):
        os.makedirs(story_root)

    with open(story_root + 'story.json','w',encoding='utf-8') as o:
        o.write(dumps(story, indent=4, sort_keys=True, separators=(',',':')))

    if session.index_html_generation is True:
        with open(story_root + 'index.html','w',encoding='utf-8') as o:
            o.write(formatIndex(dumps(story, indent=0, sort_keys=True, separators=(',',':'))))

    if len(error_chapters) > 0:
        print('# {}: Finished with {} errors. Try again. If problem persists contact the developer.'.format(story_id,len(error_chapters)))
        return False
    else:
        print('# {}: Finished!'.format(story_id))
        return True

def get_chapters(story_id,chapter_suffixes,threads_per_batch=10):
    start_time = time.time()

    if len(chapter_suffixes) == 0:
        return
    total_num_chapterse = len(chapter_suffixes)
    chapter_prefix = "https://www.writing.com/main/interact/item_id/" + story_id + "/map/"
    
    chapters = {} # map of {chapter descent : string -> ChapterInfo} for chapters we've downloaded.

    #  while some chapters are not yet acquired,
    #  run a batch of threads for X of missing chapters and wait for them all to either get or fail.
    #  you will need a way of discriminating between landing on the "UNAVAILABLE" page and encountering
    #  a real error.
    #  for fun print num of successes for each batch.

    # TODO lower the number of chapters and speed when failing a lot, there seems to be times when the entire batch fails for 10 minutes straight
        
    class ChapterScraper(threading.Thread):
        def __init__(self,chapter_suffix):
            self.chapter_suffix = chapter_suffix
            threading.Thread.__init__(self)

        def run(self):
            try:
                chapter = get_chapter(chapter_prefix + str(self.chapter_suffix))
            except (requests.exceptions.ConnectionError, ServerRefusal) as e:
                return
            except Exception as e:
                print(traceback.format_exc())
                # Unknown error. Let the caller deal with it.
                chapter = e
               
            self.chapter = chapter

    threads = []
    fails = 0
    while chapter_suffixes != [] or threads != []:
        to_add = threads_per_batch - len(threads) 
        next_suffixes = chapter_suffixes[:to_add]
        chapter_suffixes = chapter_suffixes[to_add:]
        
        for chapter_suffix in next_suffixes:
            thread = ChapterScraper(chapter_suffix)
            threads.append(thread)
            thread.start()

        for thread in threads:
            if not thread.is_alive():
                if hasattr(thread, 'chapter'):
                    chapters[thread.chapter_suffix] = thread.chapter
                else:
                    chapter_suffixes.append(thread.chapter_suffix)
                    fails = fails + 1
                threads.remove(thread)

        for descent, chapter in chapters.items():
            yield descent, chapter
        chapters.clear()

        time.sleep(1)

        print('# {}: {}/{} @ {:.2f} chpt/s, fail {:.2f} chpts/s '.format(
            story_id,
            total_num_chapterse - len(chapter_suffixes) - len(threads),
            total_num_chapterse,
            (total_num_chapterse - len(chapter_suffixes) - len(threads)) / (time.time() - start_time),
            fails / (time.time() - start_time)

        ))
