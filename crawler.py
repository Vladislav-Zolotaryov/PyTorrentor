import requests
from html.parser import HTMLParser
from html import escape
from abc import ABCMeta, abstractmethod


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


crawler = KickassCrawler()
result = crawler.searchFor('Game Of Thrones')

with open('test.torrrent', 'wb') as out:
	out.write(result.content)