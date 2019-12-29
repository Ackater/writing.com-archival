from urllib import request
import json, re, os, mechanicalsoup
from datetime import datetime
from getch import getch
import lxml
from lxml import html
import requests
from defs import ServerRefusal

__logged_in__ = False
browser = mechanicalsoup.Browser(
    soup_config={"features":"lxml"},
    user_agent="Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0"
)

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
    else:
        __log_in()

'''prompts y/n. returns bool of == y'''
def __prompt_yn():
    response = ''
    while response == '':
        print("[y/n]:")
        key = getch()
        if key == 'y' or key == 'n':
            response = key
        else:
            print("You must type either y or n.")
            
    return response == 'y'
    
'''Gives a prompt and repeats the answer back.'''
def __prompt_ensure(str):
    ans = input(str)
    print("you typed " + ans + ". is this correct?")
    corr = __prompt_yn()
    if not corr:
        __prompt_ensure(str)
    else:
        return ans

'''Logs in to writing.com and saves the session cookies.'''
def __log_in():
    print("Logging in...")
    login_p = browser.get('https://www.writing.com/main/login.php')
    login_form = login_p.soup.find("form",method="post",action="https://www.Writing.Com/main/login.php")
    username_form = login_form.find("input",type="text")
    password_form = login_form.find("input",type="password")

    sn = ""
    pw = ""
    print("Enter your username and password for writing.com.")

    sn = __prompt_ensure("Enter your username: ")
    pw = __prompt_ensure("Enter your password: ")
    
    username_form['value'] = sn
    password_form['value'] = pw

    landing_p = browser.submit(login_form,login_p.url)
    print("Submitted login form.")

    #Assume login successful.
    __save_session()

'''Reload the session upon import!'''
__reload_session()


''' Uses the soup browser with logged-in session to return an xpathable tree.'''
def get_page(url):
    #Try 5 times, the requests can fail with requests.exceptions.ConnectionError sometimes
    for tries in range(5):
        try:
            response = browser.get(url)
            break
        except requests.exceptions.ConnectionError as e:
            pass
    
    if (tries == 4):
        raise ServerRefusal('Could not connect to server after 5 attempts')

    tree = html.fromstring(response.content.decode('latin-1'))
    return tree
