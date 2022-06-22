import sublime
from .src.Commands import *
from .src.ViewListener import *
from .src.RemoteFileManager import manager

def plugin_loaded():
	return
	for w in sublime.windows():
		for v in w.views():
			manager.handle_view_opened(v)
