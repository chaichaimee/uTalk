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
from gui.settingsDialogs import NVDASettingsDialog
from . import config as uconfig
from . import settingsPanel

addonHandler.initTranslation()

_utalk_plugin = None

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("uTalk")

	def __init__(self):
		super().__init__()
		global _utalk_plugin
		_utalk_plugin = self
		
		self.config = uconfig.loadConfig()
		self.use_alternate_language = self.config.get("last_used_language", False)
		
		self._tap_count = 0
		self._last_tap_time = 0
		self._tap_timer = None
		
		core.callLater(500, self._bind_gestures)

		try:
			if settingsPanel.uTalkSettingsPanel not in NVDASettingsDialog.categoryClasses:
				NVDASettingsDialog.categoryClasses.append(settingsPanel.uTalkSettingsPanel)
		except:
			pass

	def _bind_gestures(self):
		if not _utalk_plugin:
			return
		gestures = [
			("kb:NVDA+alt+t", "toggle_or_settings"),
			("kb:control+c", "announceCopy"),
			("kb:control+v", "announcePaste"),
			("kb:control+x", "announceCut"),
			("kb:control+z", "announceUndo"),
			("kb:control+y", "announceRedo"),
			("kb:control+shift+z", "announceRedo"),
			("kb:control+a", "announceSelectAll"),
			("kb:control+s", "announceSave"),
			("kb:control+shift+c", "announceCopyAsPath"),
			("kb:control+alt+c", "announceCopyFile")
		]
		for gesture, script in gestures:
			try:
				self.bindGesture(gesture, script)
			except:
				pass

	def _safe_speak(self, key_or_text, is_direct=False):
		def task():
			if not _utalk_plugin:
				return
			if is_direct:
				ui.message(key_or_text.strip())
				return
			
			msg = self.config.get(f"{key_or_text}_alt", "") if self.use_alternate_language else uconfig.DEFAULT_CONFIG.get(key_or_text, "")
			if msg:
				ui.message(msg.strip())
		core.callLater(100, task)

	def _get_selected_text_robust(self, obj_param):
		"""
		Retrieves selected text using makeTextInfo or Ctrl+C fallback.
		Returns plain text or None.
		"""
		current_obj = obj_param
		selected_text = None

		try:
			target_obj_for_text = None
			if hasattr(current_obj, 'treeInterceptor') and isinstance(current_obj.treeInterceptor, browseMode.BrowseModeDocumentTreeInterceptor):
				target_obj_for_text = current_obj.treeInterceptor
			elif hasattr(current_obj, 'makeTextInfo'):
				target_obj_for_text = current_obj
			
			if target_obj_for_text:
				try:
					info = target_obj_for_text.makeTextInfo(textInfos.POSITION_SELECTION)
					if info and not info.isCollapsed:
						selected_text = info.clipboardText
						if selected_text:
							return selected_text.replace('\r\n', '\n').replace('\r', '\n').strip()
				except (RuntimeError, NotImplementedError):
					pass
		except Exception:
			pass

		# Fallback: simulate Ctrl+C and read clipboard
		original_clipboard_data = ""
		clipboard = None
		try:
			clipboard = wx.Clipboard.Get()
			if clipboard.Open():
				try:
					if clipboard.IsSupported(wx.DataFormat(wx.DF_UNICODETEXT)):
						data = wx.TextDataObject()
						clipboard.GetData(data)
						original_clipboard_data = data.GetText() or ""
					clipboard.Clear()
				finally:
					clipboard.Close()
				
			keyboardHandler.injectKey("control+c")
			time.sleep(0.05)
			
			if clipboard.Open():
				try:
					if clipboard.IsSupported(wx.DataFormat(wx.DF_UNICODETEXT)):
						data = wx.TextDataObject()
						clipboard.GetData(data)
						clipboard_text = data.GetText() or ""
						if clipboard_text:
							selected_text = clipboard_text
							return selected_text.replace('\r\n', '\n').replace('\r', '\n').strip()
				finally:
					clipboard.Close()
		except Exception:
			pass
		finally:
			try:
				if clipboard and clipboard.Open():
					try:
						clipboard.Clear()
						if original_clipboard_data:
							data = wx.TextDataObject(original_clipboard_data)
							clipboard.SetData(data)
					finally:
						clipboard.Close()
			except Exception:
				pass

		return None

	def script_announceCopy(self, gesture):
		try:
			obj = api.getFocusObject()
			if not obj:
				core.callLater(0, gesture.send)
				self._safe_speak("copy")
				return

			app_name = obj.appModule.appName.lower() if obj.appModule else ""
			
			# Only browsers use the plain-text fallback
			browser_apps = {"chrome", "firefox", "edge", "msedge", "opera", "safari", "brave"}
			
			if app_name in browser_apps:
				selected_text = self._get_selected_text_robust(obj)
				if selected_text:
					api.copyToClip(selected_text)
					self._safe_speak("copy")
					return
				else:
					# If fallback fails, pass through the original gesture
					core.callLater(0, gesture.send)
					self._safe_speak("copy")
			else:
				# For all other apps (Word, Excel, PowerPoint, Notepad, etc.) use native gesture
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
		now = wx.GetLocalTimeMillis()
		if (now - self._last_tap_time) > 600:
			self._tap_count = 0
		self._tap_count += 1
		self._last_tap_time = now
		if self._tap_timer and self._tap_timer.IsRunning():
			self._tap_timer.Stop()
		self._tap_timer = wx.CallLater(500, self._handle_tap)

	def _handle_tap(self):
		if not _utalk_plugin:
			return
		if self._tap_count == 1:
			self.use_alternate_language = not self.use_alternate_language
			self.config["last_used_language"] = self.use_alternate_language
			uconfig.saveConfig(self.config)
			name = self.config.get("language_alt", "Alt") if self.use_alternate_language else "English"
			self._safe_speak(name, is_direct=True)
		elif self._tap_count >= 2:
			import gui
			core.callLater(300, gui.mainFrame.popupSettingsDialog, NVDASettingsDialog, settingsPanel.uTalkSettingsPanel)
		self._tap_count = 0

	def update_config(self, new_config):
		self.config.update(new_config)
		self.use_alternate_language = self.config.get("last_used_language", self.use_alternate_language)

	def terminate(self):
		global _utalk_plugin
		if self._tap_timer:
			try:
				self._tap_timer.Stop()
			except:
				pass
		self._tap_timer = None
		try:
			NVDASettingsDialog.categoryClasses.remove(settingsPanel.uTalkSettingsPanel)
		except:
			pass
		_utalk_plugin = None
		super().terminate()