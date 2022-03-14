import sublime
import sublime_plugin

from collections import namedtuple
import os
import tempfile
import subprocess

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
		localpath = _scp_temporary(host, remotepath)

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

_manager = RemoteFileManager()

class ViewListener(sublime_plugin.ViewEventListener):
	def on_load(self):
		info = _manager.get_info(self.view.id())
		if info is None:
			return
		_, filename = os.path.split(info.remotepath)
		self.view.set_name(f"(SSH) {info.host}: {filename}")
		self.view.set_read_only(True)
		self.view.set_scratch(True)

	def on_close(self):
		_manager.handle_view_closed(self.view.id())

class RemoteOpenSsh(sublime_plugin.WindowCommand):
	def run(self):
		def on_done(v):
			_manager.open_remote_path(self.window, v)
		self.window.show_input_panel("Remote file to open", "host:/path/to/file",
				on_done, None, None)

class TabContextCopyRemotePath(sublime_plugin.WindowCommand):
	def run(self, group, index):
		info = _manager.get_info(self._get_view_id(group, index))
		if info is not None:
			sublime.set_clipboard(info.remotepath)

	def is_visible(self, group, index):
		info = _manager.get_info(self._get_view_id(group, index))
		return info is not None

	def _get_view_id(self, group, index):
		return self.window.views_in_group(group)[index].id()

def _scp_exec(pargs):
	# BatchMode is to fail when server asked for password
	args = ["scp", "-oBatchMode=yes"]
	args.extend(pargs)
	try:
		subprocess.check_output(args, stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as ex:
		raise RuntimeError(ex.stderr.decode('utf8'))

def _scp_temporary(host, remotepath):
	# work out the extension of the remote file
	_, filename = os.path.split(remotepath)
	suffix = None
	if '.' in filename:
		_, suffix = filename.rsplit('.', 1)

	try:
		fd, localpath = tempfile.mkstemp(suffix=f'.{suffix}')
	except Exception as ex:
		sublime.error_message(f"Error creating temporary file: {ex}")
		return None

	# we don't need the fd handle as SCP will do the job
	os.close(fd)

	try:
		_scp_exec((f'{host}:{remotepath}', localpath))
	except Exception as ex:
		sublime.error_message(f"Error SCP to local. Note that password authentication is not supported.\n\n{ex}")
		try:
			os.unlink(localpath)
		except:
			pass
		return None

	# OK
	return localpath
