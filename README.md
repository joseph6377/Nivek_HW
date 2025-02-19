# Homework Answer Bot

A Telegram bot that provides direct answers to homework questions using Google Gemini AI for text and image based queries.

## Features
- 📖 **Text or Image based question answering** using Gemini AI
- 🏫 **Grade-level specific answers** for elementary, middle, and high school students
- 🔄 **Easy grade-level selection** via interactive buttons
- 🤖 **Automated responses** for text queries

## Prerequisites
- Python 3.8+
- A Telegram bot token from [BotFather](https://t.me/BotFather)
- API key for:
  - [Google Gemini AI](https://ai.google.dev/)

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/homework-answer-bot.git
   cd homework-answer-bot
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Create a `.env` file and add your API keys:
   ```sh
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

## Usage
Run the bot:
```sh
python bot.py
```

### Commands
- `/start` - Start the bot and select grade level
- `/change_grade` - Change grade level

Send a text question to get a direct answer.

## Deployment
To run the bot continuously, use a process manager like `pm2` or deploy it on a cloud service such as AWS, Google Cloud, or Heroku.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License.

