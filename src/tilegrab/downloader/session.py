from typing import Dict, Optional
import requests
from requests.adapters import HTTPAdapter, Retry

from .config import DownloadConfig


def create_session(
        config: DownloadConfig, 
        headers:Optional[Dict] = None) -> requests.Session:
    
    session = requests.Session()

    retries = Retry(
        total=config.max_retries,
        connect=config.max_retries,
        read=config.max_retries,
        backoff_factor=config.backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(("GET", "HEAD")),
        raise_on_status=False,
        redirect=False,
    )

    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=20,
        pool_maxsize=20,
    )

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "referer": "",
        "accept": "*/*",
        "user-agent": "Mozilla/5.0 QGIS/34202/Windows 11 Version 2009",
        "connection": "Keep-Alive",
        "accept-encoding": "gzip, deflate",
        "accept-language": "en-US,*",
    })

    if headers:
        session.headers.update(headers)

    return session