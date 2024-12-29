import json

def get_tmail(scraper):
    """Fetches a temporary email address using the provided scraper session."""
    email_endpoint = "https://10minutemail.com/session/address"

    try:
        # Get the temporary email address
        email_response = scraper.get(email_endpoint)
        email_response.raise_for_status()

        content = email_response.json()
        return content['address']
    except Exception as e:
        print(f"An error occurred while fetching the email: {e}")
        return None

def get_message(scraper):
    """Fetches messages associated with the temporary email using the same session."""
    messages_endpoint = "https://10minutemail.com/messages/"
    try:
        # Get messages for the temporary email
        messages_response = scraper.get(messages_endpoint)
        messages_response.raise_for_status()

        messages = messages_response.json()

        if messages:
            for message in messages:
                return message.get('bodyPlainText')

    except Exception as e:
        print(f"An error occurred while fetching messages: {e}")
        return None 
