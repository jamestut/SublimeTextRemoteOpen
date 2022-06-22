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
			info = manager.get_view_pathkey(curr_view)
			if info is not None:
				host, remotepath = info
				def_text = f"{host}:{remotepath}"
		self.window.show_input_panel("Remote file to open", def_text,
				on_done, None, None)

class CommonContextCmd(sublime_plugin.WindowCommand):
	def _get_view(self, group, index):
		if group < 0 or index < 0:
			return sublime.active_window().active_view()
		else:
			return self.window.views_in_group(group)[index]

class TabContextCopyRemotePath(CommonContextCmd):
	def run(self, group, index):
		info = manager.get_view_pathkey(self._get_view(group, index))
		if info is not None:
			_, remotepath = info
			sublime.set_clipboard(remotepath)

	def is_visible(self, group, index):
		return manager.is_view_managed(self._get_view(group, index))

class ReloadRemote(CommonContextCmd):
	def run(self, group=-1, index=-1):
		view = self._get_view(group, index)
		info = manager.get_view_pathkey(view)
		if info is None:
			return
		host, remotepath = info
		localpath = view.buffer().file_name()
		ScpUtils.scp_download(self.window, host, remotepath, localpath, None)

	def is_visible(self, group=-1, index=-1):
		return manager.is_view_managed(self._get_view(group, index))
