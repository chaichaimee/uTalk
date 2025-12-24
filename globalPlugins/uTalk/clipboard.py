# clipboard.py

import wx
import os
import time
import threading
import addonHandler

addonHandler.initTranslation()

class ClipboardMonitor:
    def __init__(self):
        # Initialize clipboard lock
        self._clipboard_lock = threading.Lock()
        self._last_error_time = 0

    def _try_open_clipboard(self, max_attempts=3, delay=0.1):
        # Attempt to open clipboard with retry mechanism
        attempts = 0
        clipboard = wx.Clipboard.Get()
        while attempts < max_attempts:
            try:
                if clipboard.Open():
                    return True, clipboard
            except Exception:
                pass
            time.sleep(delay)
            attempts += 1
        return False, None

    def getClipboard(self):
        """Safely get clipboard content with proper cleanup"""
        with self._clipboard_lock:
            success, clipboard = self._try_open_clipboard()
            if not success:
                return None

            try:
                if clipboard.IsSupported(wx.DataFormat(wx.DF_FILENAME)):
                    file_data = wx.FileDataObject()
                    clipboard.GetData(file_data)
                    files = file_data.GetFilenames()
                    return files if len(files) > 1 else files[0] if files else None
                elif clipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                    text_data = wx.TextDataObject()
                    clipboard.GetData(text_data)
                    text = text_data.GetText()
                    return text if text else None
                return None
            finally:
                try:
                    clipboard.Close()
                except Exception:
                    pass
