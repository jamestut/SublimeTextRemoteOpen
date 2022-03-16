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
		self.view.set_read_only(True)
		self.view.set_scratch(True)

	def on_close(self):
		manager.handle_view_closed(self.view.id())
