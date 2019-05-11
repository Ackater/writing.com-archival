from urllib import request
import json, re, os, mechanicalsoup
from datetime import datetime
from defs import ChapterInfo, StoryInfo, ServerRefusal
import time

import lxml
from lxml import html

#logs in or reloads cookies upon import
from session import get_page
from session import browser

###   XPATHS AND REGEXPS   ###
#note that these return [] when a match fails

#For a chapter page
#   Really important note here. If the chapter's descent is '1' or '0' (it is the first chapter), you must format these chapter xpaths with '1'. else, format them with '0'.
#   This is because the first chapter doesn't have the additional div element before all content announcing which choice you just took.

chapter_title_xp                = ".//*[@class='shadowBox']/table/tr[1]/td[@class='norm']/table/tr/td[@class='norm']/div[2]/div[2-{}]/span[1]/big/big/b/text()"
chapter_content_xp              = ".//div[@class='KonaBody']"
chapter_member_name_xp          = "//a[starts-with(@title, 'Username:')]"
chapter_choices_xp              = ".//div[@class='shadowBox']/table/tr[1]/td[@class='norm']/table/tr/td[@class='norm']/div[2]/div/table/tr/td[@class='norm']/div/div[1]//a"

#For a story page
#....Note: if the story has an award banner, format with '1'. else, format with '0'.
story_title_xp             = ".//*[@id='Content_Column_Inner']/div[4]/table/tr/td[2]/div[2+{}]/a/text()"
story_author_name_xp       = "//a[starts-with(@title, 'Username:')]/text()"
story_author_id_xp         = ".//*[@id='Content_Column_Inner']/div[4]/table/tr/td[2]/div[4+{}]/a[1]"
story_description_xp       = ".//*[@id='Content_Column_Inner']/div[6]/div[2]//td"
story_brief_description_xp = ".//*[@id='Content_Column_Inner']/div[4]/table/tr/td[2]/div[6+{}]/big/text()"

#For an outline
outline_chapters_xpath = ".//*[@id='Content_Column_Inner']/div[6]/div[2]/pre//a"

#For the heavy server message
refusal_text_substring = "Please try again in a few minutes".lower()
        
#For a search page
search_results_xp=".//*[@id='Content_Column_Inner']/div[6]/font/div/div"
search_pages_dropdown_xp = ".//*[@id='pageVal1']"

def assertNotServerRefusal(page):
    try:
        if page.text_content().lower().find(refusal_text_substring) >= 0:
            raise ServerRefusal('Heavy Server Volume')
    except UnicodeDecodeError:
        #If we have a unicode decoding error assume it's not a refusal page :P
        return False
        
''' takes a chapter page url and returns a ChapterInfo. '''
def get_chapter(url):
    chapter = get_page(url)
    
    #Did we hit a "heavy server volume" error?
    assertNotServerRefusal(chapter)

    data = ChapterInfo()

    suff = url[url.rfind('/')+1:]
    if suff == '1' or suff == '0':
        xpathformat='1'
    else:
        xpathformat='0'
    
    def xpath(path):
        return chapter.xpath(path.format(xpathformat))

    #Title
    data.title = xpath(chapter_title_xp)[0]

    #Chapter content
    data.content = html.tostring(xpath(chapter_content_xp)[0], encoding = "unicode", method="html")


    #Gives 3 results if member isn't deleted, else 1
    #First one is interactive's creator
    #Second is the chapter's author
    #3rd is the chapter's author again but in the copyright link
    author_name = xpath(chapter_member_name_xp)
    
    if (len(author_name) is 1):
        data.is_author_past = True
    else:
        data.author_name = author_name[1].text_content()
        #Grab the title, split by new line, and cut off 'Username: ' which is 10 characters
        data.author_id = author_name[1].attrib['title'].split("\n")[0][10:]

    #Choices
    choices = xpath(chapter_choices_xp)
    for choice in choices:
        data.choices.append(choice.text_content())

    return data

''' takes a story id and returns two lists [str1 str2 ...] where stri of the first list is an existing chapter descent in the story and stri of the second list is that chapter's title. sorry this is inconsistent with the other funcs...'''
def get_chapter_list(story_id):
    url = "http://www.writing.com/main/interact/item_id/" + story_id + "/action/outline"
    outline = get_page(url)

    #Did we hit a "heavy server volume" error?
    assertNotServerRefusal(outline)

    #Decided to re-write this because I had no clue what it was doing before.
    descents = []
    names = []
    outline_links = outline.xpath(outline_chapters_xpath)


    #Links default to https now, but I'm too lazy to change it everywhere, so gonna pull the URL and find the last / to cut off the
    url_cutoff = outline_links[0].attrib['href'].rfind("/") + 1
    
    for a_element in outline_links:
        link = a_element.attrib['href'][url_cutoff:]
        descents.append(link)
        names.append(a_element.text_content())

    return descents, names

''' takes a link to a story landing page and returns a StoryInfo. '''
def get_story_info(url,award_banner=False):
    story = get_page(url)
    data = StoryInfo()

    assertNotServerRefusal(story)

    formatter = ""
    if award_banner:
        formatter = "1"
    else:
        formatter = "0"
        
    def xpath(path):
        return story.xpath(path.format(formatter))

    try:
        #pretty title
        data.pretty_title = xpath(story_title_xp)[0]

        #author id
        authorlink = xpath(story_author_id_xp)[0].attrib['href']
        data.author_id = authorlink[authorlink.rfind('/')+1:]

        data.author_name = xpath(story_author_name_xp)[0]

        #description
        data.description = html.tostring(xpath(story_description_xp)[0], encoding="unicode", with_tail=False)

        #brief description
        data.brief_description = xpath(story_brief_description_xp)[0]

        #image url
        data.image_url = xpath('//meta[@property="og:image"]')[0].attrib["content"]

    except Exception as e:
        if award_banner:
            raise e
        else:
            return get_story_info(url,True)

    return data


''' generator that yields the url of every page of the search, given the url for the first (or ith) page. '''
def all_search_urls(search_url):
    search = get_page(search_url)
    dropdown = search.xpath(search_pages_dropdown_xp)[0]
    for o in dropdown.value_options:
        u = re.sub(r'&page=(\d+)','&page=' + o, search_url)
        u= re.sub(r'&resort_page=(\d+)','&resort_page=' + str(int(o)-1),u)
        yield u

''' takes a search page element tree and returns all INTERACTIVE item_ids listed '''
def get_search_page_interactive_ids(search):
    assertNotServerRefusal(search)
    listings = search.xpath(search_results_xp)[0]
    items = []
    for l in listings.iterchildren():
        #I can only do interactive stories!
        items.append(re.findall(r"interact/item_id/(.+?)'" , list(l.getchildren())[0].attrib['oncontextmenu'])[0])
    return items

''' returns a list of all interactive ids for every result in this search page and all subsequent ones. '''
def get_search_ids(search_url):
    urls = list(all_search_urls(search_url))
    for idx,u in enumerate(urls):
        print('# Gathering ids from page {}/{}'.format(idx+1,len(urls)))
        ids = get_search_page_interactive_ids(get_page(u))
        for id in ids:
            yield id
    
