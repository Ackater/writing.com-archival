from scraper import get_story_info, get_chapter
from defs import ServerRefusal,  StoryInfo
import threading
import time
import requests
import traceback

def get_story_info_safe(story_id):
    try:
        info = get_story_info("https://www.writing.com/main/interact/item_id/" + story_id)
    except ServerRefusal:
        #Just try again after a bit.
        time.sleep(5)
        return get_story_info_safe(story_id)
    return info
        

''' yields a map of {chapter descent string -> ChapterInfo object} by downloading the chapters.
    Note that it's a generator. '''
def get_chapters(story_id,chapter_suffixes,threads_per_batch=5):
    total_num_chapterse = len(chapter_suffixes)
    chapter_prefix = "https://www.writing.com/main/interact/item_id/" + story_id + "/map/"
    
    chapters = {} # map of {chapter descent : string -> ChapterInfo} for chapters we've downloaded.

    #  while some chapters are not yet acquired,
    #  run a batch of threads for X of missing chapters and wait for them all to either get or fail.
    #  you will need a way of discriminating between landing on the "UNAVAILABLE" page and encountering
    #  a real error.
    #  for fun print num of successes for each batch.
    
    lock = threading.Lock()
        
    class ChapterScraper(threading.Thread):
        def __init__(self,chapter_suffix):
            self.chapter_suffix = chapter_suffix
            threading.Thread.__init__(self)

        def run(self):
            try:
                chapter = get_chapter(chapter_prefix + self.chapter_suffix)
            except (requests.exceptions.ConnectionError, ServerRefusal) as e:
                # Wait and we will try this chapter again later.
                time.sleep(5)
                lock.acquire()
                chapter_suffixes.append(self.chapter_suffix) #put the suffix back on the list
                lock.release()
                return
            except Exception as e:
                print(traceback.format_exc())
                # Unknown error. Let the caller deal with it.
                chapter = e
               
            lock.acquire()
            chapters[self.chapter_suffix] = chapter
            lock.release()

    while chapter_suffixes != []:
        next_suffixes = chapter_suffixes[:threads_per_batch]
        chapter_suffixes = chapter_suffixes[threads_per_batch:]
        
        threads = []
        for chapter_suffix in next_suffixes:
            thread = ChapterScraper(chapter_suffix)
            threads.append(thread)
            thread.start()

        for i in range(len(threads)):
            threads[i].join()

        for descent, chapter in chapters.items():
            yield descent, chapter

        chapters = {}
        print('# {}: {}/{}'.format(story_id, total_num_chapterse - len(chapter_suffixes),total_num_chapterse))