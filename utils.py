from hashlib import sha256


def get_id(url: str) -> str:
    return sha256(url.encode()).hexdigest()