# Gmail Inbox Widget

Shows the unread mail of **several Gmail addresses at once**, and checks for new mail every X minutes.

## Features

- One row per account with an unread counter
- Give each account a **display name** (e.g. "Private", "Work"): the widget then shows only that name and never the e-mail address, so visitors can't read your addresses off the screen. Without a name, the address is shown
- Click an address to open that account's Gmail in your default browser (it opens the right account via `authuser`)
- Click the arrow next to the counter to list the newest unread messages (sender, subject, time)
- Click a message to open that conversation in Gmail
- Hover a message to **mark it as read** (✓) or **move it to the trash** (🗑, happens immediately without asking; recoverable from Gmail's Trash for 30 days)
- New mail: the account row flashes for 15 seconds and a sound plays. Pick the sound yourself: any of the Windows sounds, or your own `.wav` file (settings play a preview when you choose one)
- **Do not disturb**: the bell button (🔔) in the widget header silences the sound and the flashing. Counters and lists keep updating. The setting is remembered until you click the bell again (🔕 = silent)
- Accounts that can't be checked show a red `!`; hover it to see why
- Passwords are stored encrypted with Windows DPAPI — only your Windows user can read them

## Setting up an account

Gmail no longer accepts your normal password in other apps, so every account needs an **app password**:

1. Turn on 2-Step Verification for the Google account (if it isn't on already).
2. Go to <https://myaccount.google.com/apppasswords> and create an app password (name it e.g. "Imolia widget"). Google shows 16 characters, spaces don't matter.
3. In the widget click ⚙ (or use Settings → Widgets in the tray menu), then **Toevoegen…**, enter the address, a display name and the app password and press **Testen** to verify it. Use **Bewerken…** later to change the name or the app password (leave the password empty to keep it).

Repeat for each address. App passwords are not available for accounts with Advanced Protection, or when a Google Workspace admin has disabled them.

## Settings

- Accounts: address, display name, app password
- Check interval (1–120 minutes)
- Number of unread messages shown per account
- Sound on new mail: on/off and which sound (Windows sounds or your own `.wav`)
- Background opacity and text color

## Notes

- Checking only *reads* the inbox; it never marks mail as read. Opening mail in the widget (clicking it) opens Gmail, which marks it read as usual.
- Moving to the trash is reversible: the message ends up in Gmail's Trash folder.
- Use the mouse wheel to scroll when the list is longer than the widget.
- The widget talks to `imap.gmail.com` directly. Nothing is sent anywhere else.

## Troubleshooting

- *"Inloggen mislukt"*: the app password is wrong or was revoked. Create a new one and use **Bewerken…**.
- *"Geen verbinding met Gmail"*: no internet, or a firewall blocks `imap.gmail.com:993`.
- Check the application logs for details.
