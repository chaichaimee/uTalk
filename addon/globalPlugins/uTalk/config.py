# config.py

import json
import os
import config
import addonHandler
import logHandler
import tempfile
import shutil

addonHandler.initTranslation()

CONFIG_FILENAME = "uTalk.json"
DEFAULT_CONFIG = {
	"last_used_language": False,
	"language_alt": "",
	"copy": "copy",
	"copy_alt": "",
	"copyAsPath": "copy as path",
	"copyFile": "copy file",
	"copyFile_alt": "",
	"cut": "cut",
	"cut_alt": "",
	"paste": "paste",
	"paste_alt": "",
	"redo": "redo",
	"redo_alt": "",
	"save": "save",
	"save_alt": "",
	"selectAll": "select all",
	"selectAll_alt": "",
	"undo": "undo",
	"undo_alt": ""
}

# Migration flag
_migrated = False

def getConfigPath():
	"""Return the path to the configuration file in the ChaiChaimee subdirectory."""
	base_dir = config.getUserDefaultConfigPath()
	return os.path.join(base_dir, "ChaiChaimee", CONFIG_FILENAME)

def _migrate_old_config():
	r"""
	Migrate configuration from old location (userConfig\uTalk.json) to new location
	(userConfig\ChaiChaimee\uTalk.json) and clean up old file if it exists.
	"""
	base_dir = config.getUserDefaultConfigPath()
	old_path = os.path.join(base_dir, CONFIG_FILENAME)
	new_path = getConfigPath()

	# If old config does not exist, nothing to do
	if not os.path.isfile(old_path):
		return

	# If new config already exists, we can safely delete the old one
	if os.path.isfile(new_path):
		try:
			os.remove(old_path)
			logHandler.log.info(f"uTalk: Removed old config file at {old_path} because new config exists.")
		except Exception as e:
			logHandler.log.warning(f"uTalk: Could not remove old config file at {old_path}: {str(e)}")
		return

	# New config does not exist, so migrate
	logHandler.log.info(f"uTalk: Migrating config from {old_path} to {new_path}.")
	try:
		# Ensure target directory exists
		os.makedirs(os.path.dirname(new_path), exist_ok=True)
		# Try to move first (atomic if on same filesystem)
		shutil.move(old_path, new_path)
		logHandler.log.info("uTalk: Config migration successful (move).")
	except Exception as e:
		logHandler.log.warning(f"uTalk: Move failed, trying copy and delete: {str(e)}")
		try:
			shutil.copy2(old_path, new_path)
			os.remove(old_path)
			logHandler.log.info("uTalk: Config migration successful (copy+delete).")
		except Exception as e2:
			logHandler.log.error(f"uTalk: Failed to migrate config: {str(e2)}")
			# If copy also fails, we leave old file in place

def _ensure_migration():
	"""Ensure migration is performed only once."""
	global _migrated
	if _migrated:
		return
	_migrated = True
	_migrate_old_config()

def loadConfig():
	_ensure_migration()
	path = getConfigPath()
	logHandler.log.info(f"uTalk: Attempting to load config from: {path}")
	if os.path.isfile(path):
		try:
			with open(path, "r", encoding="utf-8") as f:
				loaded_data = json.load(f)
				logHandler.log.info(f"uTalk: Successfully loaded raw config data: {loaded_data}")
				final_config = DEFAULT_CONFIG.copy()
				final_config.update(loaded_data)
				logHandler.log.info(f"uTalk: Merged config after load: {final_config}")
				return final_config
		except json.JSONDecodeError as e:
			logHandler.log.error(f"uTalk: JSON decoding error loading config from {path}: {str(e)}. File might be corrupt or empty.")
			logHandler.log.info(f"uTalk: Returning default config due to JSON error.")
			return DEFAULT_CONFIG.copy()
		except Exception as e:
			logHandler.log.error(f"uTalk: Generic error loading config from {path}: {str(e)}")
			logHandler.log.info(f"uTalk: Returning default config due to error.")
			return DEFAULT_CONFIG.copy()
	else:
		# If config not found at new path, check if old path exists but migration failed or was skipped.
		old_path = os.path.join(config.getUserDefaultConfigPath(), CONFIG_FILENAME)
		if os.path.isfile(old_path):
			logHandler.log.warning(f"uTalk: Config not found at new path but exists at old path. Attempting to load from old path as fallback.")
			try:
				with open(old_path, "r", encoding="utf-8") as f:
					loaded_data = json.load(f)
					logHandler.log.info(f"uTalk: Successfully loaded raw config data from old path: {loaded_data}")
					final_config = DEFAULT_CONFIG.copy()
					final_config.update(loaded_data)
					return final_config
			except Exception as e:
				logHandler.log.error(f"uTalk: Error loading from old path: {str(e)}")

		logHandler.log.info(f"uTalk: Config file not found at {path}, returning default config.")
		return DEFAULT_CONFIG.copy()

def saveConfig(data):
	_ensure_migration()
	path = getConfigPath()
	dir_path = os.path.dirname(path)
	logHandler.log.info(f"uTalk: Attempting to save config to: {path}")
	logHandler.log.info(f"uTalk: Data to be saved: {data}")
	try:
		os.makedirs(dir_path, exist_ok=True)

		# Use a temporary file for atomic write
		temp_fd, temp_path = tempfile.mkstemp(prefix=CONFIG_FILENAME + '.', dir=dir_path)
		with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=2, ensure_ascii=False)

		# Atomically replace the original file
		os.replace(temp_path, path)

		logHandler.log.info(f"uTalk: Config successfully saved to {path} via atomic write. Verifying content...")

		# Verification step
		with open(path, "r", encoding="utf-8") as f_read:
			verify_data = json.load(f_read)
			logHandler.log.info(f"uTalk: Verified saved content: {verify_data}")
			if verify_data == data:
				logHandler.log.info("uTalk: Saved data matches verification.")
				return True
			else:
				logHandler.log.error("uTalk: Saved data MISMATCH after verification!")
				return False
	except Exception as e:
		logHandler.log.error(f"uTalk: Error saving config to {path}: {str(e)}")
		# Clean up temporary file if it exists and was not renamed
		if os.path.exists(temp_path):
			os.remove(temp_path)
		return False