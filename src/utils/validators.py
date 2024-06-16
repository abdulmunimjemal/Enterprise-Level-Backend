import os
import re
from typing import IO
from urllib.parse import urlparse
import filetype
from fastapi import HTTPException, status

def is_valid_path_or_url(path_or_url):
    # Define a regex for local file path starting with "file://"
    file_url_regex = re.compile(r'^file://')
    
    # Check if it is a valid local file path
    if os.path.exists(path_or_url):
        return True
    
    # Check if it is a valid "file://" URL
    if file_url_regex.match(path_or_url):
        local_path = path_or_url[7:]
        if os.path.exists(local_path):
            return True

    # Check if it is a valid URL
    try:
        result = urlparse(path_or_url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

async def validate_uploaded_file(file: IO):
    # TODO: validate bytes
    pass
    # await validate_file_type_(file)
    # if file_type.mime not in accepted_file_types:
        # raise HTTPException(status_code=415, detail="Unsupported file type")

async def validate_file_type_(file: IO):
    accepted_file_types = ["application/zip", "zip"]
    file_info = filetype.guess(file)
    if file_info is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unable to determine file type"
        )
    detected_content_type = file_info.extension.lower()

    if (
        file.content_type not in accepted_file_types
        or detected_content_type not in accepted_file_types
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type"
        )
