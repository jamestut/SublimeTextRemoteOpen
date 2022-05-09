import sublime
import sublime_plugin

from collections import namedtuple
import os
import threading
from . import ScpUtils
from .TempFileUtils import delete_temp_file

class RemoteFileManager():
	_ViewInfo = namedtuple('ViewInfo', ['host','remotepath','localpath','view'])

	def __init__(self):
		self._idmap = {}
		# map key: pair (host, remotepath) | value: view id
		self._pathmap = {}
		# map key: window id | value: last opened hostname
		self._last_hostname = {}
		self._lock = threading.Lock()

	def get_info(self, viewid):
		# we need lock here because we expect this function to be called by ViewListener
		# after the SCP operation finishes. There is a race between ST's calling of
		# on_load vs whether we've put the views into _idmap
		with self._lock:
			return self._idmap.get(viewid, None)

	def get_view_id(self, host, remotepath):
		return _pathmap.get((host, remotepath), None)

	def handle_view_closed(self, viewid):
		info = self._idmap.get(viewid, None)
		if info is None:
			return
		del self._idmap[viewid]
		del self._pathmap[(info.host, info.remotepath)]
		try:
			delete_temp_file(info.localpath)
		except Exception as ex:
			sublime.error_message(f"Error deleting temporary file '{info.localpath}': {ex}")

	def open_remote_ssh_path(self, window, host, remotepath):
		pathkey = (host, remotepath)
		viewid = self._pathmap.get(pathkey, None)
		if viewid is not None:
			view = self._idmap[viewid].view
			window = view.window()
			window.focus_view(view)
			return

		def on_finish(localpath):
			if localpath is not None:
				# see `get_info` why this lock is needed
				with self._lock:
					view = window.open_file(localpath)
					viewid = view.id()
					info = self._ViewInfo(host, remotepath, localpath, view)
					self._idmap[viewid] = info
					self._pathmap[pathkey] = viewid

		ScpUtils.scp_download_to_tempfile(window, host, remotepath, on_finish)

	def save_remote_ssh_path(self, viewid):
		info = self.get_info(viewid)
		if info is None:
			return

		ScpUtils.scp_save_to_remote(info.view.window(),
			info.host, info.remotepath, info.localpath)

	def open_remote_path(self, window, query):
		if query.strip() == "":
			# assume cancel
			return
		splt = query.split(":", 1)

		# for hostname, prioritize current view first, then current window
		curr_view = window.active_view()
		info = self.get_info(curr_view.id()) if curr_view else None
		default_host = info.host if info else self._last_hostname.get(window.id(), None)
		# for the default dir, only consider curent view
		# we don't store default_dir for current window because it will be an extra work
		# to determine whether the file loading were successful or not
		default_dir = os.path.split(info.remotepath)[0] if info else None

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
				return
			remotepath = os.path.join(default_dir, remotepath)

		if host is None:
			sublime.error_message("Please specify host name!"
				" You can omit hostname for the consequent open requests.")
			return

		self._last_hostname[window.id()] = host
		self.open_remote_ssh_path(window, host, remotepath)

manager = RemoteFileManager()
