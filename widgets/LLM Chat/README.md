# LLM Chat Widget for Imolia Desktop Customization Tool

## Overview
The LLM Chat Widget is a customizable chat interface that integrates with OpenAI's language models, allowing users to interact with AI directly from their desktop.

## Features
- Real-time chat with AI models
- Customizable appearance (colors, size, position)
- Support for multiple OpenAI models
- Easy-to-use settings interface
- New Chat functionality to start fresh conversations

## Installation

1. Ensure you have the Imolia Desktop Customization Tool installed.
2. Place the `LLMChat.py` file in the widgets folder of your Imolia Desktop Customization Tool installation.
   - Typically located at: `C:\Users\[YourUsername]\Documents\Imolia Desktop Customizer Widgets\`
3. Restart the Imolia Desktop Customization Tool to load the new widget.

## Configuration

1. Open the Imolia Desktop Customization Tool.
2. Go to the settings and find the LLM Chat Widget in the list of available widgets.
3. Click on the settings icon next to the LLM Chat Widget to open its configuration panel.
4. In the configuration panel:
   - Enter your OpenAI API key
   - Select your preferred AI model
   - Customize the widget colors if desired
5. Click 'Save' to apply your settings.

## Usage

1. Activate the LLM Chat Widget from the Imolia Desktop Customization Tool's main interface.
2. The widget will appear on your desktop.
3. Type your message in the input field and press 'Send' or hit Enter to send your message.
4. The AI's response will appear in the chat display above.
5. Use the 'New Chat' button to clear the current conversation and start a new one.

## Customization

You can customize the widget's appearance directly from the widget's settings:
- Background Color: Changes the main background of the widget
- Text Color: Alters the color of the text in the chat display and input field
- Button Color: Modifies the color of the Send and New Chat buttons

## Supported Models

The widget supports various OpenAI models, including but not limited to:
- GPT-4
- GTP-4o
- GPT-3.5-Turbo
- Text-Davinci-003
- And more (check the settings panel for the full list)

## Troubleshooting

- If you encounter any issues with the API connection, ensure your API key is correct and you have the necessary permissions for the selected model.
- If the widget doesn't appear, try restarting the Imolia Desktop Customization Tool.
- For persistent issues, check the `llm_chat_widget.log` file in the widget's directory for error messages.

## Requirements

- Imolia Desktop Customization Tool
- Python 3.7 or higher
- PyQt5 (version 5.15.6 or compatible)
- OpenAI Python library (version 0.27.0 or compatible)

## Support

For additional support or to report issues, please contact the Imolia Desktop Customization Tool support team or open an issue in the project's repository.