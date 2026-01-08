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
            ("redo", _("Redo")), # Add redo to commands list
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

    def get_plugin_instance(self):
        """Get the plugin instance from the module"""
        try:
            # Import the module that contains the plugin
            module = sys.modules['globalPlugins.uTalk']
            # Get the module-level variable
            return getattr(module, '_utalk_plugin', None)
        except (KeyError, AttributeError):
            return None
    
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
        
        # Get the current plugin instance
        plugin_instance = self.get_plugin_instance()
        if plugin_instance:
            # Preserve the current language setting from the running plugin
            new_config["last_used_language"] = plugin_instance.use_alternate_language
            logHandler.log.info(f"uTalk: SettingsPanel: Preserving last_used_language: {new_config['last_used_language']}")
        else:
            # If plugin instance not found, set based on whether language code is set
            new_config["last_used_language"] = bool(new_config["language_alt"].strip())
            logHandler.log.warning("uTalk: Plugin instance not found, using language_alt to determine last_used_language")
        
        # Save the new_config to file
        if uconfig.saveConfig(new_config):
            logHandler.log.info("uTalk: Settings saved to file successfully.")
            
            # Update the running plugin's config data immediately
            if plugin_instance:
                # Update configuration directly without reloading from file
                plugin_instance.update_config(new_config)
                
                # Speak the selected language immediately after saving settings
                lang = new_config.get("language_alt", "Alternate") if plugin_instance.use_alternate_language else "English"
                plugin_instance._speak_word(lang)
                logHandler.log.info(f"uTalk: Settings updated immediately. Current language: {lang}")
        else:
            logHandler.log.error("uTalk: Failed to save settings to file.")