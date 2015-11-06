#coding: utf-8
import sys
import argparse
import re
import socket
import urllib2
import os
import urlparse
from urllib import urlencode
import HTMLParser
import pickle
import json
import time
import webbrowser
import SocketServer, BaseHTTPServer

import xml.etree.ElementTree as ET
from pync import Notifier

from edit_distance import get_edit_distance


HOME_DIR = os.path.expanduser("~")
RADIUM_SONG_LOG_FILENAME = os.path.join(HOME_DIR, 'Library/Application Support/Radium/song_history.plist')
APP_ID = '4786305'
SCRIPT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
TOKEN_CACHE_FILENAME = os.path.join(SCRIPT_DIRECTORY, '.token')
TOKEN = None


def get_vk_token():
    # TODO: test with expired token
    # TODO: check if token is valid

    token = load_token_from_file()
    if token and token['expiring_time'] > int(time.time()):
        access_token = token['access_token']
    else:
        token = get_new_vk_token()
        save_token_to_file(token)
        access_token = token['access_token']
    return access_token


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
    # TODO: rewrite in more clear way
    tree = ET.parse(RADIUM_SONG_LOG_FILENAME)
    root = tree.getroot()
    song = root[0][0]
    song_name = song.findall('string')[-1].text.encode('utf-8')
    return HTMLParser.HTMLParser().unescape(song_name)


def search_song(access_token, search_queue, n_of_items=5):
    # TODO: make list of search_query preprocessors, e.g. deleting word or symbols
    print('Looking for "{}"'.format(search_queue))
    parameters = {
        'q': search_queue,
        'count': n_of_items,
        'access_token': access_token
    }
    request_url = 'https://api.vk.com/method/audio.search?{}'.format(urlencode(parameters))
    # TODO: rewrite with requests
    response = urllib2.urlopen(request_url)
    data = json.loads(response.read())
    # TODO: add error_code handlers
    if 'response' not in data:
        print 'Some error occurred'
        print data
        return
    songs_list = data['response'][1:n_of_items + 1]
    for index, song in enumerate(songs_list):
        song['artist'] = song['artist'].encode('utf-8')

        song['title'] = song['title'].encode('utf-8')
        # TODO: move it to string normalization method with replacing web chars
        song['title'] = re.sub('[\n+]', '', song['title'])
        print '{:2d}. {} - {}'.format(index + 1, song['artist'], song['title'])

    return songs_list


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


class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("<html><body>")
        self.wfile.write("""
            <script>
            var xhr = new XMLHttpRequest();

            xhr.open("POST", '{redirect_uri}', true)
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')

            xhr.send(window.location.hash);
            window.close();
            </script>
        """.format(
            redirect_uri='http://' + self.headers.get('Host')
        ))
        self.wfile.write("</body></html>")

    def do_POST(self):
        length = int(self.headers.getheader('content-length'))
        global TOKEN
        TOKEN = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=0)


def get_new_vk_token():
    SocketServer.TCPServer.allow_reuse_address = True
    httpd = None
    redirect_port = 20938
    while httpd is None:
        try:
            httpd = SocketServer.TCPServer(("", redirect_port), HttpHandler)
            print 'Server is running on port %d.' % redirect_port
        except socket.error:
            print 'Port %d is already in use. Trying next port.' % redirect_port
            redirect_port += 1

    parameters = {
        'client_id': APP_ID,
        'scope': 'audio',
        'redirect_uri': 'http://localhost:%d' % redirect_port,
        'display': 'page',
        'v': 5.37,
        'response_type': 'token'
    }
    auth_url = "https://oauth.vk.com/authorize?{}".format(urlencode(parameters))

    webbrowser.open_new(auth_url)

    httpd.handle_request()
    httpd.handle_request()
    token_object = dict()
    token_object['access_token'] = TOKEN['#access_token'][0]
    token_expires_in = int(TOKEN['expires_in'][0])
    token_object['expiring_time'] = int(time.time()) + token_expires_in - 60
    return token_object


def get_song_short_title(song, max_length=30):
    title = song['title']
    if len(title) > max_length:
        space_index = title.find(' ', max_length)
        if space_index != -1:
            title = title[:space_index] + ' ...'
    return title


def get_most_similar_song(song_name, songs_list):
    min_distance = sys.maxint
    best_song = None
    for song in songs_list:
        distance = get_edit_distance(song_name, "%s - %s" % (song['artist'], song['title']))
        if distance < min_distance:
            min_distance = distance
            best_song = song
    return best_song


def run_dev():
    vk_token = get_vk_token()
    song_name = get_song_name()
    songs_list = search_song(vk_token, song_name)
    song = get_most_similar_song(song_name, songs_list)
    if song is None:
        search_url = 'https://vk.com/audio?{}'.format(urlencode({'q': song_name}))
        print 'Nothing found.', search_url
        Notifier.notify(title='Nothing found',
                        message='Click to open audio search in browser.',
                        sender='com.catpigstudios.Radium',
                        open=search_url)
    else:
        # add_song(song['aid'], song['owner_id'], vk_token)

        short_title = get_song_short_title(song)
        print '"%s - %s" added.' % (song['artist'], short_title)
        # Notifier.notify(title=short_title,
        #                 subtitle='by ' + song['artist'],
        #                 message='Song was successfully added.',
        #                 sender='com.catpigstudios.Radium',
        #                 open='https://vk.com/audio')


def run():
    vk_token = get_vk_token()
    song_name = get_song_name()
    songs_list = search_song(vk_token, song_name)
    song = get_most_similar_song(song_name, songs_list)
    if song is None:
        search_url = 'https://vk.com/audio?{}'.format(urlencode({'q': song_name}))
        print 'Nothing found.', search_url
        Notifier.notify(title='Nothing found',
                        message='Click to open audio search in browser.',
                        sender='com.catpigstudios.Radium',
                        open=search_url)
    else:
        add_song(song['aid'], song['owner_id'], vk_token)

        short_title = get_song_short_title(song)
        print '"%s - %s" added.' % (song['artist'], short_title)
        Notifier.notify(title=short_title,
                        subtitle='by ' + song['artist'],
                        message='Song was successfully added.',
                        sender='com.catpigstudios.Radium',
                        open='https://vk.com/audio')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dev',
                        help='Run in developer mode',
                        default=False,
                        action='store_true')
    args = parser.parse_args()
    if args.dev:
        run_dev()
    else:
        run()
