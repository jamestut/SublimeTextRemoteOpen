import sublime
from .RemoteFileManager import manager

def copy_remote_path(view, lineno, check_only=False):
	if not view:
		return False
	window = view.window()
	if not manager.is_view_managed(view):
		return False
	_, remotepath = manager.get_view_pathkey(view)

	if lineno:
		if not view.sel():
			return False
		if not check_only:
			# 1-based index
			lineno = view.rowcol(view.sel()[0].begin())[0] + 1
			_do_copy(window, f"{remotepath}:{lineno}")
	else:
		if not check_only:
			_do_copy(window, remotepath)
	return True

def _do_copy(window, text):
	sublime.set_clipboard(text)
	window.status_message(f"Copied: {text}")
