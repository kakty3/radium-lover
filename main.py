import xml.etree.ElementTree as ET
import urllib2
import time
import webbrowser
import os
# import sys
import pickle
import json
from pync import Notifier

APP_ID = '4786305'
REDIRECT_URI = 'http://demur.in:3423'

def get_vk_token():
    token = load_token_from_file()
    if token is not None:
        return token['access_token']
    token = get_vk_token_object(APP_ID)
    save_token_to_file(token)
    return token['access_token']

def load_token_from_file():
    cache_filename = 'token_cache'
    if not os.path.isfile(cache_filename):
        return None
    with open(cache_filename, 'r') as cache_file:
        token = pickle.load(cache_file)
        return token

def save_token_to_file(token):
    cache_filename = 'token_cache'
    with open(cache_filename, 'w') as cache_file:
        pickle.dump(token, cache_file)

def get_vk_token_object(APP_ID):
    try:
        urllib2.urlopen(REDIRECT_URI)
    except urllib2.URLError:
        print 'Authentication server is not running'
        return None

    request = (
        'https://oauth.vk.com/authorize?'
        'client_id={APP_ID}&'
        'scope={PERMISSIONS}&'
        'redirect_uri={REDIRECT_URI}&'
        'display={DISPLAY}&'
        'v={API_VERSION}&'
        'response_type=code'
    ).format(
        APP_ID=APP_ID,
        PERMISSIONS=8,  # audio
        DISPLAY='page',  # try out other variants
        REDIRECT_URI=REDIRECT_URI,
        API_VERSION=5.28
    )

    webbrowser.open_new(request)

    get_token_string = lambda: urllib2.urlopen(REDIRECT_URI + '/get_token').read()
    token_string = get_token_string()
    while token_string == 'None':
        time.sleep(0.1)
        print '.',
        token_string = get_token_string()
    token_object = json.loads(token_string)
    return token_object

def get_song_name():
    home = os.path.expanduser("~")
    radium_songs_log_filename = os.path.join(home, 'Library/Application Support/Radium/song_history.plist')
    tree = ET.parse(radium_songs_log_filename)
    root = tree.getroot()
    song = root[0][0]
    return song.findall('string')[-1].text.encode('utf-8')

def search_song(search_queue, access_token):
    print('Looking for "{}"'.format(search_queue))
    print '- ' * 30
    search_queue = search_queue.replace(' ', '%20')
    request = ('https://api.vk.com/method/audio.search.xml?'
        'q={search_queue}&'
        'count=5&'
        'access_token={access_token}').format(
        search_queue=search_queue,
        access_token=access_token)
    # print request
    response = urllib2.urlopen(request)
    data = response.read()
    root = ET.fromstring(data)
    if int(root.find('count').text) == 0:
        print 'Nothing found'
        return None, None
    # print root.tag
    for song in root.findall('audio'):
        artist = song.find('artist').text.encode('utf-8')
        title = song.find('title').text.encode('utf-8')
        audio_id = song.find('aid').text
        owner_id = song.find('owner_id').text
        print '  {} - {} [audio_id={}, owner_id={}]'.format(artist, title, audio_id, owner_id)
    print '- ' * 30

    song = root.findall('audio')[0]
    audio_id = song.find('aid').text
    owner_id = song.find('owner_id').text
    return audio_id, owner_id
    # print data

def add_song(audio_id, owner_id, access_token):
    request = ('https://api.vk.com/method/audio.add?'
        'audio_id={audio_id}&'
        'owner_id={owner_id}&'
        'access_token={access_token}'
    ).format(
        audio_id=audio_id,
        owner_id=owner_id,
        access_token=access_token
    )
    response = urllib2.urlopen(request).read()
    if 'response' in json.loads(response):
        print 'Song successfully added.'
        # Notifier('zaebal')
    # print response.read()


if __name__ == '__main__':
    # Notifier.notify('Song was successfully added', title='Title', subtitle='Subtitle', sender='com.catpigstudios.Radium')

    token = get_vk_token()
    # print token
    song_name = get_song_name()
    audio_id, owner_id = search_song(song_name, token)
    # if audio_id is not None:
    #     add_song(audio_id, owner_id, token)
