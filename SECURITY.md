# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for a security problem. Email **info@imoliamedia.be** with the subject "Security", and describe:

- what you found and where (the program version or commit, the file or widget);
- how to reproduce it, and what an attacker could do with it;
- if you have one, a suggested fix.

We will look into every report and tell you what we decide. Please give us a reasonable amount of time to fix a problem before you publish it.

## Supported versions

Security fixes are made on the `main` branch and go into the next release. Older releases are not patched; update to the newest release.

## How the program deals with trust and secrets

Knowing this helps you judge what is and is not a vulnerability:

- **Widgets are programs.** The program loads and runs every `.py` file that is in the widgets folder (`Documents\Imolia Desktop Customizer Widgets`) with your Windows user's rights. Only install widgets you trust, and only from sources you trust. Widgets that come with this repository are reviewed before they are included.
- **Dependencies are installed from PyPI** on request (the **Installeer** button), with exact versions pinned in each widget's `Dependencies:` block.
- **Secrets are encrypted per Windows user.** The Gmail Inbox widget (app passwords) and the LLM Chat widget (OpenAI key) encrypt them with Windows DPAPI, so only the same Windows user on the same PC can read them. Other settings are stored as plain text in `<widget>_config.json` next to the widget. This includes the **secret iCal addresses** used by the Google Calendar widget; anyone who can read your widgets folder can read those.
- **Nothing is sent to us.** The program has no telemetry. Widgets that talk to the internet do so only to the services you configured (Gmail, your calendar's iCal URL, OpenAI, devices on your network); see the privacy table in the [User Guide](docs/USER_GUIDE.md#10-privacy-and-security).
- **Mail shown in the Gmail Inbox widget is treated as untrusted.** Formatted mail is sanitized (scripts, frames and forms removed, images never loaded) before it is displayed.
- Widgets never write secrets or what you type to the log.
