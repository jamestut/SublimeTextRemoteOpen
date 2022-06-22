import sublime
import sublime_plugin
from .RemoteFileManager import manager
import os

class ViewListener(sublime_plugin.ViewEventListener):
	def on_load(self):
		manager.handle_view_opened(self.view)

	def on_close(self):
		manager.handle_view_closed(self.view)

	def on_post_save(self):
		manager.save_remote_ssh_path(self.view)
