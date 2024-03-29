import sublime
import subprocess
import os
import subprocess
from .BackgroundWorker import BackgroundWorker
from . import TempFileUtils

def scp_exec(pargs):
	# BatchMode is to fail when server asked for password
	args = ["scp", "-oBatchMode=yes"]
	args.extend(pargs)
	try:
		subprocess.check_output(args, stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as ex:
		raise RuntimeError(ex.stderr.decode('utf8'))

def scp_download(window, host, remotepath, localpath, on_done, on_error):
	def on_error_int(ex):
		sublime.error_message(f"Error SCP to local. Note that password authentication is not supported.\n\n{ex}")
		try:
			TempFileUtils.delete_temp_file(localpath)
		except:
			pass
		on_error(ex)

	def do_scp(pargs):
		scp_exec(pargs)
		return localpath

	BackgroundWorker(
		lambda: do_scp((f'{host}:{remotepath}', localpath)),
		on_done,
		on_error_int,
		"Downloading remote file",
		window).start()

def scp_download_to_tempfile(window, host, remotepath, on_done, on_error):
	try:
		localpath = TempFileUtils.create_temp_file(host, remotepath)
	except Exception as ex:
		sublime.error_message(f"Error creating temporary directory: {ex}")
		return False
	print(f"SCP destination: {localpath}")

	scp_download(window, host, remotepath, localpath, on_done, on_error)
	# we succeeded in *creating* the download job, but not the download job itself!
	return True

def scp_save_to_remote(window, host, remotepath, localpath):
	def do_scp():
		scp_exec((localpath, f'{host}:{remotepath}'))

	def on_done(*args):
		window.status_message(f'{host}:{remotepath} saved')

	def on_error(ex):
		sublime.error_message(f"Error saving file via SCP.\n\n{ex}")

	BackgroundWorker(
		do_scp,
		on_done,
		on_error,
		"Saving remote file",
		window).start()
