def formatIndex(info):
    with open('templates/index.html', 'r') as file:
        return file.read().replace('{{ story_info }}', info)

