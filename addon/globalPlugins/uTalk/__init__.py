# __init__.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import globalPluginHandler
import addonHandler
import api
import keyboardHandler
import wx
import core
import ui
import logHandler
import time
import browseMode
import textInfos
import weakref
from gui.settingsDialogs import NVDASettingsDialog
from . import config as uconfig
from . import settingsPanel

addonHandler.initTranslation()

_utalk_plugin_ref = None

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
		global _utalk_plugin_ref
		_utalk_plugin_ref = weakref.ref(self)
		
		self.config = uconfig.loadConfig()
		self.use_alternate_language = self.config.get("last_used_language", False)
		
		self._tap_count = 0
		self._last_tap_time = 0
		self._tap_timer = None
		
		try:
			if settingsPanel.uTalkSettingsPanel not in NVDASettingsDialog.categoryClasses:
				NVDASettingsDialog.categoryClasses.append(settingsPanel.uTalkSettingsPanel)
		except RuntimeError as e:
			logHandler.log.warning(f"uTalk: Could not register settings panel: {e}")

	def _safe_speak(self, key_or_text, is_direct=False):
		def task():
			plugin = _utalk_plugin_ref() if _utalk_plugin_ref else None
			if not plugin:
				return
			if is_direct:
				ui.message(key_or_text.strip())
				return
			
			msg = plugin.config.get(f"{key_or_text}_alt", "") if plugin.use_alternate_language else uconfig.DEFAULT_CONFIG.get(key_or_text, "")
			if msg:
				ui.message(msg.strip())
		core.callLater(100, task)

	def _get_selected_text_robust(self, focusObject):
		if not focusObject:
			return None

		try:
			target = focusObject.treeInterceptor if hasattr(focusObject, 'treeInterceptor') and isinstance(focusObject.treeInterceptor, browseMode.BrowseModeDocumentTreeInterceptor) else focusObject
			if hasattr(target, 'makeTextInfo'):
				info = target.makeTextInfo(textInfos.POSITION_SELECTION)
				if info and not info.isCollapsed:
					raw = info.clipboardText
					if raw:
						return raw.replace('\r\n', '\n').replace('\r', '\n').strip()
		except (RuntimeError, NotImplementedError):
			pass

		return None

	def script_announceCopy(self, gesture):
		try:
			obj = api.getFocusObject()
			if not obj:
				core.callLater(0, gesture.send)
				self._safe_speak("copy")
				return

			selected_text = self._get_selected_text_robust(obj)
			if selected_text:
				api.copyToClip(selected_text)
				self._safe_speak("copy")
			else:
				core.callLater(0, gesture.send)
				self._safe_speak("copy")
		except Exception:
			core.callLater(0, gesture.send)
			self._safe_speak("copy")

	def script_announcePaste(self, gesture):
		core.callLater(0, gesture.send)
		self._safe_speak("paste")

	def script_announceCut(self, gesture):
		core.callLater(0, gesture.send)
		self._safe_speak("cut")

	def script_announceUndo(self, gesture):
		core.callLater(0, gesture.send)
		self._safe_speak("undo")

	def script_announceRedo(self, gesture):
		core.callLater(0, gesture.send)
		self._safe_speak("redo")

	def script_announceSelectAll(self, gesture):
		core.callLater(0, gesture.send)
		self._safe_speak("selectAll")

	def script_announceSave(self, gesture):
		core.callLater(0, gesture.send)
		self._safe_speak("save")

	def script_announceCopyAsPath(self, gesture):
		obj = api.getFocusObject()
		if obj and obj.appModule and obj.appModule.appName.lower() == "explorer":
			self._safe_speak("copyAsPath")
		core.callLater(0, gesture.send)

	def script_announceCopyFile(self, gesture):
		obj = api.getFocusObject()
		if obj and obj.appModule and obj.appModule.appName.lower() == "explorer":
			self._safe_speak("copyFile")
		core.callLater(0, gesture.send)

	def script_toggle_or_settings(self, gesture):
		logHandler.log.info("uTalk: toggle_or_settings script triggered")
		try:
			now = int(time.time() * 1000)
			if (now - self._last_tap_time) > 600:
				self._tap_count = 0
			self._tap_count += 1
			self._last_tap_time = now
			if self._tap_timer and self._tap_timer.IsRunning():
				self._tap_timer.Stop()
			self._tap_timer = core.callLater(500, self._handle_tap)
		except Exception as e:
			logHandler.log.error(f"uTalk: Error in toggle_or_settings: {str(e)}")

	def _handle_tap(self):
		logHandler.log.info(f"uTalk: _handle_tap called with tap_count={self._tap_count}")
		plugin = _utalk_plugin_ref() if _utalk_plugin_ref else None
		if not plugin:
			return
		try:
			if self._tap_count == 1:
				self.use_alternate_language = not self.use_alternate_language
				self.config["last_used_language"] = self.use_alternate_language
				uconfig.saveConfig(self.config)
				name = self.config.get("language_alt", "Alt") if self.use_alternate_language else "English"
				self._safe_speak(name, is_direct=True)
				logHandler.log.info(f"uTalk: Language toggled to {name}")
			elif self._tap_count >= 2:
				import gui
				core.callLater(300, gui.mainFrame.popupSettingsDialog, NVDASettingsDialog, settingsPanel.uTalkSettingsPanel)
				logHandler.log.info("uTalk: Opening settings dialog")
			self._tap_count = 0
		except Exception as e:
			logHandler.log.error(f"uTalk: Error in _handle_tap: {str(e)}")

	def update_config(self, new_config):
		self.config.update(new_config)
		self.use_alternate_language = self.config.get("last_used_language", self.use_alternate_language)

	def terminate(self):
		global _utalk_plugin_ref
		if self._tap_timer:
			try:
				self._tap_timer.Stop()
			except RuntimeError:
				pass
		self._tap_timer = None
		try:
			NVDASettingsDialog.categoryClasses.remove(settingsPanel.uTalkSettingsPanel)
		except (ValueError, RuntimeError) as e:
			logHandler.log.warning(f"uTalk: Could not unregister settings panel: {e}")
		_utalk_plugin_ref = None
		super().terminate()