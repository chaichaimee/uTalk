# __init__.py

import globalPluginHandler
import speech
import addonHandler
import inputCore
import scriptHandler
import logHandler
import gui
import api
import winUser
import time
import browseMode
import textInfos
import treeInterceptorHandler
import keyboardHandler
from gui.settingsDialogs import NVDASettingsDialog
from . import config as uconfig
from . import settingsPanel
import tones
import controlTypes

addonHandler.initTranslation()

if hasattr(controlTypes, 'State'):
    controlTypes.STATE_SELECTED = controlTypes.State.SELECTED
    controlTypes.STATE_READONLY = controlTypes.State.READONLY

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("uTalk")

    def __init__(self):
        super().__init__()
        # Load config and ensure all default keys are present
        loaded_config = uconfig.loadConfig()
        self.config = uconfig.DEFAULT_CONFIG.copy() # Start with all defaults
        self.config.update(loaded_config) # Overlay with anything loaded from file

        self.use_alternate_language = self.config.get("last_used_language", False)
        
        self._register_gestures_separately()
        # Removed _update_speech_language() call because speech.setLanguage is not available

        try:
            logHandler.log.info(f"uTalk: Loading settingsPanel from {settingsPanel.__file__}")
            NVDASettingsDialog.categoryClasses.append(settingsPanel.uTalkSettingsPanel)
        except Exception as e:
            logHandler.log.error(f"Failed to register settings panel: {e}")

    def _register_gestures_separately(self):
        """Register gestures separately as in tTalk"""
        gestures = [
            ("kb:NVDA+alt+t", "toggleLanguage"),
            ("kb:control+c", "announceCopy"),
            ("kb:control+v", "announcePaste"),
            ("kb:control+x", "announceCut"),
            ("kb:control+z", "announceUndo"),
            ("kb:control+y", "announceRedo"), # Add redo gesture with Ctrl+Y
            ("kb:control+shift+z", "announceRedo"), # Add redo gesture with Ctrl+Shift+Z
            ("kb:control+a", "announceSelectAll"),
            ("kb:control+s", "announceSave"),
            ("kb:control+shift+c", "announceCopyAsPath"),
            ("kb:control+alt+c", "announceCopyFile")
        ]
        
        for gesture, script in gestures:
            try:
                self.bindGesture(gesture, script)
                logHandler.log.info(f"uTalk: Successfully bound {gesture}")
            except Exception as e:
                logHandler.log.error(f"uTalk: Failed to bind {gesture}: {str(e)}")

    def _get_selected_text_robust(self, obj_param):
        """
        Retrieves selected text using makeTextInfo or Ctrl+C fallback
        """
        logHandler.log.info("uTalk: _get_selected_text_robust started.")
        current_obj = obj_param
        selected_text = None

        try:
            target_obj_for_text = None
            if hasattr(current_obj, 'treeInterceptor') and isinstance(current_obj.treeInterceptor, browseMode.BrowseModeDocumentTreeInterceptor):
                target_obj_for_text = current_obj.treeInterceptor
                logHandler.log.info("uTalk: Using treeInterceptor for text info.")
            elif hasattr(current_obj, 'makeTextInfo'):
                target_obj_for_text = current_obj
            
            if target_obj_for_text:
                try:
                    info = target_obj_for_text.makeTextInfo(textInfos.POSITION_SELECTION)
                    if info and not info.isCollapsed:
                        selected_text = info.clipboardText
                        if selected_text:
                            logHandler.log.info(f"uTalk: Retrieved text via makeTextInfo")
                            return selected_text.replace('\r\n', '\n').replace('\r', '\n').strip()
                except (RuntimeError, NotImplementedError) as e:
                    logHandler.log.warning(f"uTalk: makeTextInfo failed: {str(e)}")
            else:
                logHandler.log.info("uTalk: No makeTextInfo available")

        except Exception as e_info:
            logHandler.log.debug(f"uTalk: makeTextInfo error: {str(e_info)}")

        logHandler.log.info("uTalk: Attempting Ctrl+C fallback")
        original_clipboard_data = ""
        try:
            # New way to manage clipboard without context manager
            # to avoid WinError 0 issues
            if winUser.openClipboard(gui.mainFrame.Handle):
                try:
                    original_clipboard_data = winUser.getClipboardData(winUser.CF_UNICODETEXT) or ""
                    winUser.emptyClipboard()
                finally:
                    winUser.closeClipboard()
                
            keyboardHandler.injectKey("control+c") # Use injectKey for reliable simulation
            time.sleep(0.1) # Give system a moment to process the paste
            
            # Retrieve data from new clipboard
            if winUser.openClipboard(gui.mainFrame.Handle):
                try:
                    clipboard_text = winUser.getClipboardData(winUser.CF_UNICODETEXT) or ""
                    if clipboard_text:
                        selected_text = clipboard_text
                        logHandler.log.info("uTalk: Retrieved text via Ctrl+C fallback")
                        return selected_text.replace('\r\n', '\n').replace('\r', '\n').strip()
                finally:
                    winUser.closeClipboard()

        except Exception as e_fallback:
            # Don't notify the user about the error
            pass
        finally:
            try:
                # Restore the original clipboard
                if winUser.openClipboard(gui.mainFrame.Handle):
                    try:
                        winUser.emptyClipboard()
                        if original_clipboard_data:
                            winUser.setClipboardData(winUser.CF_UNICODETEXT, original_clipboard_data)
                    finally:
                        winUser.closeClipboard()
            except Exception as e_restore:
                # Don't notify the user about the error
                pass

        logHandler.log.info("uTalk: No selected text found")
        return None

    def _speak_word(self, word):
        try:
            if isinstance(word, str):
                word = word.strip()
                speech.speak([word], priority=speech.Spri.NORMAL)
        except Exception as e:
            # Don't notify the user about the error
            pass

    def _get_message(self, key):
        default = uconfig.DEFAULT_CONFIG.get(key, "")
        return self.config.get(f"{key}_alt", default) if self.use_alternate_language else default

    def script_announceCopy(self, gesture):
        try:
            obj = api.getFocusObject()
            app_name = obj.appModule.appName.lower() if obj.appModule else ""
            
            # Browser/text field handling
            if app_name in ("chrome", "firefox", "edge", "msedge", "opera", "safari", "brave") or \
               hasattr(obj, 'makeTextInfo'):
                selected_text = self._get_selected_text_robust(obj)
                if selected_text:
                    api.copyToClip(selected_text)
                    self._speak_word(self._get_message("copy"))
                    return

            # File Explorer handling or generic copy
            gesture.send() # Always send the original gesture first
            if app_name == "explorer":
                self._speak_word(self._get_message("copyFile"))
            else:
                self._speak_word(self._get_message("copy"))

        except Exception as e:
            # Don't notify the user about the error
            pass

    script_announceCopy.__doc__ = _("copy")

    def script_announcePaste(self, gesture):
        self._speak_word(self._get_message("paste"))
        gesture.send()
    script_announcePaste.__doc__ = _("paste")

    def script_announceCut(self, gesture):
        self._speak_word(self._get_message("cut"))
        gesture.send()
    script_announceCut.__doc__ = _("cut")

    def script_announceUndo(self, gesture):
        self._speak_word(self._get_message("undo"))
        gesture.send()
    script_announceUndo.__doc__ = _("undo")

    def script_announceRedo(self, gesture):
        self._speak_word(self._get_message("redo"))
        gesture.send()
    script_announceRedo.__doc__ = _("redo")

    def script_announceSelectAll(self, gesture):
        self._speak_word(self._get_message("selectAll"))
        gesture.send()
    script_announceSelectAll.__doc__ = _("select all")

    def script_announceSave(self, gesture):
        self._speak_word(self._get_message("save"))
        gesture.send()
    script_announceSave.__doc__ = _("save")

    def script_announceCopyAsPath(self, gesture):
        # Check if we are in File Explorer
        try:
            obj = api.getFocusObject()
            app_name = obj.appModule.appName.lower() if obj.appModule else ""
            
            # Only announce in File Explorer
            if app_name != "explorer":
                # Pass the gesture through without handling
                # This allows other addons to use the same shortcut
                gesture.send()
                return
                
            # We are in File Explorer, so announce and send the gesture
            self._speak_word(self._get_message("copyAsPath"))
            gesture.send()
            
        except Exception as e:
            # Don't notify the user about the error
            gesture.send() # Always pass through the gesture

    script_announceCopyAsPath.__doc__ = _("copy as path")

    def script_announceCopyFile(self, gesture):
        self._speak_word(self._get_message("copyFile"))
        gesture.send()
    script_announceCopyFile.__doc__ = _("copy file")

    def script_toggleLanguage(self, gesture):
        logHandler.log.info(f"uTalk: script_toggleLanguage called. Current self.config before *re-load*: {self.config}")
        # Force reload config from file to ensure we have the latest saved data
        self.config = uconfig.loadConfig()
        logHandler.log.info(f"uTalk: script_toggleLanguage: self.config AFTER re-load from file: {self.config}")

        self.use_alternate_language = not self.use_alternate_language
        self.config["last_used_language"] = self.use_alternate_language
        logHandler.log.info(f"uTalk: script_toggleLanguage: self.config after toggle logic (before save): {self.config}")
        uconfig.saveConfig(self.config)
        
        lang_to_speak = self.config.get("language_alt", "Alternate") if self.use_alternate_language else "English"
        self._speak_word(lang_to_speak)
        logHandler.log.info(f"uTalk: script_toggleLanguage completed.")

    script_toggleLanguage.__doc__ = _("Toggle language")

    def terminate(self):
        try:
            NVDASettingsDialog.categoryClasses.remove(settingsPanel.uTalkSettingsPanel)
        except:
            pass
        super().terminate()
