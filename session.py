from urllib import request
import json, re, os, mechanicalsoup
from datetime import datetime
from getch import getch
import lxml
from lxml import html

__logged_in__ = False
browser = mechanicalsoup.Browser(soup_config={"features":"lxml"})

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
        print("Reloading session.")
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
    while response is '':
        print("[y/n]:")
        key = getch()
        if key is 'y' or key is 'n':
            response = key
        else:
            print("You must type either y or n.")
            
    return response is 'y'
    
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
    login_p = browser.get('http://www.writing.com/main/login.php')
    login_form = login_p.soup.find("form",method="post",action="http://www.Writing.Com/main/login.php")
    username_form = login_form.find("input",type="text")
    password_form = login_form.find("input",type="password")

    sn = ""
    pw = ""
    if os.path.isfile('credentials'):
        credentials = open("credentials")
        sn,pw = credentials.readline().split()
    else:
        print("Enter your username and password to login.")

        sn = __prompt_ensure("Enter your username: ")
        pw = __prompt_ensure("Enter your password: ")

        print("Do you want to save your username and password to \"credentials\"?")
        print("(If you delete it, you'll be asked to input your creds again if the session expires.)")

        saves_credentials = __prompt_yn()
        print("OK.")
        
        if saves_credentials:
            creds = open('credentials','w')
            creds.write(sn + " " + pw)
            creds.flush()
            creds.close()
    
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
    response = browser.get(url)

    # I'm 12 and what is encoding
    try:
        tree = html.fromstring(response.content.decode('utf-8'))
    except:
        tree = html.fromstring(response.content.decode('latin-1'))
        
    return tree
    
