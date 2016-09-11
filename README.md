# writing.com-archival
This is a Python3 utility for archiving interactive stories from [writing.com](http://www.writing.com/).

This is not finished yet, but basic functionality is working.

To use:

```
$ cd <path-to-source>
$ python3
>> from archiver import archive
>> archive('<story_id>')
```

This will download every chapter from that story into `./archive/<story_id>/` as a set of browsable html files. If you run the command again, it will download any new chapters.

The 'archive' command also returns a map of chapters it could not download. The map is structured {string -> Exception} where string is the chapter descent string (e.g., '111221312') which uniquely designates a chapter, and Exception is the exception the archiver encountered. Some exceptions will happen no matter how many times you re-run `archive`. Some won't.

You will be asked to enter your login credentials to the site on your first use. Don't worry, it doesn't have to keep a record of your password.

## dependencies

Python3 and the packages `mechanicalsoup` and `jinja2`. You will need to `pip install` them.
