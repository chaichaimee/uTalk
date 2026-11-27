# config.py

import copy
import json
import os
import shutil
import tempfile
import globalVars
import addonHandler
import logHandler

addonHandler.initTranslation()

PUBLISHER_FOLDER_NAME = "ChaiChaimee"
ADDON_FOLDER_NAME = "uTalk"
CONFIG_FILENAME = "uTalk.json"
MAX_PHRASE_LENGTH = 200

OUTPUT_MODES = ("speechBraille", "speech", "braille", "beep")
VERBOSITY_LEVELS = ("short", "detailed")
APP_RULE_VALUES = ("off", "main", "alt")

DEFAULT_CONFIG = {
	"last_used_language": False,
	"language_alt": "",
	"outputMode": "speechBraille",
	"verbosity": "short",
	"verifyActions": True,
	"appRules": {
		"cmd": "off",
		"conhost": "off",
		"openconsole": "off",
		"powershell": "off",
		"pwsh": "off",
		"windowsterminal": "off",
		"wt": "off"
	},
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

_migrated = False
_lastSavedSnapshot = None


def getDefaultConfig():
	return copy.deepcopy(DEFAULT_CONFIG)


def hasAlternateLanguage(configData):
	return any(
		isinstance(value, str) and value.strip()
		for key, value in configData.items()
		if key.endswith("_alt") and key != "language_alt"
	)


def normalizeAppName(rawName):
	appName = rawName.strip().lower()
	if appName.endswith(".exe"):
		appName = appName[:-4]
	return appName


def parseAppRules(ruleText):
	rules = {}
	for lineNumber, rawLine in enumerate(ruleText.splitlines(), start=1):
		line = rawLine.strip()
		if not line:
			continue
		appName, separator, ruleValue = line.partition("=")
		appName = normalizeAppName(appName)
		ruleValue = ruleValue.strip().lower()
		if not separator or not appName or ruleValue not in APP_RULE_VALUES:
			return None, lineNumber
		rules[appName] = ruleValue
	return rules, 0


def formatAppRules(rules):
	return "\n".join(f"{appName}={ruleValue}" for appName, ruleValue in sorted(rules.items()))


def getConfigPath():
	return os.path.join(
		globalVars.appArgs.configPath,
		PUBLISHER_FOLDER_NAME,
		ADDON_FOLDER_NAME,
		CONFIG_FILENAME
	)


def _getLegacyConfigPaths():
	baseDir = globalVars.appArgs.configPath
	return [
		os.path.join(baseDir, PUBLISHER_FOLDER_NAME, CONFIG_FILENAME),
		os.path.join(baseDir, CONFIG_FILENAME)
	]


def _readJsonDict(path):
	try:
		with open(path, "r", encoding="utf-8") as configFile:
			loadedData = json.load(configFile)
	except (OSError, ValueError) as e:
		logHandler.log.warning(f"uTalk: Could not read config file {path}: {str(e)}")
		return None
	if not isinstance(loadedData, dict):
		logHandler.log.warning(f"uTalk: Config file {path} does not hold a JSON object.")
		return None
	return loadedData


def _findLegacyConfigs():
	existingPaths = [path for path in _getLegacyConfigPaths() if os.path.isfile(path)]
	existingPaths.sort(key=os.path.getmtime, reverse=True)
	return existingPaths


def _isCopyVerified(sourcePath, targetPath):
	try:
		if os.path.getsize(sourcePath) != os.path.getsize(targetPath):
			return False
	except OSError:
		return False
	return _readJsonDict(targetPath) is not None


def _removeQuietly(path):
	if os.path.isfile(path):
		try:
			os.remove(path)
		except OSError as e:
			logHandler.log.warning(f"uTalk: Could not remove temporary file {path}: {str(e)}")


def _copyAtomically(sourcePath, targetPath):
	targetDir = os.path.dirname(targetPath)
	os.makedirs(targetDir, exist_ok=True)
	tempFd, tempPath = tempfile.mkstemp(prefix=CONFIG_FILENAME + ".", dir=targetDir)
	os.close(tempFd)
	try:
		shutil.copyfile(sourcePath, tempPath)
		os.replace(tempPath, targetPath)
	except OSError:
		if os.path.exists(tempPath):
			_removeQuietly(tempPath)
		raise


def _removeLegacyFile(legacyPath, newPath):
	if legacyPath not in _getLegacyConfigPaths() or legacyPath == newPath:
		return
	if _readJsonDict(newPath) is None:
		logHandler.log.warning(f"uTalk: Keeping old config file {legacyPath} because the new config is not valid.")
		return
	if os.path.isfile(legacyPath):
		try:
			os.remove(legacyPath)
			logHandler.log.info(f"uTalk: Removed old config file at {legacyPath}.")
		except OSError as e:
			logHandler.log.warning(f"uTalk: Could not remove old config file at {legacyPath}: {str(e)}")


def _migrateOldConfig():
	legacyPaths = _findLegacyConfigs()
	if not legacyPaths:
		return
	newPath = getConfigPath()
	logHandler.log.info(f"uTalk: Found old config file(s): {legacyPaths}. New location is {newPath}.")

	if _readJsonDict(newPath) is None:
		sourcePath = next((path for path in legacyPaths if _readJsonDict(path) is not None), None)
		if not sourcePath:
			logHandler.log.error("uTalk: Old config file(s) exist but none holds valid JSON. Nothing migrated.")
			return
		logHandler.log.info(f"uTalk: Migrating config from {sourcePath} to {newPath}.")
		try:
			_copyAtomically(sourcePath, newPath)
		except OSError as e:
			logHandler.log.error(f"uTalk: Failed to migrate config: {str(e)}")
			return
		if not _isCopyVerified(sourcePath, newPath):
			logHandler.log.error("uTalk: Migrated config failed verification. Old file(s) kept.")
			return
		logHandler.log.info("uTalk: Config migration successful.")
	else:
		logHandler.log.info("uTalk: New config already exists, old file(s) are stale.")

	for legacyPath in legacyPaths:
		_removeLegacyFile(legacyPath, newPath)


def _ensureMigration():
	global _migrated
	if _migrated:
		return
	_migrated = True
	_migrateOldConfig()


def _isValidAppRules(value):
	if not isinstance(value, dict):
		return False
	return all(
		isinstance(appName, str) and appName and value[appName] in APP_RULE_VALUES
		for appName in value
	)


def _isValidValue(key, value):
	defaultValue = DEFAULT_CONFIG[key]
	if key == "outputMode":
		return value in OUTPUT_MODES
	if key == "verbosity":
		return value in VERBOSITY_LEVELS
	if key == "appRules":
		return _isValidAppRules(value)
	if isinstance(defaultValue, bool):
		return isinstance(value, bool)
	return isinstance(value, type(defaultValue))


def _normalizeConfig(loadedData):
	finalConfig = getDefaultConfig()
	for key, value in loadedData.items():
		if key not in DEFAULT_CONFIG:
			finalConfig[key] = value
			continue
		if _isValidValue(key, value):
			finalConfig[key] = value
			continue
		logHandler.log.warning(f"uTalk: Ignoring invalid value for config key {key}. Using its default.")
	return finalConfig


def _snapshotOf(data):
	return json.dumps(data, sort_keys=True, ensure_ascii=False)


def loadConfig():
	global _lastSavedSnapshot
	_ensureMigration()
	path = getConfigPath()
	logHandler.log.info(f"uTalk: Attempting to load config from: {path}")
	loadedData = _readJsonDict(path) if os.path.isfile(path) else None

	if loadedData is not None:
		_lastSavedSnapshot = _snapshotOf(loadedData)
	else:
		_lastSavedSnapshot = None
		for legacyPath in _findLegacyConfigs():
			loadedData = _readJsonDict(legacyPath)
			if loadedData is not None:
				logHandler.log.warning(f"uTalk: Config not usable at new path. Loaded from old path {legacyPath} as fallback.")
				break

	if loadedData is None:
		logHandler.log.info(f"uTalk: No usable config found at {path}, returning default config.")
		return getDefaultConfig()

	finalConfig = _normalizeConfig(loadedData)
	logHandler.log.debug(f"uTalk: Merged config after load: {finalConfig}")
	return finalConfig


def saveConfig(data):
	global _lastSavedSnapshot
	_ensureMigration()
	path = getConfigPath()
	dirPath = os.path.dirname(path)
	try:
		newSnapshot = _snapshotOf(data)
	except (TypeError, ValueError) as e:
		logHandler.log.error(f"uTalk: Config data cannot be serialized: {str(e)}")
		return False
	if newSnapshot == _lastSavedSnapshot and os.path.isfile(path):
		logHandler.log.debug("uTalk: Config unchanged since last save, write skipped.")
		return True

	tempPath = None
	logHandler.log.info(f"uTalk: Attempting to save config to: {path}")
	logHandler.log.debug(f"uTalk: Data to be saved: {data}")
	try:
		os.makedirs(dirPath, exist_ok=True)
		tempFd, tempPath = tempfile.mkstemp(prefix=CONFIG_FILENAME + ".", dir=dirPath)
		with os.fdopen(tempFd, "w", encoding="utf-8") as configFile:
			json.dump(data, configFile, indent=2, ensure_ascii=False)
			configFile.flush()
			os.fsync(configFile.fileno())
		os.replace(tempPath, path)
		tempPath = None
	except (OSError, TypeError, ValueError) as e:
		logHandler.log.error(f"uTalk: Error saving config to {path}: {str(e)}")
		if tempPath and os.path.exists(tempPath):
			_removeQuietly(tempPath)
		return False

	verifyData = _readJsonDict(path)
	if verifyData != data:
		logHandler.log.error("uTalk: Saved data MISMATCH after verification!")
		return False
	_lastSavedSnapshot = newSnapshot
	logHandler.log.info(f"uTalk: Config successfully saved to {path} via atomic write and verified.")
	return True
