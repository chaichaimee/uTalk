![NVDA Logo](https://www.nvaccess.org/files/nvda/documentation/userGuide/images/nvda.ico)

# uTalk

Hear every Copy, Paste, Undo and Save confirmed, in your language, only when it really happened.

**author:** chai chaimee

**url:** https://github.com/chaichaimee/uTalk

## Introduction

uTalk gives you instant spoken confirmation for the editing commands you use every day: Copy, Cut, Paste, Undo, Redo, Select All, Save, Copy as path and Copy file. Instead of wondering whether a shortcut worked, you hear it.

uTalk checks that the action really took effect before it speaks, so you are not told "copy" when nothing was copied. It works with two language profiles that you can swap with a single key press, lets you set different behavior for each application, and lets you choose whether confirmations come as speech, braille or a short beep. Every phrase can be changed to your own wording.

## Hot Keys

**NVDA+Alt+T**

- Single Tap : Swap between the main language and the alternate language
- Double Tap : Open uTalk settings
- Triple Tap : Turn uTalk off or on for the current application
- Four Taps : Mute or unmute uTalk announcements

The mute command and the current application command can also be given their own keys. Open NVDA menu > Preferences > Input Gestures, find the uTalk category, and assign a key to "Mute or unmute uTalk announcements" or "Turn uTalk off or on for the current application". The multi tap command appears there as "uTalk multi tap".

**Keys that uTalk announces**

- **Control+C** : Copy
- **Control+X** : Cut
- **Control+V** : Paste
- **Control+Z** : Undo
- **Control+Y** or **Control+Shift+Z** : Redo
- **Control+A** : Select all
- **Control+S** : Save
- **Control+Shift+C** : Copy as path (announced in File Explorer only)
- **Control+Alt+C** : Copy file (announced in File Explorer only)

uTalk passes each of these keys on to the application as usual. It only adds the announcement.

## Features

### Smart Copy and Cut Confirmation

After you press Control+C or Control+X, uTalk waits to see whether the clipboard actually changed. If it did, you hear "copy" or "cut". If nothing was placed on the clipboard, you hear "Nothing to copy" or "Nothing to cut" instead.

**Example:** You press Control+C with nothing selected. uTalk says "Nothing to copy" rather than confirming a copy that never happened.

Paste is announced only where pasting is possible. In browse mode and in read-only fields, Control+V is not announced.

You can turn this checking off with the option "Announce copy, cut and paste only when they take effect" in the settings. When it is off, the command name is always announced.

### Copying in Browse Mode

On web pages and other documents in browse mode, a selection exists only inside NVDA, so the application would copy nothing. uTalk copies your selected text for you, so Control+C works in browse mode and is confirmed like any other copy.

### One Announcement per Action

If you hold a shortcut down or press it repeatedly and quickly, uTalk gives you a single announcement instead of a long queue of repeated messages.

### Dual Language Profiles

uTalk keeps two sets of phrases: the main language (English) and an alternate language of your choice. Press NVDA+Alt+T once to swap between them. uTalk announces the name of the language you switched to. NVDA remembers which language you used last.

If a command has no alternate phrase, uTalk uses its English phrase. If you press the swap key before setting up any alternate phrase, uTalk tells you that the alternate language is not set and reminds you to open the settings.

**How to set up the alternate language:**

1. Press NVDA+Alt+T twice to open the uTalk settings.
2. In "Alternate language code", type the name you want to hear when you switch to this language.
3. In the "Command translations" fields, type your own phrase for each command: Copy, Copy path, Copy file, Cut, Paste, Redo, Save, Select all and Undo.
4. Activate OK to save.
5. Press NVDA+Alt+T once to start using the alternate language.

### Output Choices

Choose how uTalk gives you its confirmations in the "Announcement output" list:

- Speech and braille
- Speech only
- Braille only
- Beep only

With "Beep only", each command has its own tone, so you can tell Copy from Paste or Save by pitch alone. A lower error tone is played when there was nothing to copy or cut.

### Announcement Detail

The "Announcement detail" list has two levels: Short and Detailed.

**Short** says only the command name, for example "copy".

**Detailed** adds more information:

- Copy, cut and paste report the number of characters, and the number of lines when there is more than one line. For example: "copy 2 lines 50 characters". A line break at the very end of the text is not counted as an extra line.
- In editable fields, undo and redo tell you what changed, for example "undo removed hello", "redo added world" or "undo replaced cat with dog". Long pieces of text are shortened, and text that is only spaces is described as "whitespace".

Detailed information is not used with "Beep only". For very large texts, and in applications that read text too slowly, undo and redo give the plain command name.

### Per-Application Rules

You can decide how uTalk behaves in each application. Each rule has the form **name=value**, one per line, where name is the program name (the ".exe" ending is optional and capital letters do not matter) and value is one of:

- **off** : uTalk stays silent in that application
- **main** : always use the main language phrases in that application
- **alt** : always use the alternate language phrases in that application

By default uTalk is silent in Command Prompt, PowerShell and Windows Terminal. Applications without a rule follow the language you selected with NVDA+Alt+T.

**How to add a rule:**

1. Press NVDA+Alt+T twice to open the uTalk settings.
2. Move to the "Application rules" field.
3. Type a new line, for example: notepad=alt
4. Activate OK to save.

**Quick switch for the current application:** Press NVDA+Alt+T three times while working in an application. uTalk adds or removes an "off" rule for it and tells you, for example, "uTalk off for notepad" or "uTalk on for notepad". The change is saved automatically.

### Mute

Press NVDA+Alt+T four times to mute all uTalk announcements, and press it four times again to unmute. Muting also cancels any announcement that is waiting to be spoken.

### Customizable Phrases

The main language phrases are Copy, Copy as path, Copy file, Cut, Paste, Redo, Save, Select all and Undo. Each one has an alternate field in the settings where you can write your own wording. Each phrase can be up to 200 characters.

### Safe Settings

The settings dialog protects you from mistakes:

- Text longer than 200 characters is refused, and uTalk tells you which field to shorten.
- An application rule that is not valid is refused, and uTalk tells you which line to correct. Use name=off, name=main or name=alt.
- The "Restore Defaults" button returns every setting to its original value.

Your settings are stored in the file uTalk.json in userConfig\\ChaiChaimee\\uTalk\\. If you used an older version of uTalk, your existing settings file is moved to this location automatically when NVDA starts, and the old copy is removed once the new one is checked. If a value in the file is of the wrong type, uTalk replaces it with the default value.

## Support Me

If this tool has made your life easier, consider fueling the next update with a small donation.

[![Support me](https://img.shields.io/badge/Donate-Support%20Me-blue?style=for-the-badge&logo=stripe)](https://buy.stripe.com/dRm9AU1xQ3Ds22N6VK1VK01)

Your support means the world. Let's build something great together

© 2026 Chai Chaimee NVDA Add-on Released under GNU GPL
