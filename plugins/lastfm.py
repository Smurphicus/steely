#!/usr/bin/env python3

import requests
from tinydb import TinyDB, Query
from operator import itemgetter
# from steelybot import config


COMMAND = '.np'
USERDB = TinyDB('../lastfm.json')
USER = Query()


def get_np(user):
    base = "http://ws.audioscrobbler.com/2.0/"
    payload = {'method': 'user.getRecentTracks',
               'user': user,
               'api_key': "f18d9bd2cc53c33d6be50fba1a418b4f",
               # 'api_key': config.LASTFM_API_KEY,
               'limit': '2',
               'format': 'json'}
    response = requests.get(base, params=payload)
    return response.json()["recenttracks"]["track"][0]

def get_playcount(user):
    base = "http://ws.audioscrobbler.com/2.0/"
    payload = {'method': 'user.getInfo',
               'user': user,
               'api_key': "f18d9bd2cc53c33d6be50fba1a418b4f",
               # 'api_key': config.LASTFM_API_KEY,
               'limit': '1',
               'format': 'json'}
    response = requests.get(base, params=payload)
    return response.json()["user"]["playcount"]

def get_tags(artist, track):
    base = "http://ws.audioscrobbler.com/2.0/"
    payload = {'method': 'artist.gettoptags',
               'api_key': config.LASTFM_API_KEY,
               'artist': artist,
               'user': 'alexkraak',
               'format': 'json'}
    response = requests.get(base, params=payload).json()
    top = 0
    try:
        for tag in response['toptags']['tag']:
            if top < 3 and tag['name'] != 'seen live':
                top += 1
                yield tag['name']
    except KeyError:
        yield 'None'

def collage(author_id, user):
    base = "http://www.tapmusic.net/collage.php/"
    payload = {'user': user,
               'type': '1month',
               'size': '3x3',
               'caption': 'true'}
    image_url = requests.get(base, params=payload)
    image = image_url.content
    print(image_url.url)
    image_path = '/tmp/{}.jpg'.format(str(author_id))
    with open(image_path, 'wb') as f:
        f.write(image)
    return image_path

def extract_song(user):
    try:
        response = get_np(user)
    except requests.exceptions.RequestException:
        return 'failed to retrieve now playing information'
    artist = response['artist']['#text']
    song = response['name']
    tags = list(get_tags(artist, song))
    return '{} is playing {} by {}. tags: {}'.format(user, song, artist, tags)


def main(bot, author_id, message, thread_id, thread_type, **kwargs):
    message_split = message.split()
    if not message:
        search = USERDB.search(USER.fb_id == author_id)
        if len(search) != 0:
            lastfm_name = search[0]['lastfm']
            bot.sendMessage(extract_song(lastfm_name),
                            thread_id=thread_id, thread_type=thread_type)
        else:
            bot.sendMessage('include username please or use .np set',
                            thread_id=thread_id, thread_type=thread_type)
        return

    elif message_split[0] == 'set' and len(message_split) == 2:
        if len(USERDB.search(USER.fb_id == author_id)) == 0:
            USERDB.insert({"fb_id": author_id, "lastfm": message_split[1]})
            bot.sendMessage('good egg',
                            thread_id=thread_id, thread_type=thread_type)
        else:
            USERDB.update({"lastfm": message_split[1]},
                          USER.fb_id == author_id)
            bot.sendMessage('updated egg',
                            thread_id=thread_id, thread_type=thread_type)
        return
    elif message_split[0] == 'collage' and len(message_split) == 2:
        bot.sendLocalImage(collage(author_id, message_split[1]),
                           message=None,
                           thread_id=thread_id,
                           thread_type=thread_type)

    elif message_split[0] == 'list' and len(message_split) == 2:
        max_lastfm = max(len(user["lastfm"]) for user in USERDB.all())
        stats = []
        for user in USERDB.all():
            lastfm = user["lastfm"]
            stats.append((lastfm, get_playcount(lastfm)))
        for lastfm, playcount in sorted(stats, key=itemgetter(1), reverse=True):
            print("{:<{max_lastfm}} {:>6,}".format(lastfm, int(playcount), max_lastfm=max_lastfm))

    else:
        bot.sendMessage(extract_song(message),
                        thread_id=thread_id, thread_type=thread_type)
        return
