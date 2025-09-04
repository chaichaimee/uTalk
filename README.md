<div align="center">

# uTalk

</div>


Monitors clipboard content and announces actions (copy, cut, paste, etc.) in either English or an alternate language (configurable).


**Author:** Chai Chaimee  

**URL:** https://github.com/chaichaimee/uTalk


## Overview

uTalk enhances your clipboard experience by monitoring clipboard content, maintaining a history, and announcing actions in multiple languages.  

With uTalk, you'll receive audible confirmation of clipboard operations and can easily switch between languages.  

Hear clipboard operation confirmations in your preferred language with easy toggling between languages.  

**Smart Application Handling**: Different behaviors for File Explorer, web browsers, and text editors ensure optimal clipboard operations.  

**Persistent Settings**: Tailor each announcement to your preference in the settings panel. Your language preferences and custom messages are saved between sessions.  


## Keyboard Commands

**NVDA + Alt + T** — Toggle Language: Switches between primary and alternate language.  


## Usage

1. Install uTalk through NVDA's add-on manager (**NVDA Menu → Tools → Manage Add-ons**).  

2. After installation, you'll hear **"uTalk loaded"** confirmation.  

3. Use standard clipboard commands (**Ctrl+C, Ctrl+V, etc.**) as you normally would.  

4. uTalk will announce each action in your current language setting.  

5. Press **NVDA+Alt+T** to toggle between languages.  


## Configure Your Preferred Alternate Language

1. Open **NVDA Menu → Preferences → Settings**.  

2. Select **uTalk** category from the list.  

3. In **"Language code for alternate commands"** field, enter your preferred language code (e.g., `"th"` for Thai, `"es"` for Spanish).  

4. In uTalk settings, locate the command you want to customize.  

5. Enter your preferred announcement in the text field for:  

   - Copy  
   - Copy as path  
   - Copy file  
   - Cut  
   - Paste  
   - Save  
   - Select all  
   - Undo  
   - Redo  

6. Click **OK** to save your custom messages.  


## Note

Language toggling (**NVDA+Alt+T**) works immediately after changing settings.  

The alternate language uses your custom messages if configured, or the language code you provided.  
