# -*- coding: utf-8 -*-
# clipboard.py
# Copyright (C) 2025 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import wx
import os
import time
import addonHandler
import logHandler

addonHandler.initTranslation()

class ClipboardMonitor:
    def getClipboard(self):
        """Safely get clipboard content with proper cleanup"""
        clipboard = None
        try:
            clipboard = wx.Clipboard.Get()
            if clipboard.Open():
                if clipboard.IsSupported(wx.DataFormat(wx.DF_FILENAME)):
                    file_data = wx.FileDataObject()
                    clipboard.GetData(file_data)
                    result = file_data.GetFilenames()
                elif clipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                    text_data = wx.TextDataObject()
                    clipboard.GetData(text_data)
                    result = text_data.GetText()
                else:
                    result = None
                clipboard.Close()
                return result
        except Exception as e:
            logHandler.log.error(f"Clipboard error: {str(e)}")
            return None
        finally:
            if clipboard and clipboard.IsOpened():
                clipboard.Close()
