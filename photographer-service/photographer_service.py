#!/usr/bin/env python3

import uvicorn

from fastapi import Depends, FastAPI, HTTPException
from starlette.responses import Response
from fastapi.logger import logger

from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel,BaseSettings
from typing import List
import pymongo
import requests
from models import Dname, Photographer, PhotographerDesc, PHOTOGRAPHER_BODY, Photographers, PhotographerDigest

from beanie import Document, init_beanie
import asyncio, motor

import re #正则检查

class Settings(BaseSettings):
    mongo_host: str = "localhost"
    mongo_port: str = "27017"
    mongo_user: str = ""
    mongo_password: str = ""
    database_name: str = "photographers"
    auth_database_name: str = "photographers"

settings = Settings()

app = FastAPI(title = "Photographer Service")

# CORS中间件是为了解决跨域资源共享的问题
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastAPI logging
#gunicorn_logger = logging.getLogger('gunicorn.error')
#logger.handlers = gunicorn_logger.handlers

@app.on_event("startup") #定义在应用程序启动之前或应用程序关闭时需要执行的事件处理程序（函数）
async def startup_event():
    conn = f"mongodb://"
    if settings.mongo_user:
        conn += f"{settings.mongo_user}:{settings.mongo_password}@"
    conn += f"{settings.mongo_host}:{settings.mongo_port}"
    conn += f"/{settings.database_name}?authSource={settings.auth_database_name}"
    client = motor.motor_asyncio.AsyncIOMotorClient(conn) #motor连接数据库
    await init_beanie(database=client[settings.database_name], document_models=[Photographer])

    # 在上面的代码块中，我们导入了init_beanie方法，它负责初始化由motor.motor_asyncio驱动的数据库引擎。init_beanie 方法需要两个参数。
    # database - 要使用的数据库的名称。
    # document_models - 一个定义的文档模型的列表


@app.get("/photographers", response_model = Photographers, status_code = 200)    #200是默认状态代码，它表示一切「正常」
async def get_photographers(request: Request, offset: int = 0, limit: int = 10):
    list_of_digests = list()
    last_id = 0
    try:
        async for result in Photographer.find().sort("_id").skip(offset).limit(limit):
            digest = PhotographerDigest(display_name=result.display_name, link="/photographer/" + result.display_name)
            last_id = result.id
            list_of_digests.append(digest)
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable") #`500` 及以上状态码用于服务器端错误
    has_more = await Photographer.find(Photographer.id > last_id).to_list()
    return {'items': list_of_digests, 'has_more': True if len(has_more) else False}

@app.post("/photographers", status_code = 201) # `201`，「已创建」。它通常在数据库中创建了一条新记录后使用。
async def create_photographer(response: Response, photographer: PhotographerDesc = PHOTOGRAPHER_BODY):

    try:
        check = await Photographer.find_one(Photographer.display_name == photographer.display_name)
        if check is None:# 如果没在db中找到同名摄影师
            await Photographer(**dict(photographer)).insert() #Beanie的插入
            response.headers["Location"] = "/photographer/" + str(photographer.display_name) #插入后写入信息到response里
        else:
            raise HTTPException(status_code = 409, detail = "Conflict") #`400` 及以上状态码用于「客户端错误」响应，这里指重复创建同名摄影师
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable") #`500` 及以上状态码用于服务器端错误

@app.get("/photographer/{display_name}", response_model = PhotographerDesc, status_code = 200)    
async def get_photographer(display_name: str = Dname.PATH_PARAM):

    try:
        photographer = await Photographer.find_one(Photographer.display_name == display_name)    
        if photographer is not None:
            return photographer
        else:
            raise HTTPException(status_code = 404, detail = "Photographer does not exist") # 404`，用于「未找到」响应。
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable")


@app.put("/photographer/{display_name}", status_code = 200)
async def update_photographer(display_name: str = Dname.PATH_PARAM, # PATH_PARAM = Path(..., title = STR, max_length = MAX_LENGTH)
                        photographer: PhotographerDesc = PHOTOGRAPHER_BODY): # PHOTOGRAPHER_BODY = Body(..., example = PHOTOGRAPHER_EXAMPLE)
    try:
        found = await Photographer.find_one(Photographer.display_name == display_name)    
        if found is None:
            raise HTTPException(status_code = 503, detail = "Not Found")
        else:
            await found.set(dict(photographer))
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable")

@app.delete("/photographer/{display_name}", status_code = 200)
async def delete_photographer(display_name: str = Dname.PATH_PARAM):
    try:
        photographer = await Photographer.find_one(Photographer.display_name == display_name)    
        if photographer is not None:
            await photographer.delete()
            return {"message": "Record deleted successfully"}
        else:
            raise HTTPException(status_code = 404, detail = "Photographer does not exist") # 404`，用于「未找到」响应。
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable")    

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")
    #logger.setLevel(logging.DEBUG)
else:
    #logger.setLevel(gunicorn_logger.level)
    pass
