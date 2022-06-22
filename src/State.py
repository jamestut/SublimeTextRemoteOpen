import sublime
import json
from os import path

FILE_NAME = None
_state_obj = None

def _init():
	global FILE_NAME
	# get ~/.local/Sublime Text/Local location
	# We'll store our persistence data there
	sublime_base_path, _ = path.split(sublime.packages_path())
	FILE_NAME = path.join(sublime_base_path, "Local/RemoteOpenState.json")

def load():
	global _state_obj
	if _state_obj is None:
		if not path.exists(FILE_NAME):
			_state_obj = {}
		else:
			with open(FILE_NAME, "r") as f:
				_state_obj = json.load(f)
	return _state_obj

def persist():
	global _state_obj
	if _state_obj:
		with open(FILE_NAME, "w") as f:
			json.dump(_state_obj, f)

_init()
