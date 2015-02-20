from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import parse_qs
import urllib2
from urllib import urlencode

APP_ID = 4786305
APP_SECRET = 'RgGtGp8CwfewgwW1Pldl'
ACCESS_TOKEN_OBJECT = None
REDIRECT_URI = None

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global  REDIRECT_URI
        REDIRECT_URI = self.headers.get('Host')
        print REDIRECT_URI
        global ACCESS_TOKEN_OBJECT
        question_mark_position = self.path.find('?')
        if question_mark_position == -1:
            action = self.path[1:]
        else:
            action = self.path[1:question_mark_position]

        if action:
            print '[ACTION]', action
        if action == 'get_token':
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(ACCESS_TOKEN_OBJECT)
            return

        url_parameters = parse_qs(self.path[2:])
        if 'code' in url_parameters:
            ACCESS_TOKEN_OBJECT = get_token_object(APP_ID, APP_SECRET, url_parameters['code'][0])
        # print("Just received a GET request")
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        return

    # def log_request(self, code=None, size=None):
    #     print('Request')

    # def log_message(self, format, *args):
    #     print('Message')


def get_token_object(app_id, app_secret, code):
    # request = (
    #     'https://oauth.vk.com/access_token?'
    #     'client_id={APP_ID}&'
    #     'client_secret={APP_SECRET}&'
    #     'code={CODE}&'
    #     'redirect_uri={REDIRECT_URI}'
    # ).format(
    #     APP_ID=app_id,
    #     APP_SECRET=app_secret,
    #     CODE=code,
    #     REDIRECT_URI=REDIRECT_URI
    # )
    parameters = {
        'client_id': app_id,
        'client_secret': app_secret,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    request_url = 'https://oauth.vk.com/access_token?{}'.format(urlencode(parameters))

    # print 'Fetching token'
    json_response = urllib2.urlopen(request_url).read()
    # token_object = json.loads(json_response)
    # token = dict_response['access_token']
    # print 'Token received', token
    return json_response


if __name__ == "__main__":
    server = HTTPServer(('192.168.0.106', 5676), MyHandler)
    print('Started http server')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down server')
        server.socket.close()
