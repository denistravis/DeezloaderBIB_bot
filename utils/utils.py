#!/usr/bin/python3

from urllib.parse import urlparse
from requests import get as req_get
from shutil import disk_usage, rmtree
from helpers.db_help import initialize_db
from libtmux import Server as tmux_server
from .converter_bytes import convert_bytes_to
from deezloader.libutils.utils import var_excape
from deezloader.deezloader.deezer_settings import qualities

from configs.bot_settings import (
	output_songs, supported_link, output_shazam,
	log_errors, log_downloads,
	log_uploads, logs_path
)

from os import (
	walk, listdir, mkdir,
	remove, system,
	name as os_name
)

from os.path import (
	getsize, join,
	islink, isdir, exists
)

def check_config_file(config):
	if not "token" in config['deez_login']:
		print("Something went wrong with the login token in the configuration file")
		exit()

	if (
		not "api_id" in config['pyrogram']
	) or (
		not "api_hash" in config['pyrogram']
	):
		print("Something went wrong with pyrogram in the configuration file")
		exit()

	if not "bot_token" in config['telegram']:
		print("Something went wrong with the telegram token in the configuration file")
		exit()

	if (
		not "key" in config['acrcloud']
	) or (
		not "secret" in config['acrcloud']
	) or (
		not "host" in config['acrcloud']
	):
		print("Something went wrong with acrcloud in the configuration file")
		exit()

def is_supported_link(link):
	is_supported = True
	netloc = urlparse(link).netloc

	if not any(
		c_link == netloc
		for c_link in supported_link
	):
		return False

	return is_supported

def set_path(tag, song_quality, file_format, method):
	album = tag['album']
	album = __var_excape(album)

	if method == 0:
		discnum = tag['discnum']
		tracknum = tag['tracknum']
		song_name = f"{album} CD {discnum} TRACK {tracknum}"

	elif method == 1:
		artist = __var_excape(tag['artist'])
		music = __var_excape(tag['music'])
		song_name = f"{music} - {artist}"

	elif method == 2:
		artist = __var_excape(tag['artist'])
		music = __var_excape(tag['music'])
		isrc = tag['isrc']
		song_name = f"{music} - {artist} [{isrc}]"

	l_encoded = len(
		song_name.encode()
	)

	if l_encoded > 242:
		n_tronc = l_encoded - 242
		n_tronc = len(song_name) - n_tronc
	else:
		n_tronc = 242

	song_path = f"{song_name[:n_tronc]}"
	song_path += f" ({song_quality}){file_format}"
	return song_path

def get_quality(quality):
	chosen = qualities[quality]
	s_quality = chosen['s_quality']
	return s_quality

def get_url_path(link):
	parsed = urlparse(link)
	path = parsed.path
	s_path = path.split("/")
	path = f"{s_path[-2]}/{s_path[-1]}"
	return path

def my_round(num):
	rounded = round(num, 2)
	return rounded

def get_image_bytes(image_url):
	content = req_get(image_url).content
	return content

def get_avalaible_disk_space():
	total, used, free = disk_usage("/")
	total = convert_bytes_to(total, "gb")
	used = convert_bytes_to(used, "gb")
	free = convert_bytes_to(free, "gb")
	return free

def get_download_dir_size():
	total_size = 0

	for dirpath, dirnames, filenames in walk(output_songs):
		for f in filenames:
			fp = join(dirpath, f)

			if not islink(fp):
				total_size += getsize(fp)

	total_size = convert_bytes_to(total_size, "gb")
	return total_size

def clear_download_dir():
	dirs = listdir(output_songs)

	for c_dir in dirs:
		cc_dir = join(output_songs, c_dir)

		if isdir(cc_dir):
			rmtree(cc_dir)

def clear_recorded_dir():
	files = listdir(output_shazam)

	for c_file in files:
		cc_file = join(output_shazam, c_file)
		remove(cc_file)

def create_recorded_dir():
	if not isdir(output_shazam):
		mkdir(output_shazam)

def create_download_dir():
	if not isdir(output_songs):
		mkdir(output_songs)

def create_log_dir():
	if not isdir(logs_path):
		mkdir(logs_path)

	if not exists(log_downloads):
		f = open(log_downloads, "w")
		f.write("")
		f.close()

	if not exists(log_uploads):
		f = open(log_uploads, "w")
		f.write("")
		f.close()

def check_config_bot():
	initialize_db()
	create_recorded_dir()
	create_download_dir()
	create_log_dir()

def get_size(f, size) -> float:
	b_size = getsize(f)
	mb_size = convert_bytes_to(b_size, size)
	return mb_size

def show_menu():
	print("1): TEST MODE")
	print("2): COOL MODE")

	ans = input("How to use it?: ")

	if ans == "1":
		choice = 1
	elif ans == "2":
		choice = 2
	else:
		exit()

	return choice

def clear():
	cmd = None

	if os_name == "nt":
		cmd = "cls"
	else:
		cmd = "clear"

	return cmd

def create_tmux():
	cclear = clear()
	system(cclear)
	server = tmux_server()

	info = {
		"session_name": "deez_bot"
	}

	session = server.find_where(info)

	try:
		window = session.attached_window
	except AttributeError:
		print("Must be executed after typed tmux new -s deez_bot :)")
		raise KeyboardInterrupt

	pan_top_right = window.split_window(vertical = False)
	pan_top_right.send_keys(cclear)
	pan_top_right.send_keys(f"tail -f {log_errors}")
	pan_bot_left = pan_top_right.split_window(vertical = True)
	pan_bot_left.send_keys(cclear)
	pan_bot_left.send_keys(f"tail -n2 -f {log_uploads}")
	#pan_bot_right = pan_bot_left.split_window(vertical = False)
	#pan_bot_right.send_keys(cclear)
	#pan_bot_right.send_keys(f"tail -n2 -f {log_downloads}")
	return session
