import re

def test_link_regex(link):
    private_match = re.search(r'(?:t\.me/|telegram\.me/)(?:\+|joinchat/)([\w-]+)', link)
    if private_match:
        return private_match.group(1)
    return None

test_links = [
    "https://t.me/+Q1hgZoM529Y5MjVl",
    "https://t.me/joinchat/ABCDE12345",
    "http://telegram.me/+XYZ",
    "https://t.me/publicgroup",
    "just_a_username"
]

for link in test_links:
    result = test_link_regex(link)
    print(f"Link: {link} -> Hash: {result}")
