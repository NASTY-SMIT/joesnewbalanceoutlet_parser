import re


def extract_pid_from_url(url):
    """Extract PID from product URL like /pd/509/U509EV1-FTW-805505.html"""
    match = re.search(r'/pd/[^/]+/([^/.]+)\.html', url)
    return match.group(1) if match else None