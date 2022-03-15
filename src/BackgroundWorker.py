import threading

class BackgroundWorker(threading.Thread):
	def __init__(self, func, on_done, on_error, progmsg=None, progwindow=None):
		threading.Thread.__init__(self)
		self._func = func
		self._on_done = on_done
		self._on_error = on_error
		self._progmsg = progmsg
		self._progwindow = progwindow

	def run(self, *args, **kwargs):
		# start another thread to show progress message
		progupd = None
		if self._progmsg:
			assert self._progwindow is not None
			progupd = _ProgressUpdater(self._progmsg, self._progwindow)
			progupd.start()

		try:
			ret = self._func()
			if self._on_done:
				self._on_done(ret)
		except Exception as ex:
			if self._on_error:
				self._on_error(ex)
		finally:
			if progupd:
				progupd.stop()

class _ProgressUpdater(threading.Thread):
	def __init__(self, msg, window):
		threading.Thread.__init__(self)
		self._msg = msg
		self._window = window
		# in second
		self._interval = 0.2
		self._event = threading.Event()

	def run(self, *args, **kwargs):
		ctr = 0
		while True:
			self._window.status_message(f'{self._msg} {"." * ctr}')
			if self._event.wait(self._interval):
				# request to stop
				self._window.status_message('')
				break
			ctr = (ctr + 1) % 4

	def stop(self):
		self._event.set()
