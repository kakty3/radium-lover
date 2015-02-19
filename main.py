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
    # TODO: rewrite with json
    print('Looking for "{}"'.format(search_queue))
    print '- ' * 30
    search_queue = search_queue.replace(' ', '%20')
    request = ('https://api.vk.com/method/audio.search?'
        'q={search_queue}&'
        'count=5&'
        'access_token={access_token}').format(
        search_queue=search_queue,
        access_token=access_token)
    # print request
    response = urllib2.urlopen(request)
    json_data = response.read()
    data = json.loads(json_data)
    if not 'response' in data:
        print 'Some error occurred'
        return
    if data['response'][0] == 0:
        # print 'Nothing found'
        return None
    for index, song in enumerate(data['response'][1:]):
        artist = song['artist'].encode('utf-8')
        title = song['title'].encode('utf-8')
        # audio_id = song['aid']
        # owner_id = song['owner_id']
        # print '  {} - {} [audio_id={}, owner_id={}]'.format(artist, title, audio_id, owner_id)
        print '{:2d}. {} - {}'.format(index + 1, artist, title)
    print '- ' * 30

    song = data['response'][1]
    # artist = song['artist'].encode('utf-8')
    # title = song['title'].encode('utf-8')
    # audio_id = song['aid']
    # owner_id = song['owner_id']
    return song


def add_song(audio_id, owner_id, access_token):
    """

    :type audio_id: int
    :type owner_id: int
    :type access_token: unicode
    :return: True if song added, False if error occurred
    :rtype: bool
    """
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
    return 'response' in json.loads(response)


if __name__ == '__main__':
    token = get_vk_token()
    song_name = get_song_name()
    song = search_song(song_name, token)
    if song is not None:
        # song_added = False
        song_added = add_song(song['aid'], song['owner_id'], token)
        if song_added:
            print 'Song successfully added.'
            Notifier.notify('Song was successfully added.',
                            title=song['title'],
                            subtitle='by ' + song['artist'],
                            sender='com.catpigstudios.Radium')
