from abc import ABCMeta, abstractmethod
from html import escape
from html.parser import HTMLParser
from threading import Timer
from enum import Enum
import requests
import configparser


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
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

    def getTorrentsDir(self):
        return self.config(AppConfig.main_section, 'torrents_download_dir')


class FetchTask():

    states = Enum('states', IDLE, RUNNING, DONE)
    results = Enum('results', SUCCESS, FAIL)

    def __init__(self, appConfig, crawler, item, outputDir):
        self.appConfig = appConfig
        self.crawler = crawler
        self.item = item
        self.outputDir = outputDir
        self.state = states.IDLE

    def execute(self):
        self.state = states.RUNNING
        try:
            result = self.crawler.getFirstTorrent(self.item)
            outFilename = self.appConfig.getTorrentsDir() + '/' + self.item + '.torrrent',
            with open(outFilename, 'wb') as out:
                out.write(result.content)
        except:
            return results.FAIL
        self.state = states.DONE
        return results.SUCCESS
