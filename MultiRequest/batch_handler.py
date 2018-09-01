import multiprocessing
import time
import random
from . import datatypes
import traceback
from termcolor import cprint

class MultiBatchHandler:
	def __init__(self, cls, data, proxy_pool, lock, log, call_fn, timeout):
		self.pid = multiprocessing.current_process()._identity
		self.proxy_pool = proxy_pool
		self.lock = lock
		self.log = log
		self.results = []
		self.call_fn = call_fn
		self.current_proxy = self.try_get_proxy()
		self.batch_dict = datatypes.Data.from_data(cls, data)
		self.timeout = timeout
		self.interrupt = False

	def run(self):
		print("{} Running batch handler".format(self.pid))

		while self.batch_dict != {}:
			request_params = self.batch_dict[random.choice(list(self.batch_dict))]
			while self.interrupt == False:
				self.next(request_params)
			self.interrupt = False
			self.switch_proxy()

		self.lock.acquire()
		self.proxy_pool.replace(self.current_proxy)
		self.lock.release()
		return self.results

	def next(self, request_params):
		#print("{}/{}: next".format(self.pid, self.current_proxy))
		switch = False
		try:
			success, score, completed, switch = self.call_fn(self.timeout, request_params, self.current_proxy, self.results)
			if success:
				self.success()
				self.current_proxy.score += score
				self.current_proxy.momentum = 0
				# We use a score of zero to indicate the process has completed
				if completed == True:
					self.interrupt = True
					del self.batch_dict[str(repr(request_params))]
				else:
					request_params.next()
			else:
				self.failure()
				self.current_proxy.score += score
				self.current_proxy.momentum += score
				if self.current_proxy.momentum < -(random.randint(1, 2)):
					switch = True
		except Exception as e:
			self.failure()
			print("Batch handler caught error:", e)
			#traceback.print_exc()
			self.current_proxy.score -= 1
			self.current_proxy.momentum -= 1
			if self.current_proxy.momentum < -(random.randint(1, 2)):
				switch = True

		if self.current_proxy.score < -16 or self.current_proxy.momentum < -9:
			cprint("{} Blacklisting {}...".format(self.pid, self.current_proxy), 'red')
			self.blacklist_proxy()
			self.interrupt = True
		if switch:
			print("switching")
			self.interrupt = True

	def success(self):
		self.lock.acquire()
		self.log["Successes"] += 1
		self.log["Total"] += 1
		self.lock.release()

	def failure(self):
		self.lock.acquire()
		self.log["Total"] += 1
		self.lock.release()

	def blacklist_proxy(self):
		self.lock.acquire()
		self.proxy_pool.blacklist(self.current_proxy)
		self.lock.release()
		self.current_proxy = self.try_get_proxy()

	def try_get_proxy(self):
		while True:
			unlocked = self.lock.acquire(False)
			if unlocked:
				if len(self.proxy_pool) > 0:
					proxy = self.proxy_pool.get_proxy()
					self.lock.release()
					break
				else:
					self.lock.release()
					time.sleep(random.uniform(4, 8))
			else:
				print("tryget: LOCKED!")
				time.sleep(0.1)
		return proxy

	def switch_proxy(self):
		proxy = self.try_get_proxy()
		self.lock.acquire()
		self.proxy_pool.replace(self.current_proxy)
		self.lock.release()
		self.current_proxy = proxy

''' The switch function implemented below is good when there is a
	proxy bottleneck, but sucks once the proxy pool is full
	def switch_proxy(self):
		replaced = False
		while True:
			unlocked = self.lock.acquire(False)
			if unlocked:
				if len(self.proxy_pool) > 0:
					proxy = self.proxy_pool.get_proxy()
					self.lock.release()
					break
				else:
					self.lock.release()
					time.sleep(random.uniform(4, 8))
			else:
				print("LOCKED! Tried to switch...")
				if replaced == False:
					print("Replacing first...")
					self.lock.acquire()
					self.proxy_pool.replace(self.current_proxy)
					self.lock.release()
					replaced = True
					time.sleep(0.3)
				else:
					time.sleep(5)
		if replaced == False:
			self.lock.acquire()
			self.proxy_pool.replace(self.current_proxy)
			self.lock.release()
		self.current_proxy = proxy
'''
