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


OPTIMUM_NO_PROXIES = 300

class MultiProxyHandler:
	def __init__(self, proxy_pool, lock, log,  N_VIRTUAL, MIN_PROXIES, TEST_TIMEOUT, INJECT_FREQUENCY):
		self.proxy_pool = proxy_pool
		self.testing_urls = pp.urls
		self.lock = lock
		self.log = log
		self.min_proxies = MIN_PROXIES
		self.timeout = TEST_TIMEOUT
		self.freq = INJECT_FREQUENCY
		self.n_virtual = N_VIRTUAL
		self.n_proxy_workers = 25
		self.terminated = Value(ctypes.c_bool)
		self.terminated.value = False
		self.proxy_set = set()

	def run(self):
		print("Starting Pool with {} levels of virtualisation".format(self.n_virtual))
		queue = Queue()
		pool = Pool()

		terminator = Process(target=self.terminator)
		self.fetcher = Process(target = self.proxy_fetcher, args = (queue,))
		self.fetcher.start()
		self.injectors = [Process(target=self.proxy_injector_worker, args=(queue,)) for _ in range(self.n_proxy_workers)]
		self.virtualiser = Process(target=self.virtualiser)
		for i in self.injectors:
			i.start()
		self.virtualiser.start()
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
		stats = {"Total": 0, "Successes" : 0}
		past_datetime = datetime.datetime.now()
		total_time_elapsed = datetime.timedelta(seconds = 0)
		while not self.terminated.value:
			i += 1
			if i % 30 == 0:
				new_datetime = datetime.datetime.now()
				time_elapsed = new_datetime - past_datetime
				total_time_elapsed += time_elapsed
				past_datetime = new_datetime
				while True:
					unlocked = self.lock.acquire(False)
					if unlocked:
						log_copy = self.log.copy()
						len_pool = len(self.proxy_pool)
						pool_str = str(self.proxy_pool)
						self.reset_log(self.log)
						self.lock.release()
						break
					else:
						print("LOCK IN USE!")
						time.sleep(0.5)

				cprint("Proxy pool ({}):\n{}".format(len_pool, pool_str), 'cyan')

				ratio = log_copy['Successes'] / max(log_copy['Total'], .001)
				stats["Total"] += log_copy["Total"]
				stats["Successes"] += log_copy['Successes']
				total_ratio = stats['Successes'] / max(stats['Total'], .001)

				cprint("Timestep success rate: {}% ({}/{}). Time elapsed: ".format(ratio, log_copy['Successes'], log_copy['Total']) + str(time_elapsed), 'cyan')
				cprint("Accumulated success rate: {}% ({}/{}). Total time elapsed: ".format(total_ratio, stats['Successes'], stats['Total']) + str(total_time_elapsed), 'cyan')

				# Plot success rate over time
				ratio_ts.append(ratio)
				t_values = [float(x) for x in range(len(ratio_ts))]
				hp.plot(y_vals = ratio_ts, x_vals= t_values, num_x_chars=120, num_y_chars=30)

				cprint("Number of requests/timestep", 'cyan')
				n_requests.append(log_copy['Total'])
				t_values = [float(x) for x in range(len(ratio_ts))]
				hp.plot(y_vals = n_requests, x_vals= t_values, num_x_chars=120, num_y_chars=30)

				cprint("Successes/timestep", 'cyan')
				n_requests.append(log_copy['Successes'])
				t_values = [float(x) for x in range(len(ratio_ts))]
				hp.plot(y_vals = n_requests, x_vals= t_values, num_x_chars=120, num_y_chars=30)

			time.sleep(1) # If we sleep too much, the processesor will never schedule our job

		cprint("Plotting scraping progress to file...", 'cyan')
		t_values = [float(x) for x in range(len(ratio_ts))]
		hp.plot(y_vals = ratio_ts, x_vals= t_values)

		total_ratio = stats["Successes"] / max(stats["Total"], 0.0001)
		with open('Data/plot-{}.txt'.format(datetime.datetime.now()), "w") as f:
			with stdout_redirected(f):
				print("Total average success rate: {}% ({}/{})".format(total_ratio, stats["Successes"], stats["Total"]))
				print("Ended at timestep: {}".format(i))
				print("Proxy pool ({}):\n{}".format(len_pool, pool_str))
				hp.plot(y_vals = ratio_ts, x_vals= t_values, num_x_chars=240, num_y_chars=60)

		cprint("Terminating proxy manager", 'red')
		for i in self.injectors:
			i.terminate()
		self.fetcher.terminate()
		self.virtualiser.terminate()

	def reset_log(self, log):
		log['Successes'] = 0
		log['Total'] = 0

	def terminate(self):
		self.terminated.value = True

	''' End of terminator code '''

	'''
		Virtualiser:
		Create virtual proxies in the event of emergencies
		Virtual proxies will share side effects, like scoring & momentum
	'''

	def virtualiser(self):
		cprint("virtualiser running", 'yellow')
		while True:
			self.lock.acquire()
			in_use_no = len(self.proxy_pool.get_in_use())
			if in_use_no >= 1 and len(self.proxy_pool) < 50 and len(self.proxy_pool.get_virtual()) < in_use_no * self.n_virtual:
				created = self.proxy_pool.create_virtual_proxy(self.n_virtual)
				self.lock.release()
				if created:
					continue
				time.sleep(3)
			else:
				self.lock.release()
				time.sleep(0.5)

	def proxy_fetcher(self, queue):
		self.proxy_set = set()
		counter = 0
		print("proxy fetcher working")
		while True:
			# Get more proxies if not enough
			if len(self.proxy_set) < OPTIMUM_NO_PROXIES and counter % 180 == 0:
				new_proxy_set = tactics.fetch_proxies()
				self.proxy_set = self.proxy_set | new_proxy_set
				self.lock.acquire()
				all_in_pool = self.proxy_pool.all_proxies()
				self.lock.release()

				cprint("New proxies already in pool: {}".format(len(self.proxy_set & all_in_pool)), 'cyan')
				self.proxy_set = self.proxy_set - (self.proxy_set & all_in_pool)
				cprint("Accesed proxy fetch ({} new added)".format(len(self.proxy_set)), 'cyan')

			# Put proxies on queue if there is a deficit of real proxies and the queue is not jammed up
			self.lock.acquire()
			real_proxy_deficit = len(self.proxy_pool) - sum([len(virt) for virt in self.proxy_pool.get_virtual()])
			self.lock.release()

			if real_proxy_deficit < OPTIMUM_NO_PROXIES and queue.qsize() < 35 and len(self.proxy_set) > 0:
				proxy = self.proxy_set.pop()
				queue.put(proxy)
				continue

			time.sleep(1)
			counter += 1
			if counter == 30:
				print("Number of unverified proxies: {}. Time left to next fetch: {}s".format(len(self.proxy_set), 180 - counter % 180))

	def proxy_injector_worker(self, queue):
		while True:
			proxy = queue.get()
			self.test_proxy(proxy)
			time.sleep(1)

	def test_proxy(self, p):
		try:
			proxy = p[0] + ':' + p[1]
			ua = tactics.get_ua()
			url = random.choice(self.testing_urls)
			response = requests.get(url, proxies = {'http': proxy, 'https': proxy}, headers = {'user-agent': ua}, timeout=self.timeout)
			if response.status_code != 200:
				raise ValueError("Page not loaded correctly: {}".format(url))

			# If the pages load correctly in the given time, add them to the proxy pool
			self.lock.acquire()
			success = self.proxy_pool.add(pp.Proxy.from_2ple(p, ua))
			self.lock.release()
			if success:
				cprint("Successfully added: " + proxy + ".Tested on: " + url, 'cyan')
		except Exception as e:
			#print(e)
			pass

# Function to redirect stdout to file
@contextmanager
def stdout_redirected(new_stdout):
	save_stdout = sys.stdout
	sys.stdout = new_stdout
	try:
		yield None
	finally:
		sys.stdout = save_stdout
