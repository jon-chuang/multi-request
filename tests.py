import unittest
from MultiRequest.multirequest import *
from MultiRequest.multiproxy import *
from MultiRequest.tactics import *
from MultiRequest.batch_handler import *
from MultiRequest.proxypool import *

class MultiProxyTest(unittest.TestCase):
	def test_get_proxy(self):
		proxies = [('159.65.73.5', '80')]
		pool = ProxyPool()
		i = 0
		for (ip, port) in proxies:
			i += 1
			ua = get_ua()
			proxy = Proxy(ip, port, ua)
			proxy.score = i
			pool.add(proxy)
		proxy = pool.get_proxy().ip
		self.assertEqual(proxy, '159.65.73.5')

# Test for pretty printing of proxy pool object
def func(x, y, z):
	try:
		print("WORKING", z)
		time.sleep(1)
		return z
	except Exception as e:
		print(e)
def test_proxy_handler():
	handler = MultiRequestHandler(func, 10)
	data = {}
	for i in range(100):
		data[i] = i
	return handler.run(data)

def test_proxy_pool_string():
	proxies = [('159.65.73.5', '80')]
	pool = ProxyPool()
	i = 0
	for (ip, port) in proxies:
		i += 1
		ua = get_ua()
		proxy = Proxy(ip, port, ua)
		proxy.score = i
		pool.add(proxy)
	print(pool)

# Test for MultiRequestHandler
class Datum:
	def __init__(self, val):
		self.value = val
	def __str__(self):
		return str(self.value)
	def next(self):
		pass
def ret_signal(a, b, c, d):
	d.append(random.randint(1, 10))
	print("Spider crawling!")
	time.sleep(1)
	print("completed")
	return random.randint(0, 1), random.randint(-1, 1), True, False
def batch_handler(proxy_pool, lock, log, tuple):
	waiting_time, data = tuple
	if waiting_time != 0:
		print("Staggering for {} seconds (to prevent network spike).".format(waiting_time))
	time.sleep(waiting_time)
	handler = MultiBatchHandler(Datum, data, proxy_pool, lock, log, ret_signal, 10)
	results = handler.run()
	print(results)
	return results
def test_mr_handler():
	handler = MultiRequestHandler(batch_handler, 8)
	data = {}
	for i in range(100):
		data[i] = [i]
	handler.run(data)

# Run this during testting
if __name__ == "__main__":
	print("Trying to test")
	result = test_mr_handler()
	#print("Result:", result)
	#test_proxy_pool_string()
	#unittest.main(verbosity = 2)
