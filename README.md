<div align="center">

<img src="https://www.nvaccess.org/files/nvda/documentation/userGuide/images/nvda.ico" alt="NVDA Logo" width="120" />

# uTalk

Hear every Copy, Paste, Cut, Undo and Save as it happens &mdash; in the words you choose.

**author:** chai chaimee  
**url:** https://github.com/chaichaimee/uTalk

</div>

---

## Introduction

uTalk speaks a short confirmation every time you use a common editing shortcut &mdash; Copy, Paste, Cut, Undo, Redo, Select All, Save, Copy Path, and Copy File. Instead of wondering whether your Ctrl+C actually worked, uTalk quietly announces "copy" (or whatever word you prefer) right after the action happens.

Every announced word can be replaced with your own text, and you can even keep two full sets of announcements &mdash; for example English and your native language &mdash; and switch between them instantly with a single hotkey tap.

uTalk also pays special attention to copying selected text while browsing the web in NVDA's Browse Mode, where a normal Ctrl+C often fails silently because the selection only exists inside NVDA's virtual buffer.

---

### Hot Keys

> **NVDA+Alt+T**  
> Single Tap : Toggle between English and your alternate language for all announcements  
> Double Tap : Open the uTalk Settings panel

> **Control+C**  
> Single Tap : Copy, then announce "copy" (or your custom word)

> **Control+V**  
> Single Tap : Paste, then announce "paste"

> **Control+X**  
> Single Tap : Cut, then announce "cut"

> **Control+Z**  
> Single Tap : Undo, then announce "undo"

> **Control+Y or Control+Shift+Z**  
> Single Tap : Redo, then announce "redo"

> **Control+A**  
> Single Tap : Select all, then announce "select all"

> **Control+S**  
> Single Tap : Save, then announce "save"

> **Control+Shift+C**  
> Single Tap : Announce "copy as path" (Windows Explorer only), then perform the shortcut

> **Control+Alt+C**  
> Single Tap : Announce "copy file" (Windows Explorer only), then perform the shortcut

> [!NOTE]  
> uTalk listens to these standard Windows shortcuts directly. Your shortcut always still runs as normal &mdash; uTalk only adds a spoken confirmation on top of it.

---

## Features

### 1. Spoken Confirmation for Everyday Commands

Whenever you press Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+Z, Ctrl+Y (or Ctrl+Shift+Z), Ctrl+A, or Ctrl+S, uTalk lets the keystroke through to the application first and then, shortly afterward, speaks a short word confirming what happened. By default the words are plain English: "copy", "paste", "cut", "undo", "redo", "select all", and "save".

To keep NVDA responsive, announcements are never spoken instantly on the keystroke itself &mdash; uTalk waits a fraction of a second (100 milliseconds) before speaking, so the application has time to actually finish the action first.

As a safety measure, any announced text is capped at 200 characters; if you ever configure a very long custom phrase, it will be cut short with "...truncated" added at the end so it can never overwhelm the speech output.

### 2. Smart Copy Handling in Browse Mode

Copying text while reading a web page in NVDA's Browse Mode works differently from copying in a normal editable field, and uTalk handles both cases correctly:

**Step by step, when you press Control+C:**

1. uTalk checks whether your current focus is inside a Browse Mode virtual document (for example, a web page in a browser).

2. If you **are** in Browse Mode: a text selection made with Shift+Arrow keys exists only inside NVDA's own virtual buffer, not as a real selection in the browser itself. Sending the normal Ctrl+C in this situation would copy nothing at all. So instead, uTalk reads the selected text directly from NVDA's virtual buffer and places it on the clipboard itself using NVDA's own clipboard function. If no text is selected, it simply forwards your Ctrl+C as normal.

3. If you are **not** in Browse Mode (for example, typing in a text box or word processor): a real, OS-level selection already exists, so uTalk forwards your Ctrl+C to the application first, letting the application perform its own copy (this preserves any special formatting the application itself would normally copy).

4. In both cases, once the copy is done, uTalk announces "copy" (or your custom word).

### 3. Explorer-Only Announcements for Copy Path and Copy File

Windows Explorer has two extra shortcuts that do not exist in most other programs: Copy as Path (Ctrl+Shift+C) and Copy File (Ctrl+Alt+C). uTalk checks whether the currently focused window actually belongs to Windows Explorer before announcing these two commands, so you will only hear "copy as path" or "copy file" while working in Explorer itself, never in other applications where those same key combinations might mean something else.

### 4. One Hotkey, Two Jobs: Language Toggle and Settings Access

> NVDA+Alt+T is a single hotkey that behaves differently depending on how many times you tap it in quick succession:
> 
> **Single Tap** &mdash; uTalk waits up to 500 milliseconds to see if you will tap again. If you don't, it switches your active announcement language (English or your alternate language) and immediately speaks the new language's name aloud as confirmation, then saves this choice so it is remembered the next time you start NVDA.
> 
> **Double Tap** (or more) &mdash; If a second tap arrives within 600 milliseconds of the first, uTalk instead opens the NVDA Settings dialog directly to the uTalk category, so you can edit your custom phrases.
> 
> Internally, every tap resets a short timer; only once the timer expires without another tap does uTalk decide what actually happened, which is what allows one hotkey to distinguish a single tap from a double tap.

### 5. Fully Customizable Command Phrases

Opening the uTalk Settings panel (via NVDA's own Settings dialog, or by double-tapping NVDA+Alt+T) gives you a text field for an alternate language name, plus one text field for each command: Copy, Copy Path, Copy File, Cut, Paste, Redo, Save, Select All, and Undo. Whatever you type in these fields becomes what NVDA speaks for that command when your alternate language is active.

A "Restore Defaults" button clears every field back to blank, matching uTalk's built-in defaults.

Saving your changes updates the running add-on immediately (no restart needed) and speaks a quick confirmation in the currently active language.

> [!NOTE]  
> To keep the Settings dialog from ever freezing while it opens, the panel reads its current values from the add-on's in-memory settings rather than reading the configuration file from disk at that moment.

### 6. Reliable Settings Storage

Your customized phrases are saved to a configuration file in your NVDA user configuration folder, inside a "ChaiChaimee" subfolder. Saving is done safely: uTalk first writes your settings to a temporary file, then swaps it into place, and finally re-reads the saved file to confirm it matches exactly what was meant to be saved &mdash; protecting your settings from being lost or corrupted if something interrupts the save.

If you have an older version of uTalk that stored its settings in a different location, uTalk automatically moves your existing settings the first time it loads, so you don't lose your customizations when updating.

---

## Support Me

If this tool has made your life easier, consider fueling the next update with a small donation.

[![Donate Support Me](https://img.shields.io/badge/Donate-Support%20Me-blue?style=for-the-badge&logo=stripe)](https://buy.stripe.com/dRm9AU1xQ3Ds22N6VK1VK01)

Your support means the world. Let's build something great together

&copy; 2026 Chai Chaimee NVDA Add-on Released under GNU GPL