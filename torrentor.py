from abc import ABCMeta, abstractmethod
from html import escape
from html.parser import HTMLParser
from threading import Timer
import requests
import sched, time
import tkinter
import ConfigParser

class TorrentCrawler:
    __metaclass__ = ABCMeta

    @abstractmethod
    def getFirstTorrent(self, itemName): 
        pass

class KickassCrawler(TorrentCrawler):
    def __init__(self):
        self.searchUrl = 'http://kat.cr/usearch/'
        self.sorting = '?field=seeders&sorder=desc'
        self.magnetLinkClass = 'imagnet'
        self.regularTorrentClass = 'idownload'

    def getRequestUrl(self, itemName):
        return self.searchUrl + itemName + self.sorting

    def getFirstTorrent(self, itemName): 
        self.itemName = escape(itemName)
        response = requests.get(self.getRequestUrl(self.itemName))
        parser = KickassLinkExctractor()
        parser.feed(response.text)
        return requests.get(parser.links[0])

class KickassLinkExctractor(HTMLParser):
    def reset(self):
        HTMLParser.reset(self)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)

        if tag == "a" and "idownload" in attrs.get("class", ""):
            if attrs["href"] != '#':
                self.links.append(attrs["href"])

class RepetableSchedule():

    default_priority = 1

    def __init__(self, method, *args, **kargs):
        self.method = method
        self.args = args
        self.kargs = kargs
        self.timer = None
        self.running = False

    def __runMethod(self):
        self.method(*self.args, **self.kargs)
        self.__schedule()

    def __schedule(self):
        if self.running:
            self.timer = Timer(self.lastDelay, self.__runMethod, *self.args, **self.kargs)
            self.timer.start()

    def schedule(self, delay):
        if self.running:
            raise Exception('Already running')
        self.running = True
        self.lastDelay = delay
        self.__schedule()

    def stop(self):
        self.timer.cancel()
        self.running = False


class AppConfig():

    main_section = 'Main'

    def __init__(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read('config.ini')
    
    def getTorrentsDir(self):
        return self.config(AppConfig.main_section, 'torrents_download_dir')


def getNewGameOfThronesTorrent():
    print('Fetching fresh Game Of Thrones')
    crawler = KickassCrawler()
    result = crawler.getFirstTorrent('Game Of Thrones')
    with open('test.torrrent', 'wb') as out:
        out.write(result.content)
    print('Done')

print('Started!')

rpSched = RepetableSchedule(getNewGameOfThronesTorrent)
rpSched.schedule(2)

cancelShed = RepetableSchedule(rpSched.stop)
cancelShed.schedule(4)

