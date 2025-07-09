
uTalk  
Enhanced Clipboard Experience for NVDA  
by Chai Chaimee  
Version 2025.2  
Overview  

uTalk enhances your clipboard experience by monitoring clipboard content, maintaining a history, and announcing actions in multiple languages. With uTalk, you'll receive audible confirmation of clipboard operations and can easily switch between languages.  
Note: uTalk requires NVDA 2022.4 or newer. Last tested with NVDA 2025.1.  
Key Features  
Multilingual Announcements  

Hear clipboard operation confirmations in your preferred language with easy toggling between languages.  
Smart Application Handling  

Different behaviors for File Explorer, web browsers, and text editors ensure optimal clipboard operations.
Customizable Messages  

Tailor each announcement to your preference in the settings panel.  
Persistent Settings  

Your language preferences and custom messages are saved between sessions.  
Keyboard Commands  
Command 	Function 	Description  
Ctrl + C 	Copy 	Copies selected content with announcement  
Ctrl + V 	Paste 	Pastes clipboard content with announcement  
Ctrl + X 	Cut 	Cuts selected content with announcement  
Ctrl + Z 	Undo 	Undoes last action with announcement  
Ctrl + A 	Select All 	Selects all content with announcement  
Ctrl + S 	Save 	Saves document with announcement  
Ctrl + Shift + C 	Copy As Path 	Copies file path with announcement (File Explorer)  
Ctrl + Alt + C 	Copy File 	Copies file with announcement  
NVDA + Alt + T 	Toggle Language 	Switches between primary and alternate language  
Getting Started  

uTalk works immediately after installation with sensible defaults. Follow these steps to begin:  

    Install uTalk through NVDA's add-on manager (NVDA Menu → Tools → Manage Add-ons)  
    After installation, you'll hear "uTalk loaded" confirmation  
    Use standard clipboard commands (Ctrl+C, Ctrl+V, etc.) as you normally would  
    uTalk will announce each action in your current language setting  
    Press NVDA+Alt+T to toggle between languages  

Tip: uTalk intelligently handles different applications:  

    In web browsers, it ensures proper text copying  
    In File Explorer, it announces "copy file" when copying files  
    In text editors, it uses standard clipboard announcements  

Customization  

uTalk offers extensive customization options to tailor your experience:  
Language Settings  

Configure your preferred alternate language:  

    Open NVDA Menu → Preferences → Settings  
    Select uTalk category from the list  
    In "Language code for alternate commands" field, enter your preferred language code (e.g., "th" for Thai, "es" for Spanish)  
    Click OK to save your settings  

Custom Messages  

Personalize each announcement in your alternate language:  

    In uTalk settings, locate the command you want to customize  
    Enter your preferred announcement in the text field:  
        Copy  
        Copy as path  
        Copy file  
        Cut  
        Paste  
        Save  
        Select all  
        Undo  
    Click OK to save your custom messages  

Reset to Defaults  

If needed, you can restore original settings:  

    In uTalk settings, click the "Restore Defaults" button  
    All custom messages and language settings will be reset  
    Click OK to apply the reset  

Note: Language toggling (NVDA+Alt+T) works immediately after changing settings. The alternate language uses your custom messages if configured, or the language code you provided.  
Troubleshooting  

If you encounter issues with uTalk:  

    Verify NVDA version: Ensure you're using NVDA 2022.4 or newer  
    Check conflicts: Temporarily disable other clipboard-related add-ons  
    Reset settings: Try restoring default settings in uTalk configuration  
    Review logs: Check the NVDA log (NVDA Menu → Tools → View Log) for error messages  
    Reinstall: Try uninstalling and reinstalling the add-on  

Common issues and solutions:  

    No announcements: Check if uTalk is enabled in the add-on manager  
    Language not changing: Verify you entered a valid language code in settings  
    Clipboard issues in browsers: Ensure you have the latest version of uTalk  

Support & Contribution  

uTalk is an open-source project. For support, feature requests, or to contribute:  

    GitHub Repository: https://github.com/chaichaimee/uTalk  
    Issue Tracking: Report bugs or request features through GitHub Issues  
    Contribution: Pull requests are welcome for improvements and translations  

Version Information  
Current Version: 2025.2  
Minimum NVDA Version: 2022.4  
Last Tested NVDA Version: 2025.1  
Release Date: February 2025  

uTalk Add-on | Developed by Chai Chaimee | Licensed under GNU General Public License  

Documentation generated on: July 9, 2025    
# uTalk
Monitors clipboard content and announces actions (copy, cut, paste, etc.) in either English or an alternate language (configurable)
