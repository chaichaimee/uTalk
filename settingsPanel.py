# settingsPanel.py
# Copyright (C) 2025 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import wx
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
        self.configData = uconfig.loadConfig() # Use configData as in old script
        
        # Language code
        self.lang_field = sHelper.addLabeledControl(
            _("Alternate language code:"),
            wx.TextCtrl,
            value=self.configData.get("language_alt", "")
        )
        
        # Commands
        commands = [
            ("copy", _("Copy")),
            ("copyAsPath", _("Copy path")),
            ("copyFile", _("Copy file")),
            ("cut", _("Cut")),
            ("paste", _("Paste")),
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
        
        # Reset button
        resetBtn = wx.Button(self, label=_("Restore Defaults"))
        resetBtn.Bind(wx.EVT_BUTTON, self.onReset)
        sHelper.addItem(resetBtn)

    def onReset(self, event):
        # Reset values in UI to default
        self.lang_field.SetValue(uconfig.DEFAULT_CONFIG.get("language_alt", ""))
        for key, ctrl in self.alt_controls.items():
            ctrl.SetValue(uconfig.DEFAULT_CONFIG.get(f"{key}_alt", ""))
    
    def onSave(self):
        new_config = {}
        
        # Log values before retrieving
        logHandler.log.info(f"uTalk: SettingsPanel: onSave called.")
        
        # Populate with values from UI controls
        new_config["language_alt"] = self.lang_field.GetValue()
        logHandler.log.info(f"uTalk: SettingsPanel: Retrieved language_alt: '{new_config['language_alt']}'")

        for key, ctrl in self.alt_controls.items():
            value = ctrl.GetValue()
            new_config[f"{key}_alt"] = value
            logHandler.log.info(f"uTalk: SettingsPanel: Retrieved {key}_alt: '{value}'")
        
        # Handle 'last_used_language' based on whether an alternate language code is set
        new_config["last_used_language"] = bool(new_config["language_alt"].strip())
        
        # Save the new_config
        if uconfig.saveConfig(new_config):
            logHandler.log.info("uTalk: Settings saved successfully.")
            
            # Import main_plugin here to avoid circular dependency
            from . import __init__ as main_plugin
            if hasattr(main_plugin, 'GlobalPlugin'):
                # Update the running plugin's config data
                main_plugin.GlobalPlugin.config = new_config
                main_plugin.GlobalPlugin.use_alternate_language = new_config["last_used_language"]
                
                # Speak the selected language immediately after saving settings
                lang = new_config.get("language_alt", "Alternate") if main_plugin.GlobalPlugin.use_alternate_language else "English"
                main_plugin.GlobalPlugin._speak_word(lang)
        else:
            logHandler.log.error("uTalk: Failed to save settings.")
