import pytest
from src.controllers.storage.storage_controller import StorageController


@pytest.mark.anyio
async def test_list_buckets():
    storage_controller = StorageController()
    buckets = await storage_controller.list_buckets()
    assert len(buckets) > 0
    print(buckets)
