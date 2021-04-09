from urllib import request
import json, re, os, mechanicalsoup
from datetime import datetime
import lxml
from lxml import html
import requests
from defs import ServerRefusal
from urllib.parse import urlparse, parse_qs
from bs4 import UnicodeDammit
import yaml

__logged_in__ = False
username = None
password = None
name_in_archive = False
index_html_generation = False
premium = False

browser = mechanicalsoup.Browser(
    #soup_config={"features":"html.parser"}, Maybe don't use the soup TODO try this with those bad outlines
    user_agent="Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"
)

with open(r'config.yaml') as file:
    config_yaml = yaml.load(file, Loader=yaml.FullLoader)
    username = config_yaml['username']
    password = config_yaml['password']
    name_in_archive = config_yaml['name_in_archive']
    index_html_generation = config_yaml['index_html_generation']
    #premium = config_yaml['premium']


'''Saves session cookies (run once you have a logged-in account)'''
def __save_session():
    print("Saving session.")
    #Dump the cookies json as a dictionary
    dump = json.dumps(browser.session.cookies.get_dict())
    f = open('session','w+')
    f.writelines(dump)
    f.close()

'''Attempts to resume the session cookies from before. If no cookies exist, log in.'''
def __reload_session():
    if os.path.isfile('session'):
        #Open session file
        f = open('session','r+')
        pmud = json.loads(f.readline())
        #Iteratie the K/V pairs back into cookies (will overwrite)
        for key,value in pmud.items():
            browser.session.cookies.set(key,value)
        f.close()

        #TODO can maybe check if this comes with a login form
        #Disable the dynamic interactives just in case
        browser.get("https://www.writing.com/main/my_account?action=set_q_i2&ajax=setDynaOffOn&val=-1")
    else:
        __log_in()

'''Logs in to writing.com and saves the session cookies.'''
def __log_in():
    global username, password, browser
    print("Logging in...")

    #clear browser
    browser = mechanicalsoup.Browser(
        user_agent="Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"
    )

    login_p = browser.get('https://www.writing.com/main/login.php')
    login_form = login_p.soup.find("form",method="post",action="https://www.Writing.Com/main/login.php")
    username_form = login_form.find("input",type="text")
    password_form = login_form.find("input",type="password")

    username_form['value'] = username
    password_form['value'] = password
    landing_p = browser.submit(login_form,login_p.url)

    if landing_p.soup.find("form",method="post",action="https://www.Writing.Com/main/login.php") is not None:
        print("Error logging in. Invalid credientals?")
        return

    print("Submitted login form.")

    #Disable the dynamic interactives just in case
    browser.get("https://www.writing.com/main/my_account?action=set_q_i2&ajax=setDynaOffOn&val=-1")

    #Assume login successful.
    __save_session()

'''Reload the session upon import!'''
__reload_session()

'''A copy of get_page without retrying and without utf-8 decoding, since we're only interested in links anyways. Required because the search page will break apart multibyte utf-8 codes in the middle'''
def get_page_search(url):
    response = browser.get(url)
    tree = html.fromstring(response.content.decode("latin-1"))
    return tree

''' Uses the soup browser with logged-in session to return an xpathable tree.'''
def get_page(url, encoding="utf-8"):
    #Try 5 times, the requests can fail with requests.exceptions.ConnectionError sometimes
    for tries in range(5):
        try:
            response = browser.get(url)

            #If not logged in
            
            #TODO Lock this? Multiple scrapers will trigger this at a time, and all try to login
            if response.soup.find("form",method="post",action="https://www.Writing.Com/main/login.php") is not None:
                #Prompt for login and try again
                __log_in()
                continue

            break
        except requests.exceptions.ConnectionError as e:
            pass
    
    if (tries == 4):
        raise ServerRefusal('Could not connect to server after 5 attempts')

    #with open('chapter.html','wb') as o:
    #    o.write(response.content)

    if encoding == "utf-8":
        new_doc = detwingle(response.content)
        tree = html.fromstring(new_doc.decode("utf-8"))
    else: 
        tree = html.fromstring(new_doc.decode(encoding))

    #Handle all of writing.com's redirect links here
    links = tree.xpath("//a[starts-with(@href, 'https://www.Writing.Com/main/redirect')]")
    for link in links:
        parse = urlparse(link.attrib['href'])
        query = parse_qs(parse.query)
        
        link.attrib['href'] = query['redirect_url'][0]
    
    return tree

#Fixing another BS4 bug, it's got the wrong character for á
#https://groups.google.com/g/beautifulsoup/c/H5E660vcYl4/m/UwXgO1rBHwAJ
UnicodeDammit.WINDOWS_1252_TO_UTF8[0xe1] = b'\xc3\xa1'

#Taken from BS4
#Hacked a bit to handle codes like \xe9 "é" which would triggle multi-byte stuff but wasn't actually by checking the rest of the bytes
def detwingle(in_bytes):
    byte_chunks = []
    chunk_start = 0
    pos = 0

    while pos < len(in_bytes):
        byte = in_bytes[pos]
        
        actually_unicode = False
        if (byte >= UnicodeDammit.FIRST_MULTIBYTE_MARKER
            and byte <= UnicodeDammit.LAST_MULTIBYTE_MARKER):
            # This is the start of a UTF-8 multibyte character. Skip
            # to the end.
            for start, end, size in UnicodeDammit.MULTIBYTE_MARKERS_AND_SIZES:
                if byte >= start and byte <= end:
                    
                    #My hacks: a check to make sure the next bytes are properly utf multichar bytes
                    actually_unicode = True
                    for i in range(1, size):
                        if not (in_bytes[pos + i] >= 0x80 and in_bytes[pos + i] < 0xc0):
                            actually_unicode = False
                            break

                    #test #2, actually try to decode it
                    if actually_unicode:
                        pos += size
                        break

        if actually_unicode:
            continue
        if byte >= 0x80 and byte in UnicodeDammit.WINDOWS_1252_TO_UTF8:
            # We found a Windows-1252 character!
            # Save the string up to this point as a chunk.
            byte_chunks.append(in_bytes[chunk_start:pos])

            # Now translate the Windows-1252 character into UTF-8
            # and add it as another, one-byte chunk.
            byte_chunks.append(UnicodeDammit.WINDOWS_1252_TO_UTF8[byte])
            pos += 1
            chunk_start = pos
        else:
            # Go on to the next character.
            pos += 1
    if chunk_start == 0:
        # The string is unchanged.
        return in_bytes
    else:
        # Store the final chunk.
        byte_chunks.append(in_bytes[chunk_start:])
    return b''.join(byte_chunks)
