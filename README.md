# Rise of Kingdoms Timer Bot

Automatic bot for tracking timers in Rise of Kingdoms game with OCR recognition and Telegram notifications.

## 📋 Requirements

- **Python**: 3.10.10
- **Tesseract OCR**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki) and install
- **Windows**: Application works only on Windows (uses win32gui)

## 📦 Installation

pip install pywin32 PyQt5 mss requests opencv-python numpy pytesseract pyrogram python-telegram-bot

## 📦 Or via Python launcher:

py -3.10 -m pip install pywin32 PyQt5 mss requests opencv-python numpy pytesseract pyrogram python-telegram-bot

⚙️ Setup
1. Creating Telegram Bot
Open @BotFather in Telegram and send /newbot command

Choose a name and username for your bot (e.g., my_rok_bot)

You will receive BOT_TOKEN in format: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

Copy the token to BOT_TOKEN variable in rok_panel.py and rok_tg_bot.py

2. Getting Channel ID
Create a channel in Telegram (private or public)

Add your bot to the channel as administrator

Send any message to the channel

Open in browser:

text
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
Replace <YOUR_BOT_TOKEN> with your token

Find in response "chat":{"id":-1001234567890,...}

Copy this number (with minus!) to CHANNEL_ID variable

3. Getting USER_ID
Method 1 (via bot):

Open @userinfobot in Telegram

Press /start

Bot will send your User ID

Method 2 (manually):

Send a message to your bot

Open:

text
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
Find "from":{"id":123456789,...}

Copy the number to USER_ID variable

4. Getting API_ID and API_HASH (for Pyrogram)
Open https://my.telegram.org

Login with your phone number

Go to API development tools

Fill in the application creation form:

App title: any name (e.g., "RoK Timer")

Short name: short name (e.g., "roktimer")

Platform: Desktop

You will receive api_id (number) and api_hash (string)

Copy them to API_ID and API_HASH variables

5. Installing Tesseract OCR
Download installer: tesseract-ocr-w64-setup-5.x.x.exe

Install Tesseract (remember installation path, default is C:\Program Files\Tesseract-OCR)

In rok_panel.py find the line:

python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
If you installed to a different location, change the path

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
6. First Launch (Pyrogram Authorization)
When you first run the panel, Pyrogram will ask for authorization:

Enter your phone number (in format +7********)

Enter confirmation code from Telegram

If two-factor authentication is enabled, enter password

After authorization, rok_userbot.session file will be created — it stores your session locally.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

🚀 Launch
Running Panel (GUI)

py -3.10 rok_panel.py

Running Bot (background)

py -3.10 rok_tg_bot.py

📝 File Structure
text
rok-timer-bot/
├── rok_panel.py          # GUI panel for OCR and sending timers
├── rok_tg_bot.py         # Telegram bot for receiving timers
├── run_panel.bat         # Batch file for quick panel launch
├── accounts.json         # Stores account list (created automatically)
├── region.json           # Stores selected OCR region (created automatically)
├── timers.json           # Stores active timers (created automatically)
├── waifu.ico             # Icon for .exe files
└── README.md             # This file

🔧 Building .exe Files (optional)
If you want to distribute ready-made exe files:

Install PyInstaller:

py -3.10 -m pip install pyinstaller
Build panel:

py -3.10 -m PyInstaller rok_panel.py --onefile --hidden-import=win32gui --hidden-import=win32api --hidden-import=pywintypes --icon=waifu.ico
Build bot:

py -3.10 -m PyInstaller rok_tg_bot.py --onefile --noconsole --icon=waifu.ico
Ready files will be in dist/ folder

## 📖 Usage

Run the bot (`rok_tg_bot.py`)

Run the panel (`rok_panel.py`)

In the panel:
- Select an account or add a new one
- Click "Region" and select the zone with timers in the game
- Click "Screenshot" — timers will be automatically recognized and sent to Telegram channel

Bot will send notifications when timers complete

### ⚠️ Important: Timer Recognition

**The OCR only works correctly when the green progress bar has NOT yet reached the timer numbers.**

If the progress bar has already covered the numbers, the timer won't be recognized. Make sure to capture screenshots while timers are still fresh (progress bar hasn't reached the digits yet).

📜 License
MIT License — do whatever you want with the code.

## Credits
Developed with assistance of AI tools


