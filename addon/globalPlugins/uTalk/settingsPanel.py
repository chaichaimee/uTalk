# settingsPanel.py

import wx
import sys
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel
from . import config as uconfig
import addonHandler
import logHandler

addonHandler.initTranslation()

class uTalkSettingsPanel(SettingsPanel):
	title = _("uTalk")

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		self.configData = uconfig.loadConfig()
		
		self.lang_field = sHelper.addLabeledControl(
			_("Alternate language code:"),
			wx.TextCtrl,
			value=self.configData.get("language_alt", "")
		)
		
		commands = [
			("copy", _("Copy")),
			("copyAsPath", _("Copy path")),
			("copyFile", _("Copy file")),
			("cut", _("Cut")),
			("paste", _("Paste")),
			("redo", _("Redo")),
			("save", _("Save")),
			("selectAll", _("Select all")),
			("undo", _("Undo"))
		]
		
		sHelper.addItem(wx.StaticText(self, label=_("Command translations:")))
		self.alt_controls = {}
		
		for key, label in commands:
			self.alt_controls[key] = sHelper.addLabeledControl(
				label,
				wx.TextCtrl,
				value=self.configData.get(f"{key}_alt", "")
			)
		
		resetBtn = wx.Button(self, label=_("Restore Defaults"))
		resetBtn.Bind(wx.EVT_BUTTON, self.onReset)
		sHelper.addItem(resetBtn)

	def onReset(self, event):
		self.lang_field.SetValue(uconfig.DEFAULT_CONFIG.get("language_alt", ""))
		for key, ctrl in self.alt_controls.items():
			ctrl.SetValue(uconfig.DEFAULT_CONFIG.get(f"{key}_alt", ""))

	def get_plugin_instance(self):
		try:
			module = sys.modules['globalPlugins.uTalk']
			return getattr(module, '_utalk_plugin', None)
		except (KeyError, AttributeError):
			return None
	
	def onSave(self):
		new_config = {}
		new_config["language_alt"] = self.lang_field.GetValue()

		for key, ctrl in self.alt_controls.items():
			new_config[f"{key}_alt"] = ctrl.GetValue()
		
		plugin_instance = self.get_plugin_instance()
		if plugin_instance:
			new_config["last_used_language"] = plugin_instance.use_alternate_language
		else:
			new_config["last_used_language"] = bool(new_config["language_alt"].strip())
		
		if uconfig.saveConfig(new_config):
			if plugin_instance:
				plugin_instance.update_config(new_config)
				lang = new_config.get("language_alt", "Alt") if plugin_instance.use_alternate_language else "English"
				plugin_instance._speak(lang, is_direct=True)