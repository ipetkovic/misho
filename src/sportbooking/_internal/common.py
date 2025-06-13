HOST = 'https://sportbooking.info'

_STANDARD_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Sec-Fetch-Site':  'same-origin',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Sec-Fetch-Mode': 'navigate',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15',
    'Priority': 'u=0, i',
    'Sec-Fetch-Dest': 'document',
    'Origin': HOST,
}


def get_standard_headers() -> dict:
    """
    Returns the standard headers used for requests to the Sportbooking API.
    """
    return _STANDARD_HEADERS.copy()
