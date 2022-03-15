import sublime
import sublime_plugin
from .RemoteFileManager import manager

class RemoteOpenSsh(sublime_plugin.WindowCommand):
	def run(self):
		def on_done(v):
			manager.open_remote_path(self.window, v)
		self.window.show_input_panel("Remote file to open", "host:/path/to/file",
				on_done, None, None)

class TabContextCopyRemotePath(sublime_plugin.WindowCommand):
	def run(self, group, index):
		info = manager.get_info(self._get_view_id(group, index))
		if info is not None:
			sublime.set_clipboard(info.remotepath)

	def is_visible(self, group, index):
		info = manager.get_info(self._get_view_id(group, index))
		return info is not None

	def _get_view_id(self, group, index):
		return self.window.views_in_group(group)[index].id()
