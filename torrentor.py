from abc import ABCMeta, abstractmethod
from html import escape
from html.parser import HTMLParser
from threading import Timer
from enum import Enum
import requests
import configparser
import json
import traceback


class TorrentCrawler:
    __metaclass__ = ABCMeta

    @abstractmethod
    def getFirstTorrent(self, itemName):
        pass


class KickassCrawler(TorrentCrawler):
    def __init__(self):
        self.searchUrl = 'http://kat.cr/usearch/'
        self.sorting = '?field=seeders&sorder=desc'
        self.itemName = None

    def getRequestUrl(self, itemName):
        return self.searchUrl + itemName + self.sorting

    def getFirstTorrent(self, itemName):
        self.itemName = escape(itemName)
        response = requests.get(self.getRequestUrl(self.itemName))
        parser = KickassLinkExctractor()
        parser.feed(response.text)
        print('Trying to download by link: ' + repr(parser.links[0]))
        user_agent = {'User-agent': 'Mozilla/5.0'}
        result = requests.get(parser.links[0], headers=user_agent)
        print(result)
        result.raise_for_status()
        return result


class KickassLinkExctractor(HTMLParser):
    regularTorrentClass = 'ka-arrow-down'
 
    def reset(self):
        HTMLParser.reset(self)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)

        if tag == "a" and "data-download" in attrs:
            print(attrs['href'])
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
        return self.config.get(AppConfig.main_section, 'torrents_download_dir')


class FetchTask():

    def __init__(self, appConfig, crawler, item):
        self.appConfig = appConfig
        self.crawler = crawler
        self.item = item
        self.state = States.IDLE
        self.scheduler = RepetableSchedule(self.__execute)

    def execute(self):
        self.scheduler.schedule(2)

    def __execute(self):
        print('Trying to get ' + self.item)
        self.state = States.RUNNING
        try:
            result = self.crawler.getFirstTorrent(self.item)
            outFilename = self.item + '.torrent'
            with open(outFilename, 'wb+') as out:
                out.write(result.content)
        except Exception as e:
            print(traceback.format_exc())
            return ResultStatus.FAIL
        self.state = States.DONE
        self.scheduler.stop()
        print('Done')
        return ResultStatus.SUCCESS


class TaskManager():

    def __init__(self):
        self.__loadTasks()

    def __loadTasks(self):
        with open('appdata.json', 'r') as inFile:
            tasks = json.loads(inFile.read())['tasks']
            for item in tasks:
                FetchTask(appConfig, KickassCrawler(), item).execute()


class States(Enum):
    IDLE, RUNNING, DONE = range(3)


class ResultStatus(Enum):
    SUCCESS, FAIL = range(2)

appConfig = AppConfig()
taskManager = TaskManager()
