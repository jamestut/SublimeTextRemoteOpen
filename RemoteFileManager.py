import sublime
import sublime_plugin

from collections import namedtuple
import os
import tempfile
import subprocess
from . import ScpUtils

class RemoteFileManager():
	_ViewInfo = namedtuple('ViewInfo', ['host','remotepath','localpath','view'])

	def __init__(self):
		self._idmap = {}
		# map key: pair (host, remotepath) | value: view id
		self._pathmap = {}
		# map key: window id | value: last opened hostname
		self._last_hostname = {}

	def get_info(self, viewid):
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
			os.unlink(info.localpath)
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

		sublime.status_message(f'Opening file from {host}:{remotepath} ...')
		localpath = ScpUtils.scp_download_to_tempfile(host, remotepath)

		# add to structure
		if localpath is not None:
			view = window.open_file(localpath)
			viewid = view.id()
			info = self._ViewInfo(host, remotepath, localpath, view)
			self._idmap[viewid] = info
			self._pathmap[pathkey] = viewid

		sublime.status_message('')

	def open_remote_path(self, window, query):
		splt = query.split(":", 1)
		if len(splt) == 2:
			host, remotepath = splt
			self._last_hostname[window.id()] = host
			self.open_remote_ssh_path(window, host, remotepath)
		else:
			host = self._last_hostname.get(window.id(), None)
			if host is None:
				sublime.error_message("Please specify host name!"
					" You can omit hostname for the consequent open requests.")
				return
			self.open_remote_ssh_path(window, host, query)

manager = RemoteFileManager()
