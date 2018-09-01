# Tactics for avoiding detection

# This library needs to be actively maintained to
# ensure most updated user-agent and proxy site
# information. The headers might also need to be changed
# if they have been detected

import requests
import random
import re
import pandas as pd

from lxml.html import fromstring

# Get proxies for proxy rotation:
def fetch_ssl_proxies():
	proxies = set()


	# Updates every 15 minutes
	urls = ['https://free-proxy-list.net/', 'https://www.sslproxies.org/', 'https://www.us-proxy.org/', 'https://free-proxy-list.net/anonymous-proxy.html']
	for url in urls:
		response = requests.get(url)
		parser = fromstring(response.text)
		for i in parser.xpath('//tbody/tr'):
			if i.xpath('.//td[7]/text()')[0] == 'yes':
				ip = i.xpath('.//td[1]/text()')[0]
				port = i.xpath('.//td[2]/text()')[0]
				proxies.add((ip, port))

	# Updates once every hour
	url = 'http://spys.me/proxy.txt'
	response = requests.get(url)
	p_list = response.text.split('\n')[4:]
	p_list = p_list[:-2]
	for entry in p_list:
		entry = entry.split()
		if len(entry[1]) >= 6:
			if entry[1][3] == 'H' or entry[1][3] == 'A':
				if entry[1][5] == 'S':
					entry = entry[0].split(':')
					ip = entry[0]
					port = entry[1]
					proxies.add((ip, port))

	#print(len(proxies))
	return proxies

def fetch_other_proxies():
	proxies = set()
	# Updates every 15 minutes
	urls = ['https://free-proxy-list.net/', 'https://www.sslproxies.org/', 'https://www.us-proxy.org/', 'https://free-proxy-list.net/anonymous-proxy.html']
	for url in urls:
		response = requests.get(url)
		parser = fromstring(response.text)
		for i in parser.xpath('//tbody/tr'):
			if i.xpath('.//td[7]/text()')[0] == 'no':
				ip = i.xpath('.//td[1]/text()')[0]
				port = i.xpath('.//td[2]/text()')[0]
				proxies.add((ip, port))

	# Updates once every hour
	url = 'http://spys.me/proxy.txt'
	response = requests.get(url)
	p_list = response.text.split('\n')[4:]
	p_list = p_list[:-2]
	for entry in p_list:
		entry = entry.split()
		if len(entry[1]) >= 4:
			if entry[1][3] == 'H' or entry[1][3] == 'A' and len(entry[1]) < 6:
				entry = entry[0].split(':')
				ip = entry[0]
				port = entry[1]
				proxies.add((ip, port))

	urls = ['http://www.gatherproxy.com/proxylist/anonymity/?t=Elite', 'http://www.gatherproxy.com/proxylist/anonymity/?t=Anonymous', 'http://www.gatherproxy.com/sockslist']
	for url in urls:
		response = requests.get(url)
		parser = fromstring(response.text)
		for entry in parser.xpath('//script[@type="p/javascript"][contains(text(), "PROXY")]/text()'):
			ip = re.search(r'"PROXY_IP":"(.*?)"', entry).group(1)
			port = str(int(re.search(r'"PROXY_PORT":"(.*?)"', entry).group(1), 16))
			proxies.add((ip, port))

	url = 'https://www.socks-proxy.net/'
	response = requests.get(url)
	parser = fromstring(response.text)
	for i in parser.xpath('//tbody/tr'):
		ip = i.xpath('.//td[1]/text()')[0]
		port = i.xpath('.//td[2]/text()')[0]
		proxies.add((ip, port))
	return proxies

def fetch_proxies():
	return fetch_ssl_proxies() | fetch_other_proxies()

#def boot_proxies():

# This User-Agent list might need to be updated every once in a while to prevent detection through outdated browser information
def get_ua():
	return random.choice(ual)

ual =  [
#Chrome
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
#Firefox
'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
]

# header rotation
def create_request_header(ua):
	return{
				'user-agent': ua
		}

if __name__ == "__main__":
	print(fetch_proxies())
