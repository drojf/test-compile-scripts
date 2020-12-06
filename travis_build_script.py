import os
import shutil
import subprocess
import sys
import time


def is_windows():
	return sys.platform == "win32"


def call(args, **kwargs):
	print("running: {}".format(args))
	retcode = subprocess.call(args, shell=is_windows(), **kwargs) # use shell on windows
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


def zip(input_path, output_filename):
	try_remove_tree(output_filename)
	call(["7z", "a", output_filename, input_path])


def unzip(input_path):
	call(["7z", "x", input_path, '-y'])


def main():
	MAX_SCRIPT_COMPILE_TIME_SECONDS = 60 * 10 # time out after 10 minutes of trying to compile scripts

	print("--- Running 07th-Mod Installer Build using Python {} ---".format(sys.version))

	print("Python {}".format(sys.version))
	min_python = (3, 8)
	if not sys.version_info >= min_python:
		print(f"\nERROR: This script requires at least Python {min_python[0]}.{min_python[1]} to run")
		raise SystemExit(-1)

	# Extract the archive
	unzip('asdf.7z')

	# Copy the DLL
	shutil.copy('Assembly-CSharp.dll', 'Higurashi When They Cry Modded\\HigurashiEp01_Data\\Managed\\Assembly-CSharp.dll')

	# Run the exe as a separate process (It seems this runs in a blocking manner)
	# even though when run in windows cmd prompt it is non-blocking/new process?
	call(['Higurashi When They Cry Modded\\HigurashiEp01.exe', 'quitaftercompile'])

	# Wait for the "higu_script_compile_status.txt" file to be written before continuing
	# Not strictly necessary, but serves as a check that the scripts finished compiling/compiled correctly
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


if __name__ == '__main__':
	main()
