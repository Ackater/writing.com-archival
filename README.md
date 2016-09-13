# writing.com-archival
This is a Python3 utility for archiving interactive stories from [writing.com](http://www.writing.com/).

Archiving a story will download every chapter from that story into `./archive/<story_id>/` as a set of browsable html files which you can open in your browser. Updating a story downloads any new chapters into the archive.

Usage:

```
$ cd <path-to-source> 
$ chmod +x run.py                          # If the following commands do not work
$ ./run.py get <id1> <id2>...              # Downloads or updates interactives with item_ids <id1>, <id2>...
$ ./run.py get_search "<url1>" "<url2>"... # Downloads every interactive in these search results. See note below.
$ ./run.py update                          # Update existing archives
```

### Item_id?

The item_id for a story is in its url: `http://www.writing.com/main/interact/item_id/$(THIS_IS_THE_ITEM_ID)/map/14411122`

### get_search

To get the proper URL, first perform a search on writing.com. Then click the magnifying glass icon just above the results to redo the search. Now your URL is in the correct form for get_search. Don't forget to quote it with "".

### Your first use

You will be asked to enter your login credentials to writing.com on your first use. This is because writing.com requires a logged-in session to access interactive chapters. This doesn't have to keep a record of your password, but session cookies will be saved.

### Dependencies

Python3 and the packages `mechanicalsoup` and `jinja2`. You will need to `pip install` them.
