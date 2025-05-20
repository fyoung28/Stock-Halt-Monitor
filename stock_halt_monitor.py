import os
import time
from datetime import datetime
import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET

# Load environment variables
load_dotenv()

# NASDAQ Trader halts feed URL
NASDAQ_HALTS_URL = "https://www.nasdaqtrader.com/rss.aspx?feed=tradehalts"

def print_halt_info(message):
    """Print halt information to console instead of sending SMS"""
    print("\n" + "="*50)
    print(message)
    print("="*50 + "\n")

def get_current_halts():
    """Get current trading halts from NASDAQ Trader"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(NASDAQ_HALTS_URL, headers=headers)
        response.raise_for_status()
        
        # Parse XML feed
        root = ET.fromstring(response.content)
        halts = []
        
        # Find all halt entries
        items = root.findall('.//item')
        print(f"\nFound {len(items)} items in the feed")
        
        for item in items:
            # Get the halt information from the XML elements
            try:
                # Get the basic information
                ticker = item.find('title').text
                halt_date = item.find('.//{http://www.nasdaqtrader.com/}HaltDate').text
                halt_time = item.find('.//{http://www.nasdaqtrader.com/}HaltTime').text
                reason_code = item.find('.//{http://www.nasdaqtrader.com/}ReasonCode').text
                market = item.find('.//{http://www.nasdaqtrader.com/}Market').text
                
                # Get resumption information if available
                resumption_date = item.find('.//{http://www.nasdaqtrader.com/}ResumptionDate')
                resumption_quote_time = item.find('.//{http://www.nasdaqtrader.com/}ResumptionQuoteTime')
                resumption_trade_time = item.find('.//{http://www.nasdaqtrader.com/}ResumptionTradeTime')
                
                # Format the halt information
                halt_info = {
                    'ticker': ticker,
                    'halt_date': halt_date.strip(),
                    'halt_time': halt_time.strip(),
                    'reason_code': reason_code,
                    'market': market,
                    'resumption_date': resumption_date.text.strip() if resumption_date is not None else "Unknown",
                    'resumption_quote_time': resumption_quote_time.text.strip() if resumption_quote_time is not None else "Unknown",
                    'resumption_trade_time': resumption_trade_time.text.strip() if resumption_trade_time is not None else "Unknown"
                }
                
                # Only include halts from today
                if halt_info['halt_date'] == datetime.now().strftime('%m/%d/%Y'):
                    halts.append(halt_info)
                    print(f"Added halt for {ticker} from today")
                else:
                    print(f"Skipping halt for {ticker} - not from today")
                    
            except Exception as e:
                print(f"Error processing item: {str(e)}")
                continue
            
        return halts
    except Exception as e:
        print(f"Error fetching halts: {str(e)}")
        return []

def main():
    print("Starting Stock Halt Monitor (Test Mode)...")
    print("Monitoring NASDAQ Trader halts feed...")
    print("Press Ctrl+C to stop the program")
    print(f"Current date: {datetime.now().strftime('%m/%d/%Y')}")
    
    # Keep track of last seen halts to avoid duplicates
    last_seen_halts = set()
    
    try:
        while True:
            try:
                current_halts = get_current_halts()
                print(f"\nFound {len(current_halts)} halts from today")
                
                # Check for new halts
                for halt in current_halts:
                    halt_key = f"{halt['ticker']}_{halt['halt_date']}_{halt['halt_time']}"
                    if halt_key not in last_seen_halts:
                        message = (
                            f"🚨 TRADING HALT ALERT 🚨\n"
                            f"Ticker: {halt['ticker']}\n"
                            f"Market: {halt['market']}\n"
                            f"Halt Code: {halt['reason_code']}\n"
                            f"Halt Date: {halt['halt_date']}\n"
                            f"Halt Time: {halt['halt_time']}\n"
                            f"Resumption Date: {halt['resumption_date']}\n"
                            f"Resumption Quote Time: {halt['resumption_quote_time']}\n"
                            f"Resumption Trade Time: {halt['resumption_trade_time']}\n"
                            f"Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        print_halt_info(message)
                        last_seen_halts.add(halt_key)
                
                # Keep only the last 100 halts in memory
                if len(last_seen_halts) > 100:
                    last_seen_halts = set(list(last_seen_halts)[-100:])
                    
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                
            # Check every 30 seconds
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\nStopping Stock Halt Monitor...")

if __name__ == "__main__":
    main() 