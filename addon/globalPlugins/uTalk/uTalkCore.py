# uTalkCore.py

import ctypes
import time
import weakref
import globalPluginHandler
import addonHandler
import api
import braille
import browseMode
import config as nvdaConfig
import controlTypes
import core
import gui
import logHandler
import scriptHandler
import speech
import textInfos
import tones
import ui
from comtypes import COMError
from gui.settingsDialogs import NVDASettingsDialog
from . import config as uconfig
from . import settingsPanel

addonHandler.initTranslation()

_utalkPluginRef = None

# Hard cap on any string reaching the synthesizer or braille display via this add-on.
# Guards against pathologically long user-entered translation strings.
_MAX_SPOKEN_MESSAGE_LENGTH = 200

_ANNOUNCE_DELAY_MS = 100
_CLIPBOARD_POLL_DELAYS_MS = (100, 150, 250, 500, 500)
_UNDO_POLL_DELAYS_MS = (150, 250)
_TAP_TIMEOUT_MARGIN_MS = 50
_SETTINGS_POPUP_DELAY_MS = 300
_MAX_DIFF_TEXT_LENGTH = 100000
_SLOW_TEXT_READ_SECONDS = 0.15
_MAX_SNIPPET_LENGTH = 30
_DIRECT_MESSAGE_KEY = "direct"

_COMMAND_BEEPS = {
	"copy": (880, 40),
	"copyAsPath": (587, 40),
	"copyFile": (622, 40),
	"cut": (740, 40),
	"paste": (660, 40),
	"redo": (520, 40),
	"save": (784, 60),
	"selectAll": (990, 40),
	"undo": (440, 40)
}
_ERROR_BEEP = (220, 120)

_TEXT_READ_ERRORS = (RuntimeError, NotImplementedError, OSError, COMError, AttributeError)


def _capSpokenLength(text):
	if len(text) > _MAX_SPOKEN_MESSAGE_LENGTH:
		return text[:_MAX_SPOKEN_MESSAGE_LENGTH] + _("...truncated")
	return text


def _getClipboardSequence():
	return ctypes.windll.user32.GetClipboardSequenceNumber()


def _getAppName(focusObject):
	appName = getattr(getattr(focusObject, "appModule", None), "appName", "")
	return appName.lower() if isinstance(appName, str) else ""


def _isBrowseModeActive(focusObject):
	interceptor = getattr(focusObject, "treeInterceptor", None)
	return isinstance(interceptor, browseMode.BrowseModeDocumentTreeInterceptor) and not interceptor.passThrough


def _canPasteHere(focusObject):
	if not focusObject or _isBrowseModeActive(focusObject):
		return False
	# Only text fields are skipped when read-only. UIA also marks other controls
	# (for example File Explorer items) read-only when their name cannot be edited
	# in place, yet pasting files into them works.
	isReadOnly = controlTypes.State.READONLY in focusObject.states
	return not (isReadOnly and focusObject.role == controlTypes.Role.EDITABLETEXT)


def _getFailureText(key):
	if key == "cut":
		return _("Nothing to cut")
	return _("Nothing to copy")


def _describeLength(text):
	characterCount = len(text)
	detail = ngettext("{count} character", "{count} characters", characterCount).format(count=characterCount)
	lineCount = len(text.splitlines())
	if lineCount > 1:
		lineDetail = ngettext("{count} line", "{count} lines", lineCount).format(count=lineCount)
		return f"{lineDetail} {detail}"
	return detail


def _makeSnippet(text):
	collapsedText = " ".join(text.split())
	if not collapsedText:
		return _("whitespace")
	if len(collapsedText) > _MAX_SNIPPET_LENGTH:
		return collapsedText[:_MAX_SNIPPET_LENGTH] + "..."
	return collapsedText


def _describeTextChange(beforeText, afterText):
	commonLimit = min(len(beforeText), len(afterText))
	prefixLength = 0
	while prefixLength < commonLimit and beforeText[prefixLength] == afterText[prefixLength]:
		prefixLength += 1
	suffixLimit = commonLimit - prefixLength
	suffixLength = 0
	while suffixLength < suffixLimit and beforeText[-1 - suffixLength] == afterText[-1 - suffixLength]:
		suffixLength += 1
	removedText = beforeText[prefixLength:len(beforeText) - suffixLength]
	addedText = afterText[prefixLength:len(afterText) - suffixLength]
	if removedText and addedText:
		return _("replaced {removed} with {added}").format(
			removed=_makeSnippet(removedText),
			added=_makeSnippet(addedText)
		)
	if removedText:
		return _("removed {text}").format(text=_makeSnippet(removedText))
	if addedText:
		return _("added {text}").format(text=_makeSnippet(addedText))
	return ""


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("uTalk")

	__gestures = {
		"kb:nvda+alt+t": "toggle_or_settings",
		"kb:control+c": "announceCopy",
		"kb:control+v": "announcePaste",
		"kb:control+x": "announceCut",
		"kb:control+z": "announceUndo",
		"kb:control+y": "announceRedo",
		"kb:control+shift+z": "announceRedo",
		"kb:control+a": "announceSelectAll",
		"kb:control+s": "announceSave",
		"kb:control+shift+c": "announceCopyAsPath",
		"kb:control+alt+c": "announceCopyFile"
	}

	def __init__(self):
		super().__init__()
		global _utalkPluginRef
		_utalkPluginRef = weakref.ref(self)

		self.config = uconfig.loadConfig()
		self.useAlternateLanguage = self.config.get("last_used_language", False)
		self.isMuted = False
		self.isTerminated = False

		self._tapCount = 0
		self._tapTimer = None
		self._settingsPopupTimer = None
		self._pendingTimers = {}
		self._slowTextApps = set()

		try:
			if settingsPanel.uTalkSettingsPanel not in NVDASettingsDialog.categoryClasses:
				NVDASettingsDialog.categoryClasses.append(settingsPanel.uTalkSettingsPanel)
		except RuntimeError as e:
			logHandler.log.warning(f"uTalk: Could not register settings panel: {e}")

	def _stopTimer(self, timer):
		try:
			if timer.IsRunning():
				timer.Stop()
		except RuntimeError:
			logHandler.log.debugWarning("uTalk: Timer was already destroyed.")

	def _cancelPending(self, key):
		timer = self._pendingTimers.pop(key, None)
		if timer:
			self._stopTimer(timer)

	def _cancelAllPending(self):
		for key in list(self._pendingTimers):
			self._cancelPending(key)

	def _scheduleAnnouncement(self, key, delayMs, callback, *args):
		self._cancelPending(key)
		self._pendingTimers[key] = core.callLater(delayMs, callback, *args)

	def _forwardGesture(self, gesture):
		core.callLater(0, gesture.send)

	def _getAppMode(self, focusObject):
		return self.config.get("appRules", {}).get(_getAppName(focusObject))

	def _shouldAnnounce(self, appMode):
		return not self.isMuted and appMode != "off"

	def _isBeepMode(self):
		return self.config.get("outputMode") == "beep"

	def _isDetailed(self):
		return self.config.get("verbosity") == "detailed" and not self._isBeepMode()

	def _resolveMessage(self, key, appMode):
		useAlternate = (appMode == "alt") if appMode in ("main", "alt") else self.useAlternateLanguage
		defaultMessage = uconfig.DEFAULT_CONFIG.get(key, "")
		if not useAlternate:
			return defaultMessage
		return self.config.get(f"{key}_alt", "").strip() or defaultMessage

	def _presentText(self, text):
		text = _capSpokenLength(text.strip())
		if not text:
			return
		outputMode = self.config.get("outputMode")
		if outputMode == "speech":
			speech.speakMessage(text)
		elif outputMode == "braille":
			braille.handler.message(text)
		else:
			ui.message(text)

	def _presentCommand(self, key, text):
		if self._isBeepMode():
			hz, length = _COMMAND_BEEPS[key]
			tones.beep(hz, length)
			return
		self._presentText(text)

	def _scheduleDirect(self, text):
		self._scheduleAnnouncement(_DIRECT_MESSAGE_KEY, _ANNOUNCE_DELAY_MS, self._presentDirect, text)

	def _presentDirect(self, text):
		self._pendingTimers.pop(_DIRECT_MESSAGE_KEY, None)
		if self.isTerminated:
			return
		self._presentText(text)

	def _announceCommand(self, key, appMode, detail=""):
		self._pendingTimers.pop(key, None)
		if self.isTerminated or not self._shouldAnnounce(appMode):
			return
		text = self._resolveMessage(key, appMode)
		if not text.strip():
			return
		if detail:
			text = f"{text} {detail}"
		self._presentCommand(key, text)

	def _announceFailure(self, key):
		if self.isTerminated or self.isMuted:
			return
		if self._isBeepMode():
			tones.beep(*_ERROR_BEEP)
			return
		self._presentText(_getFailureText(key))

	def _buildClipboardDetail(self):
		if not self._isDetailed():
			return ""
		try:
			clipboardText = api.getClipData()
		except OSError as e:
			logHandler.log.debugWarning(f"uTalk: Clipboard could not be read for details: {e}")
			return ""
		return _describeLength(clipboardText) if clipboardText else ""

	def _announceClipboardCommand(self, key, appMode):
		self._announceCommand(key, appMode, self._buildClipboardDetail())

	def _startClipboardCommand(self, key, appMode, baselineSequence):
		if not self._shouldAnnounce(appMode):
			return
		if baselineSequence and self.config.get("verifyActions", True):
			self._scheduleAnnouncement(
				key, _CLIPBOARD_POLL_DELAYS_MS[0], self._pollClipboard, key, appMode, baselineSequence, 0
			)
			return
		self._scheduleAnnouncement(key, _ANNOUNCE_DELAY_MS, self._announceClipboardCommand, key, appMode)

	def _pollClipboard(self, key, appMode, baselineSequence, attemptIndex):
		self._pendingTimers.pop(key, None)
		if self.isTerminated:
			return
		if _getClipboardSequence() != baselineSequence:
			self._announceClipboardCommand(key, appMode)
			return
		nextIndex = attemptIndex + 1
		if nextIndex >= len(_CLIPBOARD_POLL_DELAYS_MS):
			self._announceFailure(key)
			return
		self._pendingTimers[key] = core.callLater(
			_CLIPBOARD_POLL_DELAYS_MS[nextIndex], self._pollClipboard, key, appMode, baselineSequence, nextIndex
		)

	def _readEditableText(self, focusObject):
		if not focusObject or _isBrowseModeActive(focusObject):
			return None
		if controlTypes.State.EDITABLE not in focusObject.states:
			return None
		appName = _getAppName(focusObject)
		if appName in self._slowTextApps:
			return None
		startTime = time.perf_counter()
		try:
			currentText = focusObject.makeTextInfo(textInfos.POSITION_ALL).text
		except _TEXT_READ_ERRORS as e:
			logHandler.log.debugWarning(f"uTalk: Could not read editable text: {e}")
			return None
		if time.perf_counter() - startTime > _SLOW_TEXT_READ_SECONDS:
			self._slowTextApps.add(appName)
			logHandler.log.debugWarning(f"uTalk: Text reads are slow in {appName}, undo details disabled for it.")
		if len(currentText) > _MAX_DIFF_TEXT_LENGTH:
			return None
		return currentText

	def _pollUndoText(self, key, appMode, beforeText, attemptIndex):
		self._pendingTimers.pop(key, None)
		if self.isTerminated:
			return
		afterText = self._readEditableText(api.getFocusObject())
		if afterText is not None and afterText != beforeText:
			self._announceCommand(key, appMode, _describeTextChange(beforeText, afterText))
			return
		nextIndex = attemptIndex + 1
		if nextIndex >= len(_UNDO_POLL_DELAYS_MS):
			self._announceCommand(key, appMode)
			return
		self._pendingTimers[key] = core.callLater(
			_UNDO_POLL_DELAYS_MS[nextIndex], self._pollUndoText, key, appMode, beforeText, nextIndex
		)

	def _handleUndoRedo(self, gesture, key):
		focusObject = api.getFocusObject()
		appMode = self._getAppMode(focusObject)
		wantsDetail = self._shouldAnnounce(appMode) and self._isDetailed()
		beforeText = self._readEditableText(focusObject) if wantsDetail else None
		self._forwardGesture(gesture)
		if not self._shouldAnnounce(appMode):
			return
		if beforeText is None:
			self._scheduleAnnouncement(key, _ANNOUNCE_DELAY_MS, self._announceCommand, key, appMode)
			return
		self._scheduleAnnouncement(key, _UNDO_POLL_DELAYS_MS[0], self._pollUndoText, key, appMode, beforeText, 0)

	def _handleSimpleCommand(self, gesture, key):
		appMode = self._getAppMode(api.getFocusObject())
		self._forwardGesture(gesture)
		if self._shouldAnnounce(appMode):
			self._scheduleAnnouncement(key, _ANNOUNCE_DELAY_MS, self._announceCommand, key, appMode)

	def _handleExplorerCommand(self, gesture, key):
		focusObject = api.getFocusObject()
		appMode = self._getAppMode(focusObject)
		if _getAppName(focusObject) == "explorer" and self._shouldAnnounce(appMode):
			self._scheduleAnnouncement(key, _ANNOUNCE_DELAY_MS, self._announceCommand, key, appMode)
		self._forwardGesture(gesture)

	def _getSelectedTextRobust(self, focusObject):
		if not focusObject:
			return None
		target = focusObject.treeInterceptor if _isBrowseModeActive(focusObject) else focusObject
		try:
			if hasattr(target, "makeTextInfo"):
				info = target.makeTextInfo(textInfos.POSITION_SELECTION)
				if info and not info.isCollapsed:
					rawText = info.clipboardText
					if rawText:
						return rawText.replace("\r\n", "\n").replace("\r", "\n").strip()
		except _TEXT_READ_ERRORS as e:
			logHandler.log.debugWarning(f"uTalk: Could not read the selection: {e}")
		return None

	def script_announceCopy(self, gesture):
		focusObject = api.getFocusObject()
		appMode = self._getAppMode(focusObject)
		baselineSequence = _getClipboardSequence()
		if _isBrowseModeActive(focusObject):
			# A browse mode selection exists only inside NVDA, so the application
			# would copy nothing from a forwarded Ctrl+C. Only the API copy works.
			selectedText = self._getSelectedTextRobust(focusObject)
			if selectedText:
				api.copyToClip(selectedText)
			else:
				self._forwardGesture(gesture)
		else:
			# Real selections are copied by the application itself, which keeps
			# any rich clipboard formats it adds.
			self._forwardGesture(gesture)
		self._startClipboardCommand("copy", appMode, baselineSequence)

	def script_announceCut(self, gesture):
		appMode = self._getAppMode(api.getFocusObject())
		baselineSequence = _getClipboardSequence()
		self._forwardGesture(gesture)
		self._startClipboardCommand("cut", appMode, baselineSequence)

	def script_announcePaste(self, gesture):
		focusObject = api.getFocusObject()
		appMode = self._getAppMode(focusObject)
		self._forwardGesture(gesture)
		if not self._shouldAnnounce(appMode):
			return
		if self.config.get("verifyActions", True) and not _canPasteHere(focusObject):
			logHandler.log.debug("uTalk: Paste announcement skipped in %s, role %s", _getAppName(focusObject), focusObject.role)
			return
		self._scheduleAnnouncement("paste", _ANNOUNCE_DELAY_MS, self._announceClipboardCommand, "paste", appMode)

	def script_announceUndo(self, gesture):
		self._handleUndoRedo(gesture, "undo")

	def script_announceRedo(self, gesture):
		self._handleUndoRedo(gesture, "redo")

	def script_announceSelectAll(self, gesture):
		self._handleSimpleCommand(gesture, "selectAll")

	def script_announceSave(self, gesture):
		self._handleSimpleCommand(gesture, "save")

	def script_announceCopyAsPath(self, gesture):
		self._handleExplorerCommand(gesture, "copyAsPath")

	def script_announceCopyFile(self, gesture):
		self._handleExplorerCommand(gesture, "copyFile")

	@scriptHandler.script(
		description=_(
			"uTalk multi tap. Once: swap languages. Twice: open settings. "
			"Three times: turn uTalk off or on for the current application. "
			"Four times: mute or unmute uTalk announcements"
		)
	)
	def script_toggle_or_settings(self, gesture):
		self._tapCount = scriptHandler.getLastScriptRepeatCount() + 1
		if self._tapTimer:
			self._stopTimer(self._tapTimer)
		delayMs = nvdaConfig.conf["keyboard"]["multiPressTimeout"] + _TAP_TIMEOUT_MARGIN_MS
		self._tapTimer = core.callLater(delayMs, self._handleTap)

	@scriptHandler.script(description=_("Mute or unmute uTalk announcements"))
	def script_toggleMute(self, gesture):
		self._toggleMute()

	def _toggleMute(self):
		self.isMuted = not self.isMuted
		if self.isMuted:
			self._cancelAllPending()
		ui.message(_("uTalk muted") if self.isMuted else _("uTalk unmuted"))

	@scriptHandler.script(description=_("Turn uTalk off or on for the current application"))
	def script_toggleCurrentApp(self, gesture):
		self._toggleCurrentApp()

	def _toggleCurrentApp(self):
		appName = _getAppName(api.getFocusObject())
		if not appName:
			ui.message(_("Cannot detect the current application"))
			return
		rules = dict(self.config.get("appRules", {}))
		if rules.get(appName) == "off":
			del rules[appName]
			resultMessage = _("uTalk on for {appName}")
		else:
			rules[appName] = "off"
			resultMessage = _("uTalk off for {appName}")
		self.config["appRules"] = rules
		if not uconfig.saveConfig(self.config):
			ui.message(_("Could not save the application rule"))
			return
		ui.message(resultMessage.format(appName=appName))

	def _getLanguageName(self):
		if self.useAlternateLanguage:
			return self.config.get("language_alt", "").strip() or _("Alternate language")
		return _("English")

	def announceLanguage(self):
		self._scheduleDirect(self._getLanguageName())

	def _handleTap(self):
		tapCount = self._tapCount
		self._tapCount = 0
		self._tapTimer = None
		logHandler.log.debug(f"uTalk: _handleTap called with tap count {tapCount}")
		if tapCount == 1:
			self._toggleLanguage()
		elif tapCount == 2:
			self._openSettings()
		elif tapCount == 3:
			self._toggleCurrentApp()
		elif tapCount >= 4:
			self._toggleMute()

	def _toggleLanguage(self):
		if not self.useAlternateLanguage and not uconfig.hasAlternateLanguage(self.config):
			ui.message(_("Alternate language is not set. Press the shortcut twice to open the uTalk settings and add phrases."))
			return
		self.useAlternateLanguage = not self.useAlternateLanguage
		self.config["last_used_language"] = self.useAlternateLanguage
		uconfig.saveConfig(self.config)
		languageName = self._getLanguageName()
		self._scheduleDirect(languageName)
		logHandler.log.info(f"uTalk: Language toggled to {languageName}")

	def _openSettings(self):
		if self._settingsPopupTimer:
			self._stopTimer(self._settingsPopupTimer)
		self._settingsPopupTimer = core.callLater(
			_SETTINGS_POPUP_DELAY_MS,
			gui.mainFrame.popupSettingsDialog,
			NVDASettingsDialog,
			settingsPanel.uTalkSettingsPanel
		)
		logHandler.log.info("uTalk: Opening settings dialog")

	def updateConfig(self, newConfig):
		self.config.update(newConfig)
		self.useAlternateLanguage = self.config.get("last_used_language", self.useAlternateLanguage)

	def terminate(self):
		global _utalkPluginRef
		self.isTerminated = True
		self._cancelAllPending()
		for timer in (self._tapTimer, self._settingsPopupTimer):
			if timer:
				self._stopTimer(timer)
		self._tapTimer = None
		self._settingsPopupTimer = None
		try:
			NVDASettingsDialog.categoryClasses.remove(settingsPanel.uTalkSettingsPanel)
		except (ValueError, RuntimeError) as e:
			logHandler.log.warning(f"uTalk: Could not unregister settings panel: {e}")
		_utalkPluginRef = None
		super().terminate()
