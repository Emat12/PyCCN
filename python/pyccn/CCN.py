#
# Copyright (c) 2011, Regents of the University of California
# BSD license, See the COPYING file for more information
# Written by: Derek Kulinski <takeda@takeda.tk>
#             Jeff Burke <jburke@ucla.edu>
#

from . import _pyccn
import select, time
import threading, dummy_threading

# Fronts ccn

# ccn_handle is opaque to c struct

class CCN(object):
	def __init__(self):
		self._handle_lock = threading.Lock()
		self.ccn_data = _pyccn._pyccn_ccn_create()
		_pyccn._pyccn_ccn_connect(self.ccn_data)

	def _acquire_lock(self):
		if not _pyccn.is_upcall_executing(self.ccn_data):
			#print("acquiring lock")
			self._handle_lock.acquire()
			#print("lock acquired")

	def _release_lock(self):
		if not _pyccn.is_upcall_executing(self.ccn_data):
			#print("releasing lock")
			self._handle_lock.release()
			#print("lock released")

	def fileno(self):
		return _pyccn.get_connection_fd(self.ccn_data)

	def process_scheduled(self):
		assert(_pyccn.is_upcall_executing(None) == -1)
		self._handle_lock.acquire()
		try:
			return _pyccn.process_scheduled_operations(self.ccn_data)
		finally:
			self._handle_lock.release()

	def output_is_pending(self):
		assert(_pyccn.is_upcall_executing(None) == -1)
		self._handle_lock.acquire()
		try:
			return _pyccn.output_is_pending(self.ccn_data)
		finally:
			self._handle_lock.release()

	def run(self, timeoutms):
		assert(_pyccn.is_upcall_executing(None) == -1)
		self._handle_lock.acquire()
		try:
			_pyccn._pyccn_ccn_run(self.ccn_data, timeoutms)
		finally:
			self._handle_lock.release()

	def setRunTimeout(self, timeoutms):
		#self._acquire_lock()
		#try:
			_pyccn._pyccn_ccn_set_run_timeout(self.ccn_data, timeoutms)
		#finally:
			#self._release_lock

	# Application-focused methods
	#
	def expressInterest(self, name, closure, template=None):
		self._acquire_lock()
		try:
			return _pyccn._pyccn_ccn_express_interest(self, name, closure, template)
		finally:
			self._release_lock()

	def setInterestFilter(self, name, closure, flags = None):
		self._acquire_lock()
		try:
			if flags is None:
				return _pyccn._pyccn_ccn_set_interest_filter(self.ccn_data, name.ccn_data, closure)
			else:
				return _pyccn._pyccn_ccn_set_interest_filter(self.ccn_data, name.ccn_data, closure, flags)
		finally:
			self._release_lock()

	# Blocking!
	def get(self, name, template = None, timeoutms = 3000):
		self._acquire_lock()
		try:
			return _pyccn._pyccn_ccn_get(self, name, template, timeoutms)
		finally:
			self._release_lock()

	def put(self, contentObject):
		self._acquire_lock()
		try:
			return _pyccn._pyccn_ccn_put(self, contentObject)
		finally:
			self._release_lock()

	def getDefaultKey(self):
		return _pyccn.get_default_key()

class EventLoop(object):
	def __init__(self, *handles):
		self.running = False
		self.fds = {}
		for handle in handles:
			self.fds[handle.fileno()] = handle

	def run_scheduled(self):
		wait = {}
		for fd, handle in zip(self.fds.keys(), self.fds.values()):
			wait[fd] = handle.process_scheduled()
		return wait[sorted(wait, key=wait.get)[0]] / 1000.0

	#
	# version that uses poll (might not work on Mac)
	#
	#def run_once(self):
	#	fd_state = select.poll()
	#	for handle in self.fds.values():
	#		flags = select.POLLIN
	#		if (handle.output_is_pending()):
	#			flags |= select.POLLOUT
	#		fd_state.register(handle, flags)
	#
	#	timeout = min(self.run_scheduled(), 1000)
	#
	#	res = fd_state.poll(timeout)
	#	for fd, event in res:
	#		self.fds[fd].run(0)

	def run_once(self):
		fd_read = self.fds.values()
		fd_write = []
		for handle in self.fds.values():
			if handle.output_is_pending():
				fd_write.append(handle)

		timeout = min(self.run_scheduled(), 1000)

		res = select.select(fd_read, fd_write, [], timeout)

		handles = set(res[0]).union(res[1])
		for handle in handles:
			handle.run(0)

	def run(self):
		self.running = True
		while self.running:
			self.run_once()

	def stop(self):
		self.running = False
