import subprocess
import os

def scp_exec(pargs):
	# BatchMode is to fail when server asked for password
	args = ["scp", "-oBatchMode=yes"]
	args.extend(pargs)
	try:
		subprocess.check_output(args, stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as ex:
		raise RuntimeError(ex.stderr.decode('utf8'))

def scp_download_to_tempfile(host, remotepath):
	# work out the extension of the remote file
	_, filename = os.path.split(remotepath)
	suffix = None
	if '.' in filename:
		_, suffix = filename.rsplit('.', 1)

	try:
		fd, localpath = tempfile.mkstemp(suffix=f'.{suffix}')
	except Exception as ex:
		sublime.error_message(f"Error creating temporary file: {ex}")
		return None

	# we don't need the fd handle as SCP will do the job
	os.close(fd)

	try:
		scp_exec((f'{host}:{remotepath}', localpath))
	except Exception as ex:
		sublime.error_message(f"Error SCP to local. Note that password authentication is not supported.\n\n{ex}")
		try:
			os.unlink(localpath)
		except:
			pass
		return None

	# OK
	return localpath
