
# writing.com-archival
This is a Python3 utility for archiving interactive stories from [writing.com](http://www.writing.com/).

Archiving a story will download every chapter from that story into `./archive/<story_id>/` as a set of browsable html files which you can open in your browser. Updating a story downloads any new chapters into the archive.

Command line usage:

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

You will be asked to enter your login credentials to writing.com on your first use. This is because writing.com requires a logged-in session to access interactive chapters. This won't save your password, but session cookies will be saved in a file called `session`. 

### Dependencies

Python3 and the packages `mechanicalsoup`, `jinja2`, and `lxml`. You will need to `pip install` them.

### Troubleshooting

You may encounter errors while trying to download stories. If the error does not crash the utility, I suggest trying to download it again, as some of the errors are transient. But let me know what story/chapter you had trouble with and I'll see what I can do.

If the error does crash the utility, I suggest logging in again. Best case scenario either your login was unsuccesful or writing.com has decided to stop serving your session. Delete `session` (not `session.py`!) and you'll be asked for your credentials again. Note that it won't tell you if the login was successful or not. If it still fails, let me know.
# writing.com-archival with Docker
This utility can also be run in a container. The container handles installing all the required dependencies for running the utility.
## Requirements
### Windows
#### Windows 7 / Windows 8 / Windows 8.1 / Windows 10 Home
- [Docker Toolbox](https://github.com/docker/toolbox/releases)
#### Windows 10 Professional / Windows 10 Enterprise
- [Docker Desktop for Windows](https://hub.docker.com/editions/community/docker-ce-desktop-windows)
- Enable Shared Volumes for Docker Desktop

### MacOS
- [Docker Desktop for MacOS](https://hub.docker.com/editions/community/docker-ce-desktop-mac)
### Linux
- Docker CE
  - [CentOS](https://docs.docker.com/install/linux/docker-ce/centos/)
  - [Debian](https://docs.docker.com/install/linux/docker-ce/debian/)
  - [Fedora](https://docs.docker.com/install/linux/docker-ce/fedora/)
  - [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
- [Docker Compose](https://docs.docker.com/compose/install/#linux)

## How to Use this Image
```bash
$ cd <path-to-source>
$ docker-compose build
$ docker-compose run scraper
# After running the above commands, the command line arguments stay the same.
root@<container-hostname>:/code# ./run.py get <id1> <id2>...              # Downloads or updates interactives with item_ids <id1>, <id2>...
root@<container-hostname>:/code# ./run.py get_search "<url1>" "<url2>"... # Downloads every interactive in these search results. See note below.
root@<container-hostname>:/code# ./run.py update                          # Update existing archives
```
### Command Explanations
`docker-compose build` - This command will use the docker-compose.yml file to build the container defined inside the Dockerfile.
`docker-compose run scraper` - This command will use the docker-compose.yml file to run the scraper container interactively in the current shell session.  
