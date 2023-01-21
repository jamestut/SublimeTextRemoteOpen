import sublime
import sublime_plugin

from collections import namedtuple
import os
import threading
from . import ScpUtils, State
from .TempFileUtils import delete_temp_file

class RemoteFileManager():
	def __init__(self):
		# map key: buffer ID | value: pair(host, remotepath)
		# used to quickly determine whether to show remote-related commands
		self._bidmap = {}

		# map key: pair(host, remotepath) | value: [localpath, refcount of open buffers]
		self._pathmap = {}
		# map key: localpath | value: pair(host, remotepath)
		self._rpathmap = {}

		# map key: window id | value: last opened hostname
		self._last_hostname = {}

		# map key: window id | value: last entered text that failed
		# we want user to be able to easily revise things if they entered things errorneously
		self._last_failed_entry = {}

		self._ppathmap = None

	def _persisted_pathmap(self):
		if self._ppathmap is None:
			ret = State.load().setdefault("pathmap", {})
			# convert all list to tuple
			for k, v in ret.items():
				if type(v) is list:
					ret[k] = tuple(v)
			self._ppathmap = ret
		return self._ppathmap

	def load_persistence(self):
		# load pathmap and rpathmap
		ppathmap = self._persisted_pathmap()
		nonexistent = []
		for localpath, pathkey in ppathmap.items():
			# we store these temp files in OS temporary folder, which might be regularly
			# cleaned up. If we didn't find such files, stop managing it
			if not os.path.exists(localpath):
				nonexistent.append(localpath)
				continue
			self._pathmap[pathkey] = [localpath, 0]
			self._rpathmap[localpath] = pathkey

		if nonexistent:
			for v in nonexistent:
				del ppathmap[v]
			State.persist()

	def _unmanage(self, host, remotepath):
		"""
		Stop managing the given file
		"""
		pathkey = (host, remotepath)
		localpath, _ = self._pathmap[pathkey]
		del self._pathmap[pathkey]
		del self._rpathmap[localpath]

		del self._persisted_pathmap()[localpath]
		State.persist()

		try:
			delete_temp_file(localpath)
		except Exception as ex:
			sublime.error_message(f"Error deleting temporary file '{info.localpath}': {ex}")

	def _manage(self, host, remotepath, localpath, initrefcount=0):
		assert localpath not in self._rpathmap
		pathkey = (host, remotepath)
		self._pathmap[pathkey] = [localpath, initrefcount]
		self._rpathmap[localpath] = pathkey

		self._persisted_pathmap()[localpath] = pathkey
		State.persist()

	def handle_view_closed(self, view):
		buff = view.buffer()
		buffid = buff.id()
		pathkey = self._bidmap.get(buffid, None)
		if pathkey is None:
			return

		# proceed only after all views for this buffer are closed
		# >1 check because the view that trigerred on_close will still persist in buff.views(),
		# conversely if buff.views() only contain 1 view, then this must be the view that
		# triggered this on_close.
		if len(buff.views()) > 1:
			return

		del self._bidmap[buffid]

		status = self._pathmap[pathkey]
		status[1] -= 1
		# if reference count reaches zero (e.g. no more buffers opening this file),
		# then delete the file
		if not status[1]:
			print(f"No more buffers are referring to {pathkey[0]}:{pathkey[1]}. Cleaning up.")
			self._unmanage(*pathkey)

	def handle_view_opened(self, view):
		buff = view.buffer()
		buffid = buff.id()
		if buffid in self._bidmap or buff.file_name() is None:
			# already managed or new unsaved file
			return

		# is the localpath something that we manage?
		localpath = os.path.realpath(buff.file_name())
		pathkey = self._rpathmap.get(localpath, None)
		if pathkey:
			self._bidmap[buffid] = pathkey
			# increment refcount
			self._pathmap[pathkey][1] += 1

	def is_view_managed(self, view):
		return view.buffer_id() in self._bidmap

	def get_view_pathkey(self, view):
		return self._bidmap.get(view.buffer_id(), None)

	def get_all_opened(self):
		return list(self._pathmap)

	def open_remote_ssh_path(self, window, host, remotepath, on_finish, on_error):
		pathkey = (host, remotepath)
		status = self._pathmap.get(pathkey, None)
		if status is not None:
			# we already manage this file: open it instead of redownloading
			window.open_file(status[0])
			on_finish()
			return True

		def on_finish_int(localpath):
			# canonicalize file name, resolving symlinks, etc
			localpath = os.path.realpath(localpath)
			self._manage(host, remotepath, localpath)
			window.open_file(localpath)
			print(f"Opened {host}:{remotepath} as {localpath}")
			on_finish()

		return ScpUtils.scp_download_to_tempfile(window, host, remotepath,
			on_finish_int, on_error)

	def save_remote_ssh_path(self, view):
		buffid = view.buffer_id()
		pathkey = self._bidmap.get(buffid, None)
		if pathkey is None:
			return
		host, remotepath = pathkey
		localpath, _ = self._pathmap[pathkey]
		ScpUtils.scp_save_to_remote(view.window(), host, remotepath, localpath)

	def open_remote_path(self, window, query):
		def on_success(*args):
			# clear user's failed entered input
			if window.id() in self._last_failed_entry:
				del self._last_failed_entry[window.id()]

		def on_error(*args):
			self._last_failed_entry[window.id()] = query

		if query.strip() == "":
			# assume cancel
			return
		splt = query.split(":", 1)

		# for hostname, prioritize current view first, then current window
		currview = window.active_view()
		host, remotepath = self.get_view_pathkey(currview) or (None, None)
		default_host = host or self._last_hostname.get(window.id(), None)
		# for the default dir, only consider curent view
		# we don't store default_dir for current window because it will be an extra work
		# to determine whether the file loading were successful or not
		default_dir = os.path.split(remotepath)[0] if remotepath else None

		if len(splt) == 2:
			host, remotepath = splt
		elif len(splt) == 1:
			host, remotepath = None, splt[0]

		if host is None:
			host = default_host
		if remotepath[0] != "/":
			if default_dir is None:
				sublime.error_message("Please specify absolute path!"
					" You can specify relative path for the consequent open reqeuests.")
				on_error()
				return
			remotepath = os.path.join(default_dir, remotepath)

		if host is None:
			sublime.error_message("Please specify host name!"
				" You can omit hostname for the consequent open requests.")
			on_error()
			return

		self._last_hostname[window.id()] = host
		if not self.open_remote_ssh_path(window, host, remotepath, on_success, on_error):
			sublime.error_message("Error creating temporary file.")
			on_error()
			return

	def default_prefill(self, view):
		# returns the default prefilled text when user invokes the SSH open command
		default = "host:/path/to/file"
		if view is None:
			return default

		# prioritize what user's entered previously if failing (unique per window)
		window = view.window()
		if window and window.id() in self._last_failed_entry:
			return self._last_failed_entry[window.id()]

		# otherwise, show the current view's remote path
		info = self.get_view_pathkey(view)
		if info is not None:
			host, remotepath = info
			return f"{host}:{remotepath}"

		return default

manager = RemoteFileManager()
