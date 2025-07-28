# Reverb Discord Bot

Reverb is a Discord bot that allows server administrators and moderators to efficiently manage messages across multiple channels. It provides functionality for both immediate and scheduled message delivery with support for text content and attachments.

## Features

- 📝 **Multi-Channel Messaging**: Post messages to multiple channels simultaneously
- ⏰ **Message Scheduling**: Schedule messages for future delivery
- 📎 **Attachment Support**: Include files, images, or other attachments with your messages
- 🔍 **Channel Search**: Easily find and select channels using the search feature
- 🔐 **Permission-Aware**: Respects Discord's permission system
- 🎯 **User-Friendly Interface**: Interactive UI components for easy channel selection

## Commands

- `/postmessage`: Send an immediate message to one or more channels
  - Optional: Attach a file when using the command
  - Select target channels using the interactive menu
  - Add optional message text

- `/schedulemessage`: Schedule a message for future delivery
  - Optional: Attach a file when using the command
  - Select target channels using the interactive menu
  - Add optional message text
  - Set delivery time (format: MM/DD/YYYY HH:MM AM/PM)

- `/help`: Display all available commands and their usage

## Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/noahsb96/reverb.git
   cd reverb
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   ```

5. **Run the Bot**
   ```bash
   python launch.py
   ```

## Development

### Project Structure
```
reverb/
├── src/
│   ├── bot.py           # Main bot implementation
│   ├── cogs/            # Command modules
│   ├── ui/              # UI components
│   └── utils/           # Utility functions
├── data/               # Data storage
├── temp_files/         # Temporary file storage
├── requirements.txt    # Dependencies
└── launch.py          # Entry point
```

### Setting Up Development Environment

1. **Install Development Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Code Style**
   - Format code using Black:
     ```bash
     black src/
     ```
   - Sort imports using isort:
     ```bash
     isort src/
     ```
   - Lint code using flake8:
     ```bash
     flake8 src/
     ```

### Testing

Run tests using pytest:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

### Bot Token Security 🔐

Your bot token is like a password - it needs to be kept secure. Follow these guidelines:

1. **Never Commit Tokens**
   - Never commit your `.env` file
   - Never share your token in code or screenshots
   - Use `.env.example` for documentation

2. **Token Rotation**
   If you accidentally expose your token:
   1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   2. Select your application
   3. Go to the "Bot" section
   4. Click "Reset Token"
   5. Update your `.env` file with the new token

3. **Repository Security**
   - Review your git history for exposed tokens
   - If a token was committed:
     1. Reset the token immediately
     2. Consider using [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) to remove sensitive data
     3. Force-push the cleaned history

4. **Best Practices**
   - Use environment variables for sensitive data
   - Regularly audit your security settings
   - Keep dependencies updated
   - Follow Discord's rate limits and terms of service
   - Use a dedicated bot account (not a user account)

## Support

For support, please:
1. Check the `/help` command in Discord
2. Review this documentation
3. Open an issue on GitHub

## Acknowledgments

- Built with [discord.py](https://discordpy.readthedocs.io/)
- Thanks to all contributors
