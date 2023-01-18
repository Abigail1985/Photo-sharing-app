import pytest
import json
from starlette.testclient import TestClient
from bson import json_util
from comment_service import app
from httpx import AsyncClient, Request

import unittest.mock

data1 = {
    "comment": "nice",
    "display_name": "rdoisneau",
    "photo_id": "0",
    "reviewer": "alice",
}

data2 = {
    "comment": "not good",
    "display_name": "rdoisneau",
    "photo_id": "0",
    "reviewer": "bob",
}

headers_content = {'Content-Type': 'application/json'}
headers_accept  = {'Accept': 'application/json'}


@pytest.mark.asyncio # 一个测试异步代码的插件
@unittest.mock.patch('comment_service.requests.get')
@pytest.mark.usefixtures("clearComments")
@pytest.mark.usefixtures("initDB")
async def test_post_once(requests_get):
    # here, we force the Photographer service to return 200 OK.
    requests_get.return_value.status_code = 200
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post('/comments', headers=headers_content,
            data=json.dumps(data1),)
        assert response.status_code == 201


@pytest.mark.asyncio # 一个测试异步代码的插件
@unittest.mock.patch('comment_service.requests.get')
@pytest.mark.usefixtures("clearComments")
@pytest.mark.usefixtures("initDB")
async def test_delete_once(requests_get):
    # here, we force the Photographer service to return 200 OK.
    requests_get.return_value.status_code = 200
    async with AsyncClient(app=app, base_url="http://test") as client:
        response1 = await client.post('/comments', headers=headers_content,
            data=json.dumps(data1),)
        assert response1.status_code == 201

        response2 = await client.delete('/photographer/rdoisneau/0/alice', headers=headers_content,)
        assert response2.status_code == 200


