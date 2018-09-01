from multiprocessing.managers import BaseManager, BaseProxy
from multiprocessing import Lock
import itertools
from termcolor import cprint
import random

class Proxy:
	def __init__(self, ip, port, ua):
		self.ip = ip
		self.port = port
		self.score = 0
		self.ua = ua
		self.momentum = 0

	def __str__(self):
		return self.ip + ":" + self.port

	@classmethod
	def from_2ple(cls, tuple, ua):
		return cls(tuple[0], tuple[1], ua)

class ProxyPool:
	def __init__(self):
		self.pool = {}
		self.in_use = {}
		self.bl = set()
		self.virtual = [set()]
		#self.virtualisation_level = 0

	def __len__(self):
		return len(self.pool)

	def add(self, proxy):
		proxy_key = str(proxy)
		# print(self.all_proxies())
		if not (proxy_key in self.all_proxies()):
			self.pool[proxy_key] = proxy
			return True
		else:
			return False

	def replace(self, proxy):
		proxy_key = str(proxy)
		virtual = self.delete_virtual_proxy(proxy_key)
		if virtual:
			pass
		else:
			self.pool[proxy_key] = proxy
			del self.in_use[proxy_key]

	def get_proxy(self):
		# Returns the proxy with the highest score
		e = random.randint(0, 2)
		trend_not_bad = [x for x in self.pool.items() if x[1].momentum >= -3]
		if e == 0 and len(trend_not_bad) != 0:
			proxy_key = max(trend_not_bad, key = lambda x : x[1].score)[0]
		else:
			proxy_key = random.choice(list(self.pool))
		proxy = self.pool.pop(proxy_key)
		self.in_use[proxy_key] = proxy
		return proxy

	# For a given virtual layer, you can virtualise all proxies currently in use
	# in the layer below it.
	def create_virtual_proxy(self, N_VIRTUAL):
		# Let us check what the lowest layer virtualisation is possible at
		for n in range(N_VIRTUAL):
			if len(self.virtual) <= n:
				self.virtual.append(set())
			assert (set(self.in_use.keys()) & self.virtual[n]) == self.virtual[n]
			if n == 0:
				in_use_below = set(self.in_use.keys())
			else:
				in_use_below = self.virtual[n-1] - (self.virtual[n-1] & set(self.pool))
			virtualisable = in_use_below - self.virtual[n]

			if len(virtualisable) > 0:
				proxy_key = random.choice(list(virtualisable))
				self.pool[proxy_key] = self.in_use[proxy_key]
				self.virtual[n].add(proxy_key)
				# cprint("Virtualised {} at level {}".format(proxy_key, n+1), 'cyan')
				return True
		cprint("Virtualisation at level {} failed: not enough resources.".format(n+1), 'cyan')
		return False

	def delete_virtual_proxy(self, proxy_key):
		for n in range(len(self.virtual)):
			virtualised = self.virtual[-(n+1)]
			if proxy_key in virtualised:
				virtualised.remove(proxy_key)
				return True

	def blacklist(self, proxy):
		proxy_key = str(proxy)
		virtual = self.delete_virtual_proxy(proxy_key)
		if virtual:
			cprint("Deleted virtual proxy. Did not blacklist.", 'cyan')
		else:
			del self.in_use[proxy_key]
			self.bl.add(proxy_key)

	def get_pool(self):
		return self.pool

	def get_in_use(self):
		return self.in_use

	def get_virtual(self):
		return self.virtual

	def all_proxies(self):
		return self.bl | set(self.in_use.keys()) | set(self.pool.keys())

	# Pretty printing the proxy pool state
	def __str__(self):
		p_list = [self.get_proxy_details(self.pool[proxy]) for proxy in self.pool]
		top = sorted(p_list, key= lambda d : d['score'], reverse=True)
		losers = sorted(top[10:], key= lambda d : d['momentum'])
		losers.reverse()
		in_pool = ['[In pool] ({})'.format(len(p_list))] + top[:min(10, len(p_list))] + ['...'] + losers[-min(10, len(p_list)):]
		in_use = ['[In use] ({})\n'.format(len(self.in_use))] + list(self.in_use)
		in_virtual = []
		for i in range(len(self.virtual)):
			in_virtual += ['\n[Virtual proxies created at level {}] ({})\n'.format(i+1, len(self.virtual[i]))] + list(self.virtual[i])
		in_bl = ['\n[In blacklist] ({})\n'.format(len(self.bl))] + list(self.bl)
		pp_string = ''
		for p in in_pool:
			pp_string  += str(p) + '\n'
		for p in in_use + in_virtual + in_bl:
			pp_string  += str(p) + '  '
		return pp_string

	def get_proxy_details(self, proxy):
		return {'proxy': proxy.ip + ':' + proxy.port, 'score' : proxy.score, 'momentum' : proxy.momentum}

# How to define a proxy class ordinarily
#class ProxyProxy(NamespaceProxy):
#	_exposed_ = ('__getattribute__', '__setattribute__', '__delattr__', )
# code for exposing the above functions. Alternatively, we can use the type
# base function

class ProxyManager(BaseManager):
	pass

# Taken from multiprocessing.managers
# Uses generic programming and memoization (caching)
def MakeProxyType(name, exposed, _cache={}):
	'''
	Return a proxy type whose methods are given by `exposed`
	'''
	exposed = tuple(exposed) # in case a list is passed in instead
	try:
		return _cache[(name, exposed)]
	except KeyError:
		pass

	dic = {}

	for meth in exposed:
		exec('''def %s(self, *args, **kwds):
		return self._callmethod(%r, args, kwds)''' % (meth, meth), dic)
	ProxyType = type(name, (BaseProxy,), dic)
	ProxyType._exposed_ = exposed
	_cache[(name, exposed)] = ProxyType
	return ProxyType

ProxyProxy = MakeProxyType('ProxyProxy', (
	'__str__', '__len__', '__copy__', 'add', 'replace', 'get_proxy', 'get_pool', 'blacklist', 'all_proxies', 'get_in_use', 'get_virtual', 'create_virtual_proxy'
	))

ProxyManager.register('proxy_pool', ProxyPool, ProxyProxy)
ProxyManager.register('Lock', Lock)

urls = [
		"https://www.accuweather.com/"
	  , "https://www.facebook.com"
	  , "https://www.youtube.com"
	  , "https://www.twitter.com"
	  , "https://maps.google.com"
	  , "https://www.amazon.com"
	  , "https://www.bookdepository.com"
	  ,'http://www.youtube.com', 'http://www.facebook.com', 'http://www.baidu.com', 'http://www.yahoo.com', 'http://www.amazon.com', 'http://www.wikipedia.org', 'http://www.qq.com', 'http://www.google.co.in', 'http://www.twitter.com', 'http://www.live.com', 'http://www.taobao.com', 'http://www.bing.com', 'http://www.instagram.com', 'http://www.weibo.com', 'http://www.sina.com.cn', 'http://www.linkedin.com', 'http://www.yahoo.co.jp', 'http://www.msn.com', 'http://www.vk.com', 'http://www.google.de', 'http://www.yandex.ru', 'http://www.hao123.com', 'http://www.google.co.uk', 'http://www.reddit.com', 'http://www.ebay.com', 'http://www.google.fr', 'http://www.t.co', 'http://www.tmall.com', 'http://www.google.com.br', 'http://www.360.cn', 'http://www.sohu.com', 'http://www.amazon.co.jp', 'http://www.pinterest.com', 'http://www.netflix.com', 'http://www.google.it', 'http://www.google.ru', 'http://www.microsoft.com', 'http://www.google.es', 'http://www.wordpress.com', 'http://www.gmw.cn', 'http://www.tumblr.com', 'http://www.paypal.com', 'http://www.blogspot.com', 'http://www.imgur.com', 'http://www.stackoverflow.com', 'http://www.aliexpress.com', 'http://www.naver.com', 'http://www.ok.ru', 'http://www.apple.com', 'http://www.github.com', 'http://www.chinadaily.com.cn', 'http://www.imdb.com', 'http://www.google.co.kr', 'http://www.fc2.com', 'http://www.jd.com', 'http://www.blogger.com', 'http://www.163.com', 'http://www.google.ca', 'http://www.whatsapp.com', 'http://www.amazon.in', 'http://www.office.com', 'http://www.tianya.cn', 'http://www.google.co.id', 'http://www.youku.com', 'http://www.rakuten.co.jp', 'http://www.craigslist.org', 'http://www.amazon.de', 'http://www.nicovideo.jp', 'http://www.google.pl', 'http://www.soso.com', 'http://www.bilibili.com', 'http://www.dropbox.com', 'http://www.xinhuanet.com', 'http://www.outbrain.com', 'http://www.pixnet.net', 'http://www.alibaba.com', 'http://www.alipay.com', 'http://www.microsoftonline.com', 'http://www.booking.com', 'http://www.googleusercontent.com', 'http://www.google.com.au', 'http://www.popads.net', 'http://www.cntv.cn', 'http://www.zhihu.com', 'http://www.amazon.co.uk', 'http://www.diply.com', 'http://www.coccoc.com', 'http://www.cnn.com', 'http://www.bbc.co.uk', 'http://www.twitch.tv', 'http://www.wikia.com', 'http://www.google.co.th', 'http://www.go.com', 'http://www.google.com.ph', 'http://www.doubleclick.net', 'http://www.onet.pl', 'http://www.googleadservices.com', 'http://www.accuweather.com', 'http://www.googleweblight.com', 'http://www.answers.yahoo.com'
	  ]
