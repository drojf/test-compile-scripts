from __future__ import unicode_literals

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import datetime
import platform
import tempfile
import time

from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen

MAX_SCRIPT_COMPILE_TIME_SECONDS = 60 * 10 # time out after 10 minutes of trying to compile scripts

print("--- Running 07th-Mod Installer Build using Python {} ---".format(sys.version))

BUILD_LINUX_MAC = True
# If user specified which platform to build for, use that platform. Otherwise, attempt to detect platform automatically.
if len(sys.argv) == 2:
	if "win" in sys.argv[1].lower():
		BUILD_LINUX_MAC = False
else:
	BUILD_LINUX_MAC = not (platform.system() == "Windows")

print(f"Building Linux Mac: {BUILD_LINUX_MAC}")

IS_WINDOWS = sys.platform == "win32"

EMBEDDED_PYTHON_ZIP_URL = "https://www.python.org/ftp/python/3.7.7/python-3.7.7-embed-win32.zip"

def call(args, **kwargs):
	print("running: {}".format(args))
	retcode = subprocess.call(args, shell=IS_WINDOWS, **kwargs) # use shell on windows
	if retcode != 0:
		raise SystemExit(retcode)


def try_remove_tree(path):
	try:
		if os.path.isdir(path):
			shutil.rmtree(path)
		else:
			os.remove(path)
	except FileNotFoundError:
		pass

# From https://stackoverflow.com/a/12526809/848627, but modified to use scandir
def clear_folder_if_exists(path):
	if not os.path.exists(path):
		return

	with os.scandir(path) as entries:
		for entry in entries:
			try:
				shutil.rmtree(entry.path)
			except OSError:
				os.remove(entry.path)

def zip(input_path, output_filename):
	try_remove_tree(output_filename)
	call(["7z", "a", output_filename, input_path])

def unzip(input_path):
	call(["7z", "x", input_path, '-y'])

def tar_gz(input_path, output_filename: str):
	try_remove_tree(output_filename)
	tempFileName = re.sub("\\.gz", "", output_filename, re.IGNORECASE)
	call(["7z", "a", tempFileName, input_path])
	call(["7z", "a", output_filename, tempFileName])
	os.remove(tempFileName)

print("Python {}".format(sys.version))
min_python = (3, 8)
if not sys.version_info >= min_python:
	print(f"\nERROR: This script requires at least Python {min_python[0]}.{min_python[1]} to run")
	raise SystemExit(-1)

print("\nTravis python build script started\n")


# first, copy the files we want into a staging folder
staging_folder = os.path.join(tempfile.gettempdir(), '07th-mod_patcher_staging')
output_folder = 'travis_installer_output'
bootstrap_copy_folder = 'travis_installer_bootstrap_copy'

# Extract the archive
unzip('asdf.7z')

# Run the exe as a separate process (It seems this runs in a blocking manner)
# even though when run in windows cmd prompt it is non-blocking/new process?
call(['Higurashi When They Cry Modded\\HigurashiEp01.exe', 'quitaftercompile'])

# Wait for the "higu_script_compile_status.txt" file to be written before continuing
for i in range(MAX_SCRIPT_COMPILE_TIME_SECONDS):
	if os.path.exists('higu_script_compile_status.txt'):
		break
	print(f"Waiting for scripts to compile... ({i})")
	time.sleep(1)
else:
	print(f"ERROR: Timed out after {MAX_SCRIPT_COMPILE_TIME_SECONDS} seconds trying to compile scripts")
	raise SystemExit(-1)

# Wait 3 seconds
print("Waiting an extra 3 seconds for things to settle...")
time.sleep(3)

# Compress the compiled scripts into the output file
output_path = 'out.zip'
zip('Higurashi When They Cry Modded\\HigurashiEp01_Data\\StreamingAssets\\CompiledUpdateScripts', output_path)

print(f"\n\nFinished Compiling Scripts - output to {os.path.abspath(output_path)}")
