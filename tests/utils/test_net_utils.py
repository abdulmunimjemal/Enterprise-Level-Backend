import pytest
import os
import boto3
from utils import net_utils

@pytest.mark.anyio
async def test_can_download_file_successfully_with_http():
    await net_utils.download_file("https://www.google.com", "/tmp/test.html")
    assert os.path.exists("/tmp/test.html")
    os.remove("/tmp/test.html")

@pytest.mark.anyio
async def test_errors_when_downloading_something_that_does_not_exist():
    with pytest.raises(Exception):
        await net_utils.download_file("https://sdfskdfjskdfskdjf.com/not_a_real_path", "/tmp/test.html")

@pytest.mark.anyio
async def test_can_download_something_from_our_s3_bucket():
    await net_utils.download_s3_file("hello.txt", "/tmp/test.txt", "moodme-test-bucket")
    assert os.path.exists("/tmp/test.txt")
    os.remove("/tmp/test.txt") 

@pytest.mark.asyncio
async def test_can_upload_file_to_our_s3_bucket():
    with open("/tmp/test.txt", "w") as f:
        f.write("Hello, world!")
    await net_utils.upload_file("/tmp/test.txt", "moodme-test-bucket")
    await net_utils.download_s3_file("test.txt", "/tmp/test.txt", "moodme-test-bucket")
    assert os.path.exists("/tmp/test.txt")
    os.remove("/tmp/test.txt")

