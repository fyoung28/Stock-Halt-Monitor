import os
import time
import feedparser
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
from twilio.rest import Client

# Load environment variables
load_dotenv()

# Configure Twilio
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
YOUR_PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER')

# Debug logging for Twilio setup
print("\nTwilio Configuration Status:")
print(f"Account SID present: {'Yes' if TWILIO_ACCOUNT_SID else 'No'}")
print(f"Auth Token present: {'Yes' if TWILIO_AUTH_TOKEN else 'No'}")
print(f"Twilio Phone Number: {TWILIO_PHONE_NUMBER}")
print(f"Your Phone Number: {YOUR_PHONE_NUMBER}\n")

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Set to store processed entries to avoid duplicates
processed_entries = set()
last_check_time = None

def send_notification(message):
    """Send notification via SMS using Twilio."""
    try:
        # Send SMS
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=YOUR_PHONE_NUMBER
        )
        print(f"SMS sent! SID: {sms.sid}")
        
        # Also print to console
        print("\n" + "="*50)
        print(message)
        print("="*50 + "\n")
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        # Fallback to console output if SMS fails
        print("\n" + "="*50)
        print(message)
        print("="*50 + "\n")

def fetch_feed():
    """Fetch the RSS feed with cache-busting headers."""
    feed_url = 'https://www.nasdaqtrader.com/rss.aspx?feed=TradeHalts'
    headers = {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Add timestamp to prevent caching
        timestamp = int(time.time())
        feed_url = f"{feed_url}&_={timestamp}"
        
        print(f"\nFetching feed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Fetch the feed content
        response = requests.get(feed_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the feed content
        feed = feedparser.parse(response.content)
        return feed
    except Exception as e:
        print(f"Error fetching feed: {str(e)}")
        return None

def parse_halt_table(description):
    """Parse the HTML table in the description to extract halt details."""
    try:
        soup = BeautifulSoup(description, 'html.parser')
        # Find the first row of data (after header)
        row = soup.find('tr').find_next('tr')
        if row:
            # Get all cells in the row
            cells = row.find_all('td')
            if len(cells) >= 9:
                halt_date = cells[0].text.strip()
                halt_time = cells[1].text.strip()
                
                # Parse the halt date and time
                try:
                    halt_datetime = datetime.strptime(f"{halt_date} {halt_time}", '%m/%d/%Y %H:%M:%S')
                except ValueError:
                    print(f"Error parsing halt datetime: {halt_date} {halt_time}")
                    halt_datetime = None
                
                return {
                    'halt_date': halt_date,
                    'halt_time': halt_time,
                    'halt_datetime': halt_datetime,
                    'symbol': cells[2].text.strip(),
                    'name': cells[3].text.strip(),
                    'market': cells[4].text.strip(),
                    'reason_code': cells[5].text.strip(),
                    'resumption_date': cells[7].text.strip(),
                    'resumption_quote_time': cells[8].text.strip() if len(cells) > 8 else '',
                    'resumption_trade_time': cells[9].text.strip() if len(cells) > 9 else ''
                }
    except Exception as e:
        print(f"Error parsing halt table: {str(e)}")
    return None

def parse_halt_entry(entry):
    """Parse a halt entry from the RSS feed."""
    try:
        # Extract the title which contains the halt information
        title = entry.title.strip()
        
        # Get the published date and convert to local time
        try:
            # Parse the GMT time
            gmt_time = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S GMT')
            # Convert to local time
            local_time = gmt_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Error parsing time: {str(e)}")
            local_time = entry.published

        # Parse the HTML table in the description
        halt_details = None
        if hasattr(entry, 'description'):
            halt_details = parse_halt_table(entry.description)

        if halt_details:
            # Set N/A if missing
            quote_time = halt_details['resumption_quote_time'] if halt_details['resumption_quote_time'] else 'N/A'
            trade_time = halt_details['resumption_trade_time'] if halt_details['resumption_trade_time'] else 'N/A'
            return {
                'symbol': halt_details['symbol'],
                'name': halt_details['name'],
                'market': halt_details['market'],
                'reason_code': halt_details['reason_code'],
                'halt_time': halt_details['halt_time'],
                'resumption_quote_time': quote_time,
                'resumption_trade_time': trade_time,
                'published': local_time,
                'halt_datetime': halt_details['halt_datetime']
            }
        else:
            return {
                'symbol': title,
                'name': 'Unknown',
                'market': 'Unknown',
                'reason_code': 'Unknown',
                'halt_time': 'Unknown',
                'resumption_quote_time': 'N/A',
                'resumption_trade_time': 'N/A',
                'published': local_time,
                'halt_datetime': None
            }
    except Exception as e:
        print(f"Error parsing entry: {str(e)}")
    return None

def check_halts():
    """Check for new trading halts using the NASDAQ RSS feed."""
    global last_check_time
    
    try:
        # Fetch and parse the NASDAQ Trading Halts RSS feed
        feed = fetch_feed()
        if not feed:
            print("Failed to fetch feed")
            return
        
        # Debug: Print feed status
        print(f"\nFeed Status: {feed.status if hasattr(feed, 'status') else 'No status'}")
        print(f"Number of entries: {len(feed.entries)}")
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\nChecking for halts... (Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        if last_check_time:
            print(f"Last check time: {last_check_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        alerts = []  # List to store alerts
        
        for entry in feed.entries:
            # Parse the halt information
            halt_info = parse_halt_entry(entry)
            
            if halt_info and halt_info['halt_datetime']:
                try:
                    # Check if the halt was published today
                    entry_date = halt_info['halt_datetime'].strftime('%Y-%m-%d')
                    
                    # Check if this entry is newer than our last check
                    if last_check_time and halt_info['halt_datetime'] <= last_check_time:
                        print(f"Skipping older entry: {halt_info['symbol']} halted at {halt_info['halt_datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
                        continue
                    
                    if entry_date == today:
                        print(f"Processing new entry: {halt_info['symbol']} halted at {halt_info['halt_datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # Create the message
                        message = (
                            f"🚨 TRADING HALT ALERT 🚨\n"
                            f"Symbol: {halt_info['symbol']}\n"
                            f"Name: {halt_info['name']}\n"
                            f"Market: {halt_info['market']}\n"
                            f"Reason Code: {halt_info['reason_code']}\n"
                            f"Halt Time: {halt_info['halt_time']}\n"
                            f"Resumption Quote Time: {halt_info['resumption_quote_time']}\n"
                            f"Resumption Trade Time: {halt_info['resumption_trade_time']}\n"
                            f"Published: {halt_info['halt_datetime'].strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        
                        # Append the alert to the list
                        alerts.append(message)
                        
                        # Keep the set size manageable by removing old entries
                        if len(processed_entries) > 1000:
                            processed_entries.clear()
                except Exception as e:
                    print(f"Error processing date: {str(e)}")
                    print(f"Problematic date string: {halt_info['published']}")
        
        # Update last check time
        last_check_time = datetime.now()
        
        # Print alerts in reverse order (most recent at the bottom)
        for alert in reversed(alerts):
            send_notification(alert)
        
    except Exception as e:
        print(f"Error checking halts: {str(e)}")

def main():
    """Main function to run the halt monitor."""
    print("Starting Stock Halt Monitor (RSS Feed Version)...")
    print("Monitoring for trading halts...")
    print("Press Ctrl+C to stop the program")
    
    while True:
        try:
            check_halts()
            # Wait for 60 seconds before checking again
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nStopping Stock Halt Monitor...")
            break
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main() 