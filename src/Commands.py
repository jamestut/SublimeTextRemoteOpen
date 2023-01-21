import sublime
import sublime_plugin
from .RemoteFileManager import manager
from .PathCopier import copy_remote_path
from . import ScpUtils

class RemoteSshOpen(sublime_plugin.WindowCommand):
	def run(self):
		def on_done(v):
			manager.open_remote_path(self.window, v)

		view = self.window.active_view()
		self.window.show_input_panel("Remote file to open",
				manager.default_prefill(view), on_done, None, None)

class CommonContextCmd(sublime_plugin.WindowCommand):
	def _get_view(self, group, index):
		if group < 0 or index < 0:
			return sublime.active_window().active_view()
		else:
			return self.window.views_in_group(group)[index]

class RemoteSshTabContextCopyRemotePath(CommonContextCmd):
	def run(self, group, index):
		view = self._get_view(group, index)
		copy_remote_path(view, False)

	def is_visible(self, group, index):
		view = self._get_view(group, index)
		return copy_remote_path(view, False, check_only=True)

class RemoteSshTextContextCopyRemotePath(sublime_plugin.TextCommand):
	def run(self, _):
		copy_remote_path(self.view, True)

	def is_visible(self):
		return copy_remote_path(self.view, True, check_only=True)

class RemoteSshReload(CommonContextCmd):
	def run(self, group=-1, index=-1):
		view = self._get_view(group, index)
		info = manager.get_view_pathkey(view)
		if info is None:
			return
		host, remotepath = info
		localpath = view.buffer().file_name()
		ScpUtils.scp_download(self.window, host, remotepath, localpath, None, None)

	def is_visible(self, group=-1, index=-1):
		return manager.is_view_managed(self._get_view(group, index))

class RemoteSshShowOpened(sublime_plugin.WindowCommand):
	def run(self, *args):
		opened = manager.get_all_opened()

		def on_select(idx):
			if idx < 0:
				return
			host, remotepath = opened[idx]
			manager.open_remote_ssh_path(self.window, host, remotepath)

		self.window.show_quick_panel([f"{host}:{remotepath}"
			for host, remotepath in opened], on_select)

class RemoteSshCopyPath(sublime_plugin.WindowCommand):
	def run(self, lineno):
		view = self._get_view()
		copy_remote_path(view, lineno)

	def is_visible(self, lineno):
		view = self._get_view()
		return copy_remote_path(view, lineno, check_only=True)

	def _get_view(self):
		return self.window.active_view()
