from urllib import request, parse
import json, re, os, mechanicalsoup
from datetime import datetime, timezone, timedelta
from defs import Chapter, StoryInfo, ServerRefusal
from dateutil import tz

import time

import lxml
from lxml import html

#logs in or reloads cookies upon import
from session import get_page, get_page_search
from session import browser

###   XPATHS AND REGEXPS   ###
#note that these return [] when a match fails

#For a chapter page
#   Really important note here. If the chapter's descent is '1' or '0' (it is the first chapter), you must format these chapter xpaths with '1'. else, format them with '0'.
#   This is because the first chapter doesn't have the additional div element before all content announcing which choice you just took.

chapter_title_xp                = "//span[starts-with(@title, 'Created')]/h2/text()"
chapter_content_xp              = "//div[@style='padding:25px 6px 20px 11px;min-width:482px;']/div"
chapter_author_name_xp          = "(//a[starts-with(@title, 'Username:')])[2]/text()"
chapter_author_name_xp_2        = '//i[starts-with(text(), "by")]/text()' #deleted authors?
chapter_author_link_xp          = '(//a[@class="imgLink imgPortLink"])[2]/@href' 
chapter_choices_xp              = "//div[@id='end_choices']/parent::*//a"
chapter_id_xp                   = '//*[text()="ID #"]/b/text()' #https://www.writing.com/main/interact/cid/#### it's a link on member accounts
chapter_created_date_xp         = "//span[starts-with(@title, 'Created')]/@title"

#For a story page
story_title_xp              =   "//a[contains(@class, 'proll')]/text()"
story_author_name_xp        =   "(//a[starts-with(@title, 'Username:')])[1]/text()"
story_author_link_xp        =   '(//a[@class="imgLink imgPortLink"])[1]/@href'
story_description_xp        =   "//*[@id='Content_Column_Inside']/div[6]/div[2]//td"
story_brief_description_xp  =   "//big/text()"
story_image_url_xp          =   "//meta[@property='og:image']/@content"
story_id_xp                 =   "//span[@class='selectAll']/text()"
story_rating_xp             =   '//div[starts-with(text(),"Rated: ")]/descendant-or-self::*/text()'
story_created_date          =   '//div[starts-with(text(),"Created")]/descendant-or-self::*/text()'
story_modified_date         =   '//div[starts-with(text(),"Modified")]/descendant-or-self::*/text()'
story_size                  =   '//div[starts-with(text(),"Size")]/descendant-or-self::*/text()'

recent_elements_xp          =   "//div[@class='mainLineBorderBottom'][@style='relative;padding:10px;']"
recent_date_xp              =   ".//div[@style='float:right;padding:0px 0px 0px 5px;']/text()"
recent_link_xp              =   ".//div[@align='left']/b/a/@href"

#For an outline
outline_chapters_xpath = "//*[@id='Content_Column_Inside']/div[6]/div[2]/pre//a"

redirect_links_xpath = "//a[starts-with(@href, 'https://www.Writing.Com/main/redirect')]"

#For the heavy server message
refusal_text_substring = "or try again soon".lower()

#A different error message that shows up once in a while
temporary_unavailable_substring = "The site is temporarily unavailable.".lower()
temporary_unavailable2_substring = "Database Temporarily Too Busy".lower()
#A less nuclear option than above. Not sure if the UnicodeDecodeError was necessary
def hasServerRefusal(page):
    if len(page.text_content()) == 0:
        return True
    if page.text_content().lower().find(refusal_text_substring) >= 0:
        return True
    if page.text_content().lower().find(temporary_unavailable_substring) >= 0:
        return True
    if page.text_content().lower().find(temporary_unavailable2_substring) >= 0:
        return True
    return False

#Parse full date stamps like Created: February 30th, 2011 at 6:00am
#Used in details of the whole interactive
def parse_date_time(date):
    date = re.sub(r"(Modified:|Created:) ", "", date)
    date = re.sub(r"(st|nd|rd|th),", ",", date)
    timedate = datetime.strptime(date, "%B %d, %Y at %I:%M%p")

    timedate = timedate.replace(tzinfo=tz.gettz('America/New_York'))
    return int(timedate.timestamp())

#Parse shorthand dates like Oct 21, 2020 8:03 pm
def parse_short_date_time(date):
    timedate = datetime.strptime(date, "%b %d, %Y %I:%M %p")

    timedate = timedate.replace(tzinfo=tz.gettz('America/New_York'))
    return int(timedate.timestamp())

def parse_date(date):
    timedate = datetime.strptime(date, "Created: %m-%d-%Y")

    timedate = timedate.replace(tzinfo=tz.gettz('America/New_York'))
    return int(timedate.timestamp())

def parse_date_element(ele):
    # new format where the 'am/pm' designation is in a sub-element
    return parse_date_time(ele.text + ele[0].text)

''' takes a link to a story landing page and returns a StoryInfo. '''
def get_story_info(story_id):
    url = "https://www.writing.com/main/interact/item_id/" + story_id
    page = get_page(url)
    
    while hasServerRefusal(page):
        page = get_page(url)

    #Private item can't access, can not scrape
    if page.text_content().lower().find('is a private item.') >= 0:
        return -1

    #Deleted item can't acccess, can not scrape
    if page.text_content().lower().find("wasn't found within writing.com") >= 0:
        return False

    #Not an interactive
    if page.text_content().lower().find("list_items/item_type/interactive-stories") == 0:
        return -2

    try:
        story_info = StoryInfo(
            id = int(page.xpath(story_id_xp)[0]),
            pretty_title = page.xpath(story_title_xp)[0],
            author_id = page.xpath(story_author_link_xp)[0][len("https://www.Writing.Com/main/portfolio/view/"):],
            author_name = page.xpath(story_author_name_xp)[0],
            description = html.tostring(page.xpath(story_description_xp)[0], encoding="unicode", with_tail=False),
            brief_description = page.xpath(story_brief_description_xp)[0],
            created = parse_date_time(page.xpath(story_created_date)[0] + page.xpath(story_created_date)[1]),
            modified = parse_date_time(page.xpath(story_modified_date)[0] + page.xpath(story_modified_date)[1]),
            image_url = page.xpath(story_image_url_xp)[0],
            last_full_update = None
        )

    except Exception as e:
        raise e

    return story_info

def get_chapter(url):
    page = get_page(url)
    
    if hasServerRefusal(page):
        raise ServerRefusal('Heavy Server Volume')

    #Error premium mode to inline chapters is on. Disable it and try again
    if len(page.xpath(chapter_content_xp)) == 0:
        get_page("https://www.writing.com/main/my_account?action=set_q_i2&ajax=setDynaOffOn&val=-1")
        page = get_page(url)
        if hasServerRefusal(page):
            raise ServerRefusal('Heavy Server Volume')

    try:
        choices = []
        choice_elements = page.xpath(chapter_choices_xp)
        for choice in choice_elements:
            choices.append(choice.text_content())
        if len(choice_elements) == 0:
            choices = None

        if len(page.xpath(chapter_author_link_xp)) != 0:
            author_id = page.xpath(chapter_author_link_xp)[0][len("https://www.Writing.Com/main/portfolio/view/"):]
        else:
            author_id = None

        if len(page.xpath(chapter_author_name_xp)) != 0:
            author_name = page.xpath(chapter_author_name_xp)[0]
        else: 
            if len(page.xpath(chapter_author_name_xp_2)) != 0:
                author_name = page.xpath(chapter_author_name_xp_2)[0][3:].strip()

                if author_name == "":
                    author_name = None
            else:
                author_name = None

        if len(page.xpath(chapter_title_xp)) != 0:
            title = page.xpath(chapter_title_xp)[0]
        else:
            title = None

        chapter = Chapter(
            title = title,
            id = int(page.xpath(chapter_id_xp)[0]),
            content = html.tostring(page.xpath(chapter_content_xp)[0], encoding="unicode"),
            author_id = author_id,
            author_name = author_name,
            choices = choices,
            created = parse_date(page.xpath(chapter_created_date_xp)[0]),
        )
    except Exception as e:
        print ("Scraping error at " + url)
        with open('scrapingerror.html','w',encoding='utf-8') as o:
            o.write(html.tostring(page))
        raise e

    return chapter

def get_recent_chapters(story_id):
    url = "https://www.writing.com/main/interactive-story/item_id/" + story_id + "/action/recent_chapters"
    page = get_page(url)
    
    while hasServerRefusal(page):
        page = get_page(url)


    output = {}
    recents = page.xpath(recent_elements_xp)

    url_cutoff = page.xpath(recent_link_xp)[0].rfind("/") + 1
    for recent in recents:
        #the descent
        link = recent.xpath(recent_link_xp)[0][url_cutoff:]
        date = parse_short_date_time(" ".join(recent.xpath(recent_date_xp)))
        output[link] = date
    
    return output

def get_outline(story_id):
    """Gets a list of all possible chapters for scraping"""
    url = "https://www.writing.com/main/interact/item_id/" + story_id + "/action/outline"
    page = get_page(url)
    
    while hasServerRefusal(page):
        page = get_page(url)

    descents = []
    outline_links = page.xpath(outline_chapters_xpath)

    #Pull the URL and find the last / to cut off the preceeding URL
    url_cutoff = outline_links[0].attrib['href'].rfind("/") + 1
    
    for a_element in outline_links:
        link = a_element.attrib['href'][url_cutoff:]
        descents.append(link)

    return descents


#TODO return dates too, so we can more easily get last modified dates to compare
def get_all_interactives_list(pages = -1, start_page = 1, oldest_first = False, search_string = None):
    search_results_xp = "//div[@id='Content_Column_Inside']/div[@class='norm']//a[starts-with(@href, 'https://www.Writing.Com/main/interactive-story/')]"
    #search_dates = "//div[@id='Content_Column_Inner']/div[@class='norm']//div[starts-with(text(), 'Updated')]"

    search_url = "https://www.writing.com/main/search.php?"
    search_variables = {
        "action": "change_page",
        "ps_type": "5000",
        "ps" : 1,
        "sort_by": "item_modified_time DESC",
        "sort_by_last": "item_modified_time DESC",
        "page": 1
    }

    if search_string is not None:
        search_variables['search_for'] = search_string
    
    if oldest_first:
        search_variables['sort_by'] = 'item_modified_time'
        search_variables['sort_by_last'] = 'item_modified_time'

    current_page = start_page

    results = -1
    interactives = []
    dates = []
    url_cutoff = None
    while results != 0:
        print ("Getting page " + str(current_page))

        search_variables['page'] = current_page
        url = search_url + parse.urlencode(search_variables)
        page = get_page_search(url)

        search_results = page.xpath(search_results_xp)
        if url_cutoff is None:
            #Pull the URL and find the last / to cut off the preceeding URL
            url_cutoff = search_results[0].attrib['href'].rfind("/") + 1

        for interactive_link in search_results:
            interactives.append(
                interactive_link.attrib['href'][url_cutoff:]
            )

        #date_results = page.xpath(search_dates)
        #TODO

        results = len(search_results)
        current_page += 1

        if (pages != -1 and (current_page - start_page) >= pages):
            break

    return interactives
    #with open('everything.txt','w',encoding='utf-8') as o:
    #    for interactive in interactives:
    #        o.write(interactive + "\n")
