# __init__.py
# Copyright (C) 2026 Chai Chaimee
# Licensed under GNU General Public License. See COPYING.txt for details.

import addonHandler

addonHandler.initTranslation()

# Import and instantiate the actual plugin class from sub-module
from .uTalkCore import GlobalPlugin
