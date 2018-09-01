try:
	from . import multiproxy
	from . import tactics
	from . import proxypool as pp
	from . import loggingpool as lp
except:
	import multiproxy
	import tactics
	import proxypool as pp
	import loggingpool as lp

import multiprocessing
from multiprocessing import Process, Pool, Manager, Lock
from termcolor import cprint
from functools import partial
import time
import datetime


# Multihandler handles multiprocessing
class MultiRequestHandler:
	def __init__(self, batch_handler, N_PROCESS):
		self.manager = pp.ProxyManager()
		self.manager.start()
		self.process_pool = Pool(processes = N_PROCESS)
		self.n_process = N_PROCESS

		N_VIRTUAL = 3

		self.proxy_pool = self.manager.proxy_pool()
		self.lock = self.manager.Lock()
		self.log = Manager().dict()
		self.log['Successes'] = 0
		self.log['Total'] = 0

		self.proxy_handler = multiproxy.MultiProxyHandler(self.proxy_pool, self.lock, self.log, N_VIRTUAL, 100, 10, 120)
		self.batch_handler = partial(batch_handler, self.proxy_pool, self.lock, self.log)

		self.TIME_TO_WAIT = 3

	def run(self, data):
		#Debugging multiple processes:logger = multiprocessing.log_to_stderr(logging.INFO)
		multiprocessing.log_to_stderr()
		stagger_amount = min(self.n_process, len(data)) + 2
		waiting_time = [self.TIME_TO_WAIT * max(n, 0) for n in range(stagger_amount, stagger_amount - len(data), -1)]
		proxy_process = Process(target = self.proxy_handler.run)
		proxy_process.start()
		start_time = datetime.datetime.now()
		parallel = self.process_pool.map_async(self.batch_handler, zip(waiting_time, list(data.values())), chunksize = 1)

		# Print progress messages
		data_len = len(data)
		i = 0
		while not parallel.ready():
			i +=1
			if i == 10:
				cprint("Batches completed: {}/{}.".format(data_len - parallel._number_left, data_len), 'magenta')
				i = 0
			time.sleep(1)
		cprint("Attempting to terminate", 'red')
		self.proxy_handler.terminate()
		result = parallel.get()
		self.process_pool.close()
		self.process_pool.join()
		proxy_process.join()

		end_time = datetime.datetime.now()
		cprint("Done. Time taken: " + str(end_time - start_time), 'red')
		return result

# BATCH_SIZE * N_BATCH = N in MultiBatch
# fn must have the following arguments: proxy_pool, lock, data_batch
class MultiRequest:
	def __init__(self, raw_data, batch_handler, BATCH_SIZE, N_PROCESS):
		self.batch_handler = batch_handler
		self.data = batch(raw_data, BATCH_SIZE)
		self.n_process = N_PROCESS

	def run(self):
		cprint("Number of batches: {}".format(len(self.data)), 'magenta')
		handler = MultiRequestHandler(self.batch_handler, self.n_process)
		result = handler.run(self.data)
		return result

def batch(raw_data, batch_size):
	mb_data = {}
	data_left = len(raw_data)

	j = 0
	while data_left > 0:
		to_consume = min(batch_size, data_left)
		mb_data[j] = raw_data[j * batch_size : (j + 1) * to_consume]
		data_left -= to_consume
		j += 1
	return mb_data
