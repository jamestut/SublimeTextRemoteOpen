import sublime
import sublime_plugin
from .RemoteFileManager import manager
from . import ScpUtils

class RemoteOpenSsh(sublime_plugin.WindowCommand):
	def run(self):
		def on_done(v):
			manager.open_remote_path(self.window, v)

		# determine default text
		def_text = "host:/path/to/file"
		curr_view = self.window.active_view()
		if curr_view is not None:
			info = manager.get_info(curr_view.id())
			if info is not None:
				def_text = f"{info.host}:{info.remotepath}"
		self.window.show_input_panel("Remote file to open", def_text,
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

class ReloadRemote(sublime_plugin.WindowCommand):
	def run(self, group=-1, index=-1):
		info = self._get_info(group, index)
		if info is None:
			return
		ScpUtils.scp_download(self.window, info.host, info.remotepath, info.localpath, None)

	def is_visible(self, group=-1, index=-1):
		info = self._get_info(group, index)
		return info is not None

	def _get_info(self, group, index):
		if group < 0 or index < 0:
			view = sublime.active_window().active_view()
		else:
			view = self.window.views_in_group(group)[index]
		return manager.get_info(view.id())
