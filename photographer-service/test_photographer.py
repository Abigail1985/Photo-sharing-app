import pytest
# from starlette.testclient import TestClient
import json
from bson import json_util
import logging
# from fastapi.testclient import TestClient
from photographer_service import app
from beanie import Document, init_beanie
from httpx import AsyncClient, Request
#logging.basicConfig(level=logging.DEBUG)

data1 = {'display_name': 'rdoisneau',
         'first_name': 'Robert',
         'last_name': 'Doisneau',
         'interests': ['street']
        }

data2 = {'display_name': 'hsentucq',
         'first_name': 'Hervé',
         'last_name': 'Sentucq',
         'interests': ['landscape']
        }

headers_content = {'Content-Type': 'application/json'}
headers_accept  = {'Accept': 'application/json'}


@pytest.mark.asyncio # 一个测试异步代码的插件
@pytest.mark.usefixtures("clearPhotographers")
@pytest.mark.usefixtures("initDB")
async def test_post_once():
    async with AsyncClient(app=app, base_url="http://test") as ac: #打开client，以发出异步请求
        response = await ac.post('/photographers',
                               headers=headers_content,
                                 content=json.dumps(data1))
        assert response.headers['Location']
        assert response.status_code == 201

@pytest.mark.asyncio
@pytest.mark.usefixtures("clearPhotographers")
@pytest.mark.usefixtures("initDB")
async def test_post_twice():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response1 = await ac.post('/photographers',
                                  headers=headers_content,
                                  content=json.dumps(data1))
        assert response1.status_code == 201 #判断是否相等，返回false或true

        response2 = await ac.post('/photographers',
                                  headers=headers_content,
                                  content=json.dumps(data1))
        assert response2.status_code == 409


@pytest.mark.asyncio
@pytest.mark.usefixtures("clearPhotographers")
@pytest.mark.usefixtures("initDB")
async def test_has_more_false_photographers():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post('/photographers',
                           headers=headers_content,
                           content=json.dumps(data1)) #json.dumps()----将Python的字典数据转换成json字符,数据的最外面都添加一层""变为字符串，这也是数据的序列化步骤
        assert response.headers['Location']
        assert response.status_code == 201

        response2 = await ac.get('/photographers?offset=0&limit=10')
        assert response2.status_code == 200
        assert response2.json()['has_more'] == False

@pytest.mark.asyncio        
@pytest.mark.usefixtures("clearPhotographers")
@pytest.mark.usefixtures("initDB")
async def test_has_more_true_photographers():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response1 = await ac.post('/photographers',
                                  headers=headers_content,
                                  content=json.dumps(data1))

        assert response1.headers['Location']
        assert response1.status_code == 201

        response2 = await ac.post('/photographers',
                                  headers=headers_content,
                                  content=json.dumps(data2))
        assert response2.headers['Location']
        assert response2.status_code == 201

        response3 = await ac.get('/photographers?offset=0&limit=1')
        assert response3.status_code == 200
        assert response3.json()['has_more'] == True
