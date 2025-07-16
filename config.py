# config.py
# -*- coding: utf-8 -*-
# config.py
# Copyright (C) 2025 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import json
import os
import config
import addonHandler
import logHandler
import tempfile # For temporary file operations

addonHandler.initTranslation()

CONFIG_FILENAME = "uTalk.json"
DEFAULT_CONFIG = {
    "last_used_language": False, # Ensure this default exists
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
    "save": "save",
    "save_alt": "",
    "selectAll": "select all",
    "selectAll_alt": "",
    "undo": "undo",
    "undo_alt": ""
}

def getConfigPath():
    return os.path.join(config.getUserDefaultConfigPath(), CONFIG_FILENAME)

def loadConfig():
    path = getConfigPath()
    logHandler.log.info(f"uTalk: Attempting to load config from: {path}")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                logHandler.log.info(f"uTalk: Successfully loaded raw config data: {loaded_data}")
                final_config = DEFAULT_CONFIG.copy()
                final_config.update(loaded_data) # This line merges loaded data over defaults.
                logHandler.log.info(f"uTalk: Merged config after load: {final_config}")
                return final_config
        except json.JSONDecodeError as e: # Catch specific JSON error
            logHandler.log.error(f"uTalk: JSON decoding error loading config from {path}: {str(e)}. File might be corrupt or empty.")
            logHandler.log.info(f"uTalk: Returning default config due to JSON error.")
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logHandler.log.error(f"uTalk: Generic error loading config from {path}: {str(e)}")
            logHandler.log.info(f"uTalk: Returning default config due to error.")
            return DEFAULT_CONFIG.copy()
    logHandler.log.info(f"uTalk: Config file not found at {path}, returning default config.")
    return DEFAULT_CONFIG.copy()

def saveConfig(data):
    path = getConfigPath()
    dir_path = os.path.dirname(path)
    logHandler.log.info(f"uTalk: Attempting to save config to: {path}")
    logHandler.log.info(f"uTalk: Data to be saved: {data}")
    try:
        os.makedirs(dir_path, exist_ok=True)
        
        # Use a temporary file for atomic write
        # This writes to a temp file in the same directory, then renames it.
        # This helps prevent data corruption and can sometimes force file system sync.
        temp_fd, temp_path = tempfile.mkstemp(prefix=CONFIG_FILENAME + '.', dir=dir_path)
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomically replace the original file
        os.replace(temp_path, path) # os.replace is atomic on POSIX, nearly atomic on Windows
        
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
