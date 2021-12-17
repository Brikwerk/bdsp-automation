import json
from os import path

from pushover import init, Client


def send_message(msg):
    if not path.isfile('notify-keys.json'):
        print("notify-keys.json not found")
        print("An empty JSON file has been created for you to fill out.")
        
        with open('notify-keys.json', 'w') as f:
            json.dump({
                "user-key": "USER-KEY-GOES-HERE",
                "token": "TOKEN-GOES-HERE"
            }, f, indent=4)

        return

    # Load the keys for pushover
    with open("notify-keys.json", "r") as f:
        keys = json.load(f)
    
    # Initialize the pushover client
    init(keys['token'])
    client = Client(keys['user-key'])

    # Send the message
    client.send_message(msg)


if __name__ == "__main__":
    send_message("Test Message")
