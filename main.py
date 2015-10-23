#! /usr/bin/env python
#coding: utf-8
import xml.etree.ElementTree as ET
import urllib2
import getpass
import os
import StringIO
from urllib import urlencode
import cStringIO
import pycurl
import re
import HTMLParser
import pickle
import json
from pync import Notifier
import time
import BaseHTTPServer

HOME_DIR = os.path.expanduser("~")
RADIUM_SONG_LOG_FILENAME = os.path.join(HOME_DIR, 'Library/Application Support/Radium/song_history.plist')
APP_ID = '4786305'
SCRIPT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
COOKIE_FILE = os.path.join(SCRIPT_DIRECTORY, 'cookie.txt')
TOKEN_CACHE_FILENAME = os.path.join(SCRIPT_DIRECTORY, 'token_cache')


def get_vk_token():
    token = load_token_from_file()
    token = None
    # token_expired = token is None or int(time.time()) >= token['expiring_time']
    if token is not None:
        if token['expiring_time'] == 0:
            token_expired = False
        elif int(time.time()) >= token['expiring_time']:
            token_expired = True
    else:
        token_expired = True

    if token_expired:
        print 'Token expired. Fetching new one.'
        token = get_vk_token_object()
        save_token_to_file(token)
    return token['access_token']


def load_token_from_file():
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
    tree = ET.parse(RADIUM_SONG_LOG_FILENAME)
    root = tree.getroot()
    song = root[0][0]
    song_name = song.findall('string')[-1].text.encode('utf-8')
    return HTMLParser.HTMLParser().unescape(song_name)


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
    if len(data['response']) <= 1:
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


# def auth_into_vk(email, password):
#     url = 'http://vk.com/login.php'

#     buf = cStringIO.StringIO()

#     c = pycurl.Curl()
#     c.setopt(c.URL, url)
#     c.setopt(c.FOLLOWLOCATION, 1)
#     c.setopt(c.COOKIEJAR, COOKIE_FILE)
#     c.setopt(c.COOKIEFILE, COOKIE_FILE)
#     c.setopt(c.WRITEFUNCTION, buf.write)

#     postFields = '_origin=https://oauth.vk.com'
#     postFields += '&email=' + email + '&pass=' + password
#     c.setopt(c.POSTFIELDS, postFields)
#     c.setopt(c.POST, 1)
#     c.perform()
#     c.close()
#     buf.close()

def run(server_class=BaseHTTPServer.HTTPServer,
        handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


def get_vk_token_object():
    parameters = {
        'client_id': APP_ID,
        'scope': 'audio',
        # 'redirect_uri': 'https://oauth.vk.com/blank.html',
        'redirect_uri': 'http://yourlocalhostalias.com:8000',
        'display': 'mobile',
        'v': 5.28,
        'response_type': 'token'
    }
    auth_url = "https://oauth.vk.com/authorize?{}".format(urlencode(parameters))

    print auth_url

    # buf = cStringIO.StringIO()
    # for suppress output
    storage = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, auth_url)
    c.setopt(c.FOLLOWLOCATION, 1)
    # global COOKIE_FILE
    c.setopt(c.COOKIEJAR, COOKIE_FILE)
    c.setopt(c.COOKIEFILE, COOKIE_FILE)

    # c.setopt(c.HEADERFUNCTION, buf.write)
    # for suppress output
    c.setopt(c.WRITEFUNCTION, storage.write)
    c.perform()
    run()

    redirect_url = c.getinfo(c.REDIRECT_URL)
    print redirect_url
    # return

    c.setopt(c.URL, redirect_url)
    c.perform()
    token_url = c.getinfo(c.REDIRECT_URL)

    c.close()
    # buf.close()
    # storage.close()

    token_object = {}
    token_object['access_token'] = re.search('access_token=([0-9A-Fa-f]+)&', token_url).group(1)
    token_expires_in_seconds = int(re.search('expires_in=([0-9A-Fa-f]+)&', token_url).group(1))
    # token_object['expires_in'] = re.search('expires_in=([0-9A-Fa-f]+)&', token_url).group(1)
    # token_object['user_id'] = re.search('user_id=([0-9A-Fa-f]+)', token_url).group(1)
    token_object['expiring_time'] = int(time.time()) + token_expires_in_seconds - 60\
                                    if token_expires_in_seconds > 0\
                                    else 0

    return token_object

if __name__ == '__main__':
    token = get_vk_token()
    song_name = get_song_name()
    song = search_song(song_name, token)
    if song is None:
        search_url = 'https://vk.com/audio?{}'.format(urlencode({'q': song_name}))
        print 'Try by yourself', search_url
        Notifier.notify(title='Nothing found',
                        message='Click to open audio search in browser.',
                        sender='com.catpigstudios.Radium',
                        open=search_url)
    else:
        song_id = add_song(song['aid'], song['owner_id'], token)
        print 'Song successfully added.'
        Notifier.notify(title=song['title'],
                        subtitle='by ' + song['artist'],
                        message='Song was successfully added.',
                        sender='com.catpigstudios.Radium')
