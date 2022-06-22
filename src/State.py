import sublime

BASE_NAME = "RemoteOpen"

def load():
	return sublime.load_settings(BASE_NAME)

def persist():
	sublime.save_settings(BASE_NAME)
