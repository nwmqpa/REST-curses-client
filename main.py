"""Main client file for the RESTful game API."""
import curses
import sys
import time
import requests
import json


def make_request(url):
    response = requests.get(url)
    if (response.status_code == 200):
        try:
            return json.loads(json.loads(str(response.text)))
        except ValueError:
            return str(response.text)
        except TypeError:
            return str(response.text)
    return None

typing = True

def display_middle(string, stdscr):
    max_cols = 0
    for i in string.split('\n'):
        if len(i) > max_cols:
            max_cols = len(i)
    max_lines = len(string.split('\n')) - 1
    startx = (curses.COLS - max_cols) // 2
    starty = (curses.LINES - max_lines) // 2
    for i in range(len(string.split('\n'))):
        startx = (curses.COLS - max_cols) // 2
        stdscr.addstr(starty, startx, string.split('\n')[i])
        starty = starty + 1
        startx = startx + len(string.split('\n')[i])
    return startx, starty - 1


class GameClient(object):

    def __init__(self, base_url, game_port, username, stdscr):
        self.url = base_url + ':' + str(game_port)
        make_request(self.url + "/join/" + username)
        self.stdscr = stdscr
        self.username = username
        self.handlers = {}
        self.register_handlers()
        make_request(self.url + "/ready/" + self.username)
        self.stdscr.nodelay(True)
        self.game_loop()
        self.stdscr.nodelay(False)

    def register_handlers(self):
        handlers = make_request(self.url + "/handlers")
        for i in handlers:
            self.stdscr.clear()
            string = 'What key do you want for {0} ?\n"{1}"'.format(i, handlers[i])
            display_middle(string, self.stdscr)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            self.handlers[key] = i

    def display(self):
        self.stdscr.clear()
        to_display = make_request(self.url + "/display/" + self.username)
        to_display = to_display.replace("\\n", "\n")[1:-1]
        display_middle(to_display, self.stdscr)
        self.stdscr.refresh()

    def game_loop(self):
        while 1:
            self.display()
            key = self.stdscr.getch()
            if key in self.handlers:
                make_request(self.url + "/handlers/" + self.username + '/' + self.handlers[key])
            time.sleep(0.1)

class Client(object):

    def __init__(self, base_url):
        self.base_url = base_url
        try:
            self.stdscr = curses.initscr()
            self.stdscr.nodelay(False)
            curses.cbreak()
            curses.start_color()
            last_x, last_y = display_middle("What is you username ?\n $> ", self.stdscr)
            self.stdscr.refresh()
            self.username = self.stdscr.getstr(last_y, last_x)
            curses.noecho()
            self.dashboard()
        except curses.error:
            pass
        finally:
            curses.endwin()

    def matchmaker(self, game_choosed):
        playground = make_request(self.base_url + '/getmatch/' + game_choosed)[:-1]
        make_request(self.base_url + '/match/{0}/join/{1}'.format(playground, self.username))
        playground_status = make_request(self.base_url + '/match/{}/status'.format(playground))
        self.stdscr.clear()
        while playground_status["port"] == 0:
            time.sleep(1)
            playground_status = make_request(self.base_url + '/match/{}/status'.format(playground))
            self.stdscr.clear()
            display_middle("Waiting for players...\n", self.stdscr)
            self.stdscr.refresh()
        time.sleep(2)
        game = GameClient(":".join(self.base_url.split(":")[:-1]),
                    playground_status["port"],
                    self.username, self.stdscr)
    
    def dashboard(self):
        while 1:
            self.stdscr.clear()
            games = make_request(self.base_url + '/games')
            string = "Welcome, " + self.username + ", what game do you choose ?\n"
            for i in range(len(games)):
                string = string + str(i) + ": " + games[i] + '\n'
            display_middle(string, self.stdscr)
            self.stdscr.refresh()
            choose = self.stdscr.getch()
            game_choosed = games[int(chr(choose))]
            self.matchmaker(game_choosed)


if __name__ == "__main__":
    if len(sys.argv) != 1:
        client = Client(sys.argv[1])
    else:
        print("Provide a valid url.")
        sys.exit(84)
    
