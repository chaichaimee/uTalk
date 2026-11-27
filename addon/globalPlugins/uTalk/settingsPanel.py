# settingsPanel.py

import sys
import wx
import gui
import addonHandler
from gui import guiHelper
from gui.settingsDialogs import SettingsPanel
from . import config as uconfig

addonHandler.initTranslation()


def _getOutputChoices():
	return (
		("speechBraille", _("Speech and braille")),
		("speech", _("Speech only")),
		("braille", _("Braille only")),
		("beep", _("Beep only"))
	)


def _getVerbosityChoices():
	return (
		("short", _("Short")),
		("detailed", _("Detailed (adds counts and what undo or redo changed)"))
	)


def _getChoiceIndex(choices, value):
	for index, (choiceValue, choiceLabel) in enumerate(choices):
		if choiceValue == value:
			return index
	return 0


class uTalkSettingsPanel(SettingsPanel):
	title = _("uTalk")

	def getPluginInstance(self):
		try:
			pluginRef = sys.modules["globalPlugins.uTalk.uTalkCore"]._utalkPluginRef
			return pluginRef() if pluginRef else None
		except (KeyError, AttributeError):
			return None

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Read the already-loaded in-memory config from the running plugin
		# instance rather than touching disk here; makeSettings must not
		# perform file I/O, or the Settings dialog itself can hang while
		# opening.
		pluginInstance = self.getPluginInstance()
		self.configData = pluginInstance.config if pluginInstance else uconfig.getDefaultConfig()

		self.langField = sHelper.addLabeledControl(
			_("Alternate language code:"),
			wx.TextCtrl,
			value=self.configData.get("language_alt", "")
		)

		self.outputChoices = _getOutputChoices()
		self.outputChoice = sHelper.addLabeledControl(
			_("Announcement &output:"),
			wx.Choice,
			choices=[label for value, label in self.outputChoices]
		)
		self.outputChoice.SetSelection(_getChoiceIndex(self.outputChoices, self.configData.get("outputMode")))

		self.verbosityChoices = _getVerbosityChoices()
		self.verbosityChoice = sHelper.addLabeledControl(
			_("Announcement &detail:"),
			wx.Choice,
			choices=[label for value, label in self.verbosityChoices]
		)
		self.verbosityChoice.SetSelection(_getChoiceIndex(self.verbosityChoices, self.configData.get("verbosity")))

		self.verifyCheckBox = sHelper.addItem(
			wx.CheckBox(self, label=_("Announce copy, cut and paste &only when they take effect"))
		)
		self.verifyCheckBox.SetValue(bool(self.configData.get("verifyActions", True)))

		self.rulesField = sHelper.addLabeledControl(
			_("&Application rules (one per line: name=off, name=main or name=alt):"),
			wx.TextCtrl,
			style=wx.TE_MULTILINE,
			size=self.scaleSize((500, 120)),
			value=uconfig.formatAppRules(self.configData.get("appRules", {}))
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
		self.altControls = {}
		self.altLabels = {}

		for key, label in commands:
			self.altLabels[key] = label
			self.altControls[key] = sHelper.addLabeledControl(
				label,
				wx.TextCtrl,
				value=self.configData.get(f"{key}_alt", "")
			)

		resetBtn = wx.Button(self, label=_("Restore Defaults"))
		resetBtn.Bind(wx.EVT_BUTTON, self.onReset)
		sHelper.addItem(resetBtn)

	def onReset(self, event):
		defaults = uconfig.getDefaultConfig()
		self.langField.SetValue(defaults["language_alt"])
		self.outputChoice.SetSelection(_getChoiceIndex(self.outputChoices, defaults["outputMode"]))
		self.verbosityChoice.SetSelection(_getChoiceIndex(self.verbosityChoices, defaults["verbosity"]))
		self.verifyCheckBox.SetValue(defaults["verifyActions"])
		self.rulesField.SetValue(uconfig.formatAppRules(defaults["appRules"]))
		for key, ctrl in self.altControls.items():
			ctrl.SetValue(defaults.get(f"{key}_alt", ""))

	def _reportInvalid(self, message, ctrl):
		gui.messageBox(message, _("Invalid configuration"), wx.OK | wx.ICON_ERROR, self)
		ctrl.SetFocus()

	def isValid(self):
		tooLongMessage = _("The text is longer than {limit} characters. Shorten it before saving.")
		if len(self.langField.GetValue()) > uconfig.MAX_PHRASE_LENGTH:
			self._reportInvalid(tooLongMessage.format(limit=uconfig.MAX_PHRASE_LENGTH), self.langField)
			return False
		for key, ctrl in self.altControls.items():
			if len(ctrl.GetValue()) > uconfig.MAX_PHRASE_LENGTH:
				self._reportInvalid(
					f"{tooLongMessage.format(limit=uconfig.MAX_PHRASE_LENGTH)}\n{self.altLabels[key]}",
					ctrl
				)
				return False
		rules, errorLine = uconfig.parseAppRules(self.rulesField.GetValue())
		if rules is None:
			self._reportInvalid(
				_("Line {line} of the application rules is not valid. Use name=off, name=main or name=alt.").format(
					line=errorLine
				),
				self.rulesField
			)
			return False
		return True

	def onSave(self):
		pluginInstance = self.getPluginInstance()
		newConfig = dict(self.configData)
		newConfig["language_alt"] = self.langField.GetValue()
		newConfig["outputMode"] = self.outputChoices[self.outputChoice.GetSelection()][0]
		newConfig["verbosity"] = self.verbosityChoices[self.verbosityChoice.GetSelection()][0]
		newConfig["verifyActions"] = self.verifyCheckBox.GetValue()
		newConfig["appRules"] = uconfig.parseAppRules(self.rulesField.GetValue())[0]

		for key, ctrl in self.altControls.items():
			newConfig[f"{key}_alt"] = ctrl.GetValue()

		if pluginInstance:
			newConfig["last_used_language"] = pluginInstance.useAlternateLanguage
		else:
			newConfig["last_used_language"] = bool(newConfig["language_alt"].strip())

		if uconfig.saveConfig(newConfig) and pluginInstance:
			pluginInstance.updateConfig(newConfig)
			pluginInstance.announceLanguage()
