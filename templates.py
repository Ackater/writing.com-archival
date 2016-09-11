from jinja2 import Template
from defs import ChapterInfo, StoryInfo
from datetime import datetime
import re

def formatChapter(chapterInfo, descent,existingdescents):
    chapterInfo.content = re.sub('\r\n','<br>',chapterInfo.content)
    previouschapter = descent[:-1]

    #Jinja doesn't support 'in' in if statements
    existsdescentfor = list(range(1+len(chapterInfo.choices)))
    for i in range(len(chapterInfo.choices)):
        existsdescentfor[i] = (descent + str(i+1)) in existingdescents

    emptychoices = chapterInfo.choices == []
        
    template = Template(
    """ 
    <!DOCTYPE html>
    <html>
        <title> {{ chapterInfo.title }} </title>
        <style>
                    body {
                            background: black;
                    }
                    .content {
                            width: 60%;
                            margin: 0 auto;
                            padding: 10px 10px;
                            background: darkgray;
                    }
                    .content ul {
                            list-style: none;
                    }
                    h2 {
                            text-align: right;
                            font-size: 1em;
                    }
        </style>
        <body>
            <div class="content">
                <h1> {{ chapterInfo.title }} </h1>
                <div>
                        {% if previouschapter != '' %}
                                <a href="{{ previouschapter +".html"}}">Go back</a>
                        {% endif %}
                <div>
                <p class="author"> By: <a href = "http://www.writing.com/main/view_item/action/show_chapters/user_id/{{ chapterInfo.author_id }}"> {{chapterInfo.author_id}} </a></p>
                <p> {{ chapterInfo.content }} </p>
                {% if emptychoices %}
                    <p><b> The End. </b></p>
                {% else %}
                    <p><b> Your choices: </b></p>
                    <ol>
                        {% for choice in chapterInfo.choices %}
                            {% set choicedescent = descent + loop.index|string + ".html" %}
                            {% if existingdescents[loop.index-1] %}
                                <li> <b><a href="{{ choicedescent }}">{{choice}}</a></b></li>
                            {% else %}
                                <li> {{ choice }}</li>
                            {% endif %}
                        {% endfor %}
                    </ol>
                {% endif %}
            <h2>Retrieved {{ date }}<h3>
            </div>
        </body>
    </html>
    """)

    return template.render(emptychoices=emptychoices,existingdescents=existsdescentfor,previouschapter=previouschapter,chapterInfo=chapterInfo,descent=descent,date="{:%B %d, %Y}".format(datetime.now()))

def formatIntro(storyInfo):
    template = Template(
    """ 
    <!DOCTYPE html>
    <html>
        <title> {{ storyInfo.pretty_title }} </title>
        <style>
                    body {
                            background: black;
                    }
                    .content {
                            width: 60%;
                            margin: 0 auto;
                            padding: 10px 10px;
                            background: darkgray;
                    }
                    .content ul {
                            list-style: none;
                    }
        </style>
        <body>
            <div class="content">
                <h1> {{ storyInfo.pretty_title }} </h1>
                <p><i> {{ storyInfo.brief_description }} </i></p>
                <p class="author"> By: <a href = "http://www.writing.com/main/view_item/action/show_chapters/user_id/{{ storyInfo.author_id }}"> {{storyInfo.author_id}} </a></p>
                <p> {{ storyInfo.description }} </p>
                <a href = "1.html">Enter the story</a><br/>
                <a href = "outline.html">View all chapters</a>
            </div>
        </body>
    </html>
    """)
    return template.render(storyInfo=storyInfo)

''' imput: equal len lists of strings for chapter descent strings and associated chapter names'''
def formatOutline(storyTitle, descents,names):
    template = Template(
    """ 
    <!DOCTYPE html>
    <html>
        <title> {{ title }} </title>
        <style>
                    body {
                            background: black;
                    }
                    .content {
                            width: 60%;
                            margin: 0 auto;
                            padding: 10px 10px;
                            background: darkgray;
                    }
                    .content ul {
                            list-style: none;
                    }
        </style>
        <body>
            <div class="content">
                <h1> {{ title }} </h1>
                <ul>
                    {% for i in num %}
                    <li> <a href="{{ descents[i] + ".html"}}">{{ descents[i] + "# " + names[i]}}</a></li>
                    {% endfor %}
                </ul>
            </div>
        </body>
    </html>
    """)

    return template.render(num=range(len(names)),names=names,descents=descents,title=storyTitle)

