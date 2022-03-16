import sublime
import sublime_plugin
from .RemoteFileManager import manager
import os

class ViewListener(sublime_plugin.ViewEventListener):
	def on_load(self):
		info = manager.get_info(self.view.id())
		if info is None:
			return
		_, filename = os.path.split(info.remotepath)

	def on_close(self):
		manager.handle_view_closed(self.view.id())

	def on_post_save(self):
		manager.save_remote_ssh_path(self.view.id())
