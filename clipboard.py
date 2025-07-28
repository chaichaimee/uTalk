# -*- coding: utf-8 -*-
# clipboard.py
# Copyright (C) 2025 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import wx
import os
import time
import addonHandler
import logHandler
import winUser
import ctypes
import threading

addonHandler.initTranslation()

class ClipboardMonitor:
    def __init__(self):
        self._clipboard_lock = threading.Lock()
        self._last_error_time = 0

    def _try_open_clipboard(self, max_attempts=3, delay=0.1):
        attempts = 0
        while attempts < max_attempts:
            try:
                if winUser.openClipboard(None):
                    return True
            except Exception:
                pass
            time.sleep(delay)
            attempts += 1
        return False

    def getClipboard(self):
        """Safely get clipboard content with proper cleanup"""
        if not self._try_open_clipboard():
            current_time = time.time()
            if current_time - self._last_error_time > 60:  # Only log once per minute
                logHandler.log.debug("uTalk: Could not open clipboard after multiple attempts")
                self._last_error_time = current_time
            return None

        try:
            if winUser.isClipboardFormatAvailable(winUser.CF_HDROP):
                file_data = ctypes.create_unicode_buffer(260)
                handle = winUser.getClipboardData(winUser.CF_HDROP)
                if handle:
                    file_count = ctypes.windll.shell32.DragQueryFileW(handle, -1, None, 0)
                    if file_count > 0:
                        files = []
                        for i in range(file_count):
                            ctypes.windll.shell32.DragQueryFileW(handle, i, file_data, ctypes.sizeof(file_data))
                            files.append(file_data.value)
                        return files if len(files) > 1 else files[0]
            elif winUser.isClipboardFormatAvailable(winUser.CF_UNICODETEXT):
                text = winUser.getClipboardData(winUser.CF_UNICODETEXT)
                return text if text else None
            return None
        except Exception as e:
            logHandler.log.debug(f"uTalk: Clipboard access error: {str(e)}")
            return None
        finally:
            try:
                winUser.closeClipboard()
            except Exception:
                pass
