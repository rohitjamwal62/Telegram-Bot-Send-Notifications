import configparser, requests, time, asyncio, smtplib
from telethon.sync import TelegramClient, errors
from telethon.events import NewMessage
from email.mime.text import MIMEText

# Create a configparser object and read the configuration file
config = configparser.ConfigParser()
config.read('config.ini')
# Read values from the configuration file
api_id = config.getint('Telegram', 'api_id')  # Convert to int
api_hash = config.get('Telegram', 'api_hash')
phone_number = config.get('Telegram', 'phone_number')
# User Id
Wizard_Assistant_Id = config.getint('Users', 'Wizard_Assistant_Id')  # Convert to int
# Group Id
Weekly_Wizdom = config.getint('Groups', 'Weekly_Wizdom')  # Convert to int
# Group Name
Weekly_Wizdom_group = config.get('GroupName', 'Weekly_Wizdom_group')
# Email Setting
SMTP_SERVER = config.get('Email', 'SMTP_SERVER')
SMTP_PORT = config.getint('Email', 'SMTP_PORT')  # Convert to int
EMAIL_USERNAME = config.get('Email', 'EMAIL_USERNAME')
EMAIL_PASSWORD = config.get('Email', 'EMAIL_PASSWORD')
RECIPIENT_EMAIL = config.get('Email', 'RECIPIENT_EMAIL')

def push_notifications(store_message, Message_Sender_name,groups_names):
    Token = config.get('PushNotification', 'Token')
    UserId = config.get('PushNotification', 'UserId')
    Message = f"Hi {Message_Sender_name}, {store_message}"
    url = "https://api.pushover.net/1/messages.json"
    payload = f'token={Token}&user={UserId}&message={Message}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    retry_count,retry_delay = 3,2
    for _ in range(retry_count):
        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout=2)
            print("Running push......", store_message)
            break  # If successful, exit the retry loop
        except requests.Timeout:
            print(f"Request timed out. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)  # Wait before retrying
        except requests.RequestException as e:
            print(f"Request error: {e}")
            break  # Exit the loop if an exception occurs

def send_email(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_USERNAME
    msg['To'] = RECIPIENT_EMAIL
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, RECIPIENT_EMAIL, msg.as_string())

# Initialize the TelegramClient within an async context
async def main():
    async with TelegramClient('session_name', api_id, api_hash) as client:
        try:
            await client.start(phone_number)
            @client.on(NewMessage(chats=Weekly_Wizdom))
            async def handle_testing_2_message(event):
                await handle_message(event, Weekly_Wizdom_group)
            await client.run_until_disconnected()
        except errors.SessionPasswordNeededError:
            print("The session file is locked with a password. Please unlock it or remove the session file.")
        except Exception as e:
            print(f"An error occurred: {e}")

async def handle_message(event, groups_names):
    try:
        if not hasattr(event, 'handled') or not event.handled:
            message = event.message
            store_message = message.text  # Store the message text
            sender_id = message.sender_id  # Get the sender's ID
            print("working")
            dialogs = await event.client.get_dialogs()
            match_found = False  # Initialize a flag to track if a match is found

            for dialog in dialogs:
                if dialog.is_group:
                    group_entity = dialog.entity
                    group_id = dialog.id
                    group_name = dialog.name
                    participants = await event.client.get_participants(group_entity)

                    for participant in participants:
                        UserId = participant.id
                        UserName = participant.first_name

                        if UserId == sender_id:
                            Message_Sender_name = UserName
                            if len(UserName) <= 1:
                                Message_Sender_name = participant.username
                            print(store_message, "************")
                            if  Wizard_Assistant_Id == sender_id:
                                print("\n\n")
                                print(f"{Message_Sender_name} has sent a new message from the {groups_names} group    : {store_message}")
                                print("\n\n")
                                push_notifications(store_message, Message_Sender_name, groups_names)
                                send_email(f"{Message_Sender_name} has sent a new message from the {groups_names} group    : ",store_message)

                            match_found = True  # Set the flag to True
                            break  # Exit the inner loop when a match is found

                    if match_found:
                        break  # Exit the outer loop when a match is found

            event.handled = True  # Set a flag to indicate that the event has been handled
    except Exception as e:
        print(f"Error handling message: {e}")

if __name__ == '__main__':
    asyncio.run(main())