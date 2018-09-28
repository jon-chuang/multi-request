import multiprocessing
import random
import time
import operator
import traceback
import requests
from termcolor import cprint
import ctypes
import signal
import os
import sys
from contextlib import contextmanager
import datetime

from multiprocessing import Lock, Pool, Queue, Process, Value, Manager
import hipsterplot as hp #Dependency

try:
	from . import tactics
	from . import proxypool as pp
except:
	import tactics
	import proxypool as pp

class Accumulator:
	def __init__(self, TEST_TIMEOUT):
		self.testing_urls = pp.urls
		self.manager = Manager()
		self.lock = self.manager.Lock()
		self.timeout = TEST_TIMEOUT
		self.n_proxy_workers = 25
		self.terminated = Value(ctypes.c_bool)
		self.terminated.value = False
		self.proxy_set = set()
		self.proxy_pool = self.manager.dict()
		self.queue = Queue()
		with open("Data/AccumulatedProxies.txt", 'r') as f:
			proxies = f.readlines()
		for proxy in proxies:
			self.proxy_pool[proxy.strip()] = 1

	def run(self):
		print("Starting Accumulator")
		pool = Pool()

		terminator = Process(target=self.terminator)
		self.fetcher = Process(target = self.proxy_fetcher)
		self.fetcher.start()
		self.injectors = [Process(target=self.proxy_injector_worker) for _ in range(self.n_proxy_workers)]
		for i in self.injectors:
			i.start()
		terminator.start()
		terminator.join()
		return True

	''' Instantiates the terminator process which prints messages while the
		program is running and kills the proxy handler and its subprocesses
		once the jobs in the main process are done, triggering a terminate
		signal to be sent
	'''
	def terminator(self):
		cprint("terminator running", 'yellow')
		i = 0
		ratio_ts = []
		n_requests = []
		n_successes = []
		stats = {"Total": 0, "Successes" : 0}
		past_datetime = datetime.datetime.now()
		total_time_elapsed = datetime.timedelta(seconds = 0)
		while not self.terminated.value:
			if i % 30 == 0:
				new_datetime = datetime.datetime.now()
				time_elapsed = new_datetime - past_datetime
				while True:
					unlocked = self.lock.acquire(False)
					if unlocked:
						len_pool = len(self.proxy_pool)
						pool_str = str(self.proxy_pool)
						self.lock.release()
						break
					else:
						print("LOCK IN USE!")
						time.sleep(0.5)
				cprint("Time elapsed: " + str(time_elapsed), 'cyan')
				cprint("Proxy pool ({}):\n{}".format(len_pool, pool_str), 'cyan')
				print("Press any key to terminate...")

				self.lock.acquire()
				pp_copy = self.proxy_pool.copy()
				self.lock.release()
				with open("Data/AccumulatedProxies.txt", 'w') as f:
					for proxy in list(pp_copy):
						f.write(proxy + '\n')
			time.sleep(1)
			i += 1
			# END LOOP

		# if loop is terminated
		cprint("Terminating proxy manager", 'red')
		for i in self.injectors:
			i.terminate()
		self.fetcher.terminate()

	def terminate(self):
		self.terminated.value = True

	''' End of terminator code '''

	def proxy_fetcher(self):
		self.proxy_set = set()
		counter = 0
		print("proxy fetcher working")
		while True:
			# Reevaluate proxies every 10 minutes
			if counter % 900 == 0:
				cprint('Reevaluating proxies...', 'cyan')
				self.lock.acquire()
				old_proxy_pool = dict(self.proxy_pool)
				self.lock.release()

				while old_proxy_pool != {}:
					if self.queue.qsize() < 35 and len(old_proxy_pool) > 0:
						proxy = random.choice(list(old_proxy_pool))
						self.proxy = old_proxy_pool.pop(proxy)
						self.lock.acquire()
						self.proxy_pool.pop(proxy)
						self.queue.put(proxy)
						self.lock.release()
						cprint("Retesting {}...".format(proxy), 'cyan')
						continue
					time.sleep(1)
				cprint("Finished queuing all current proxies for reevaluation...")

			if self.queue.qsize() < 35 and len(self.proxy_set) > 0:
				proxy = self.proxy_set.pop()
				self.queue.put(proxy)
				continue
			# Get more proxies if not enough
			if counter % 180 == 0:
				cprint("Fetching proxies...", 'cyan')
				new_proxy_set = tactics.fetch_proxies()

				self.lock.acquire()
				all_in_pool = set(self.proxy_pool.keys())
				self.lock.release()

				new_not_old = new_proxy_set - (new_proxy_set & (self.proxy_set | all_in_pool))
				cprint("Number of new proxies: {}".format(len(new_not_old)), 'cyan')
				self.proxy_set = self.proxy_set | new_not_old
				cprint("Accesed proxy fetch ({} currently unverified)".format(len(self.proxy_set)), 'cyan')

			time.sleep(1)
			counter += 1
			if counter == 30:
				print("Number of unverified proxies: {}. Time left to next fetch: {}s".format(len(self.proxy_set), 180 - counter % 180))
				self.lock.acquire()
				pp_copy = self.proxy_pool.copy()
				self.lock.release()
				with open("Data/AccumulatedProxies.txt", 'w') as f:
					for proxy in list(pp_copy):
						f.write(proxy + '\n')

	def proxy_injector_worker(self):
		while True:
			proxy = self.queue.get()
			self.test_proxy(proxy)
			time.sleep(1)

	def test_proxy(self, proxy):
		try:
			ua = tactics.get_ua()
			url = random.choice(self.testing_urls)
			response = requests.get(url, proxies = {'http': proxy, 'https': proxy}, headers = {'user-agent': ua}, timeout=self.timeout)
			if response.status_code != 200:
				raise ValueError("Page not loaded correctly: {}".format(url))
			# If the pages load correctly in the given time, add them to the proxy pool
			success = False
			self.lock.acquire()
			if not proxy in self.proxy_pool:
				self.proxy_pool[proxy] =  1
				success = True
			self.lock.release()
			if success:
				cprint("Successfully added: " + proxy + ". Tested on: " + url, 'cyan')
		except Exception as e:
			pass

if __name__ == '__main__':
	acc = Accumulator(10)
	session = Process(target=acc.run)
	session.start()
	input("Press Enter to terminate...\n")
	acc.terminate()
	session.join()
	print("Accumulation of proxies completed")
