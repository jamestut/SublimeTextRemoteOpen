import tempfile
import os

def _filter_name(v):
	return v.replace("/", "-")

def create_temp_file(host, remotepath):
	basedir = tempfile.mkdtemp(suffix=f"-{_filter_name(host)}")
	_, filename = os.path.split(remotepath)
	return os.path.join(basedir, filename)

def delete_temp_file(localpath):
	basedir, filename = os.path.split(localpath)

	def ignore_not_found(cmd):
		try:
			cmd()
		except FileNotFoundError:
			pass

	ignore_not_found(lambda: os.unlink(localpath))
	ignore_not_found(lambda: os.rmdir(basedir))
