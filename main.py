#! /usr/bin/env python
#coding: utf-8
import xml.etree.ElementTree as ET
import urllib2
import getpass
import os
from urllib import urlencode
import cStringIO
import pycurl
import re
# import sys
import pickle
import json
from pync import Notifier
import time

APP_ID = '4786305'
SCRIPT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
COOKIE_FILE = os.path.join(SCRIPT_DIRECTORY, 'cookie.txt')
TOKEN_CACHE_FILENAME = os.path.join(SCRIPT_DIRECTORY, 'token_cache')


def get_vk_token():
    token = load_token_from_file()
    token_expired = token is None or int(time.time()) >= token['expiring_time']
    if token_expired:
        token = get_vk_token_object()
        save_token_to_file(token)
    return token['access_token']

def load_token_from_file():
    global TOKEN_CACHE_FILENAME
    if not os.path.isfile(TOKEN_CACHE_FILENAME):
        return None
    with open(TOKEN_CACHE_FILENAME, 'r') as cache_file:
        token = pickle.load(cache_file)
        return token

def save_token_to_file(token):
    global TOKEN_CACHE_FILENAME
    with open(TOKEN_CACHE_FILENAME, 'w') as cache_file:
        pickle.dump(token, cache_file)

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
    parameters = {
        'q': search_queue,
        'count': 5,
        'access_token': access_token
    }
    request_url = 'https://api.vk.com/method/audio.search?{}'.format(urlencode(parameters))

    response = urllib2.urlopen(request_url)
    json_data = response.read()
    data = json.loads(json_data)
    if not 'response' in data:
        print 'Some error occurred'
        print data
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
    parameters = {
        'audio_id': audio_id,
        'owner_id': owner_id,
        'access_token': access_token
    }
    requests_url = 'https://api.vk.com/method/audio.add?{}'.format(urlencode(parameters))

    response = urllib2.urlopen(requests_url).read()
    return 'response' in json.loads(response)

def auth_into_vk(email, password):
    url = 'http://vk.com/login.php'

    buf = cStringIO.StringIO()

    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.FOLLOWLOCATION, 1)
    global COOKIE_FILE
    c.setopt(c.COOKIEJAR, COOKIE_FILE)
    c.setopt(c.COOKIEFILE, COOKIE_FILE)
    c.setopt(c.WRITEFUNCTION, buf.write)

    postFields = '_origin=https://oauth.vk.com'
    postFields += '&email=' + email + '&pass=' + password
    c.setopt(c.POSTFIELDS, postFields)
    c.setopt(c.POST, 1)
    c.perform()
    c.close()
    buf.close()

def get_vk_token_object():
    password = getpass.getpass()
    auth_into_vk(email='kakty3.mail@gmail.com',
                 password=password)

    global APP_ID
    parameters = {
        'client_id': APP_ID,
        'scope': 'audio',  # audio
        'redirect_uri': 'https://oauth.vk.com/blank.html',
        'display': 'page',  # try out other variants
        'v': 5.28,
        'response_type': 'token'
    }
    auth_url = "https://oauth.vk.com/authorize?{}".format(urlencode(parameters))

    buf = cStringIO.StringIO()
    # for suppress output
    storage = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, auth_url)
    c.setopt(c.FOLLOWLOCATION, False)
    global COOKIE_FILE
    c.setopt(c.COOKIEJAR, COOKIE_FILE)
    c.setopt(c.COOKIEFILE, COOKIE_FILE)

    c.setopt(c.HEADERFUNCTION, buf.write)
    # for suppress output
    c.setopt(c.WRITEFUNCTION, storage.write)

    c.perform()
    redirect_url = c.getinfo(c.REDIRECT_URL)
    c.setopt(c.URL, redirect_url)
    c.perform()
    token_url = c.getinfo(c.REDIRECT_URL)

    c.close()
    buf.close()
    storage.close()

    token_object = {}
    token_object['access_token'] = re.search('access_token=([0-9A-Fa-f]+)&', token_url).group(1)
    token_expires_in_seconds = int(re.search('expires_in=([0-9A-Fa-f]+)&', token_url).group(1))
    # token_object['expires_in'] = re.search('expires_in=([0-9A-Fa-f]+)&', token_url).group(1)
    # token_object['user_id'] = re.search('user_id=([0-9A-Fa-f]+)', token_url).group(1)
    token_object['expiring_time'] = int(time.time()) + (token_expires_in_seconds - 1) * 60

    return token_object

if __name__ == '__main__':

    # print get_token()
    token = get_vk_token()
    print token
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
