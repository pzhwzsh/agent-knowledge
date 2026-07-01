import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException, status


def validate_public_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only public http(s) URLs are allowed")
    hostname = parsed.hostname.strip().lower()
    if hostname in {"localhost", "localhost.localdomain"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Localhost URLs are not allowed")
    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL host cannot be resolved") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Private or reserved network URLs are not allowed")
    return url
