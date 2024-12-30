# Create New Mega Accounts
# Saves credentials to a file called accounts.csv

import subprocess
import os
import time
import re
import random
import string
import csv
import threading
import argparse
import cloudscraper
from faker import Faker

fake = Faker()

# Custom function for checking if the argument is below a certain value
def check_limit(value):
    ivalue = int(value)
    if ivalue <= 8:
        return ivalue
    else:
        raise argparse.ArgumentTypeError(f"You cannot use more than 8 threads.")

# Set up command line arguments
parser = argparse.ArgumentParser(description="Create New Mega Accounts")
parser.add_argument("-n", "--number", type=int, default=3, help="Number of accounts to create")
parser.add_argument("-t", "--threads", type=check_limit, default=None, help="Number of threads to use for concurrent account creation")
parser.add_argument("-p", "--password", type=str, default=None, help="Password to use for all accounts")
args = parser.parse_args()

def find_url(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    return [x[0] for x in re.findall(regex, string)]

def get_random_string(length):
    """Generate a random string with a given length."""
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(length))

def command_exists(command):
    """Check if a command is available on the system."""
    return subprocess.call(["which", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

class MegaAccount:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.email = None
        self.scraper = cloudscraper.create_scraper()
        self.use_megatools = command_exists("megatools")
        self.use_megareg = command_exists("megareg")
        if not self.use_megatools and not self.use_megareg:
            raise EnvironmentError("Neither 'megatools' nor 'megareg' is available on this system.")

    def generate_email(self):
        """Fetches a temporary email address using a service."""
        email_endpoint = "https://10minutemail.com/session/address"
        try:
            email_response = self.scraper.get(email_endpoint)
            email_response.raise_for_status()
            content = email_response.json()
            return content['address']
        except Exception as e:
            print(f"An error occurred while fetching the email: {e}")
            return None

    def get_mail(self):
        """Fetches messages associated with the temporary email."""
        messages_endpoint = "https://10minutemail.com/messages/"
        try:
            messages_response = self.scraper.get(messages_endpoint)
            messages_response.raise_for_status()
            messages = messages_response.json()

            if messages:
                for message in messages:
                    return message.get('bodyPlainText')

        except Exception as e:
            print(f"An error occurred while fetching messages: {e}")
            return None

    def register(self):
        """Register a new Mega account."""
        self.email = self.generate_email()
        if not self.email:
            print("Failed to generate email. Exiting.")
            return False

        print(f"Registering account for {self.email}")

        try:
            if self.use_megareg:
                registration =subprocess.run(
                    [
                        "megareg",
                        "--scripted",
                        "--register",
                        "--email", self.email,
                        "--name", self.name,
                        "--password", self.password,
                    ],
                    check=True,
                )
            elif self.use_megatools:
                registration = subprocess.run(
                    [
                        "megatools",
                        "reg",
                        "--scripted",
                        "--register",
                        "--email", self.email,
                        "--name", self.name,
                        "--password", self.password,
                    ],
                    check=True,
                )
            self.verify_command = registration.stdout
        except subprocess.CalledProcessError as e:
            print(f"Failed to register account for {self.email}: {e}")
            return False

        print(f"> Registered account for {self.email}. Waiting for verification.")
        return True

    def verify(self):
        """Handle verification by checking email and confirming registration."""
        print(f"> Waiting for verification email for {self.email}")
        confirm_message = None
        for i in range(5):
            confirm_message = self.get_mail()
            if confirm_message:
                break
            print(f"> Waiting for verification email... ({i+1} of 5)")
            time.sleep(5)

        if not confirm_message:
            print(f"Failed to verify account for {self.email}. No verification email received.")
            return False

        links = find_url(confirm_message)  # Extract the URL from the email
        if not links:
            print(f"No verification link found in email for {self.email}.")
            return False

        print(f"> Verification link found for {self.email}. Completing registration.")

        # Replace @LINK@ with the actual verification link
        self.verify_command = self.verify_command.replace("@LINK@", links[0])

        try:
            subprocess.run(self.verify_command, shell=True, check=True, stdout=subprocess.PIPE)
            print(f"Account successfully verified for {self.email}!")
            print(f"Email: {self.email}, Password: {self.password}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to verify account for {self.email}: {e}")
            return False

def new_account():
    password = args.password or get_random_string(random.randint(8, 14))
    acc = MegaAccount(fake.name(), password)
    if acc.register() and acc.verify():
        print(f"Email: {acc.email}, Password: {acc.password}")
        with open("accounts.csv", "a", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow([acc.email, acc.password, "-", "-", "-", "-"])

if __name__ == "__main__":
    # Ensure the CSV file exists with the correct headers
    if not os.path.exists("accounts.csv"):
        with open("accounts.csv", "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Email", "MEGA Password", "Usage", "Mail.tm Password", "Mail.tm ID", "Purpose"])

    # Run account creation with or without threading
    if args.threads:
        print(f"Generating {args.number} accounts using {args.threads} threads.")
        threads = []
        for _ in range(args.number):
            t = threading.Thread(target=new_account)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
    else:
        print(f"Generating {args.number} accounts.")
        for _ in range(args.number):
            new_account()
