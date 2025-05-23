# Stock Halt Monitor (RSS Feed Version)

A real-time monitoring system that alerts you via SMS when stocks are halted on major exchanges. The program uses the NASDAQ RSS feed to monitor trading halts and sends notifications using Twilio.

## Features

- Real-time monitoring of trading halts via NASDAQ RSS feed
- SMS notifications via Twilio
- Detailed halt information including:
  - Ticker symbol and company name
  - Market (NASDAQ, NYSE, etc.)
  - Halt reason code
  - Actual halt time (from the halt table)
  - Resumption quote and trade times
  - Published time
- HTML table parsing for accurate halt details
- Duplicate detection to prevent spam
- 60-second monitoring interval
- Terminal output with detailed debug information
- Cache-busting to ensure fresh feed data

## Prerequisites

- Python 3.7 or higher
- A Twilio account (for SMS functionality)
- Your Twilio credentials (Account SID and Auth Token)
- A regular Twilio phone number (not toll-free)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/fyoung28/Stock-Halt-Monitor.git
   cd Stock-Halt-Monitor
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your Twilio credentials:
   ```
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
   YOUR_PHONE_NUMBER=your_phone_number_here
   ```

## Usage

Run the program:
```bash
python3 stock_halt_monitor_rss.py
```

The program will:
- Monitor the NASDAQ RSS feed every 60 seconds
- Show detailed debug information in the terminal
- Send an SMS notification when a new halt is detected
- Include comprehensive information about the halt
- Continue running until manually stopped (Ctrl+C)

## Halt Codes

Common halt codes include:
- T1: Halt - News Pending
- T2: Halt - News Released
- T3: Halt - News and Resumption Times
- T6: Halt - Extraordinary Market Activity
- T8: Halt - ET System Error
- H4: Halt - Non-compliance
- H9: Halt - Not Current
- H10: Halt - SEC Trading Suspension
- H11: Halt - Regulatory Concern
- LUDP: Limit Up Limit Down Trading Pause

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NASDAQ Trader for providing the RSS feed
- Twilio for SMS functionality
- BeautifulSoup for HTML parsing 