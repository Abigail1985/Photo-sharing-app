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
from comment import Co, D_name, Photo_id, Reviewer, CommentDesc,Comment,COMMENT_BODY

from beanie import Document, init_beanie
import asyncio, motor

REQUEST_TIMEOUT = 5

# photographer_service_host = 'photographer-service:80'
# tags_service_host = 'tags-service:50051'
# mongo_service_host = 'mongo-service'

# tags_service = tags_service_host
# mongo_service = mongo_service_host


class Settings(BaseSettings):
    mongo_host: str = "localhost"
    mongo_port: str = "27017"
    mongo_user: str = ""
    mongo_password: str = ""
    database_name: str = "comments"
    auth_database_name: str = "photographers"

    photo_host: str = "photo-service"
    photo_port: str = "80"

    photographer_host: str = "photographer-service"
    photographer_port: str = "80"

settings = Settings()

photographer_service = 'http://' + settings.photographer_host + ':' + settings.photographer_port + '/'
photo_service = 'http://' + settings.photo_host + ':' + settings.photo_port + '/'

app = FastAPI(title = "Comment Service")

# FastAPI logging
# gunicorn_logger = logging.getLogger('gunicorn.error')
# logger.handlers = gunicorn_logger.handlers

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


@app.on_event("startup")
async def startup_event():
    conn = f"mongodb://"
    if settings.mongo_user:
        conn += f"{settings.mongo_user}:{settings.mongo_password}@"
    conn += f"{settings.mongo_host}:{settings.mongo_port}"
    conn += f"/{settings.database_name}?authSource={settings.auth_database_name}"
    client = motor.motor_asyncio.AsyncIOMotorClient(conn) #motor连接数据库
    await init_beanie(database=client[settings.database_name], document_models=[Comment])

    # tags_client.connect(settings.tags_host + ":" + settings.tags_port)

@app.post("/comments", status_code = 201) # `201`，「已创建」。它通常在数据库中创建了一条新记录后使用。
async def create_comment(response: Response, comment: CommentDesc = COMMENT_BODY):

    try:
        photographer = requests.get(photographer_service + 'photographer/' + comment.display_name,
                                    timeout=REQUEST_TIMEOUT)
        reviewer = requests.get(photographer_service + 'photographer/' + comment.reviewer,
                                    timeout=REQUEST_TIMEOUT)
        photo = requests.get(photo_service + 'photo/' + comment.display_name + '/' + comment.photo_id,
                                    timeout=REQUEST_TIMEOUT)  
                                    
        if photographer.status_code == requests.codes.unavailable:
            raise HTTPException(status_code = 503, detail = "Mongo unavailable")
        if photographer.status_code == requests.codes.not_found:
            raise HTTPException(status_code = 404, detail = "Photographer Not Found")

        if reviewer.status_code == requests.codes.unavailable:
            raise HTTPException(status_code = 503, detail = "Mongo unavailable")
        if reviewer.status_code == requests.codes.not_found:
            raise HTTPException(status_code = 404, detail = "Reviewer Not Found")
                    
        if photo.status_code == requests.codes.unavailable:
            raise HTTPException(status_code = 503, detail = "Mongo unavailable")
        if photo.status_code == requests.codes.not_found:
            raise HTTPException(status_code = 404, detail = "Photo Not Found")

        if photographer.status_code == requests.codes.ok & reviewer.status_code == requests.codes.ok & photo.status_code == requests.codes.ok:
            await Comment(**dict(comment)).insert() #Beanie的插入
            response.headers["Location"] = "/comments" #插入后写入信息到response里

    except (pymongo.errors.AutoReconnect,
            pymongo.errors.ServerSelectionTimeoutError,
            pymongo.errors.NetworkTimeout) as e:
        raise HTTPException(status_code = 503, detail = "Mongo unavailable")

@app.get("/comments/{display_name}/{photo_id}", status_code = 200)    
async def get_comment_by_photo(display_name: str = D_name.PATH_PARAM, photo_id: str = Photo_id.PATH_PARAM):

    try:
        comments = await Comment.find(Comment.display_name == display_name and Comment.photo_id == photo_id).to_list()   
        if comments is not None:
            pure_comments=list ()
            for comment in comments:
                pure_comments.append(comment.comment)
            return pure_comments
        else:
            raise HTTPException(status_code = 404, detail = "Comment does not exist") # 404`，用于「未找到」响应。
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable")
   
@app.get("/comments/{reviewer}", status_code = 200)    
async def get_comment_by_reviewer(reviewer: str = Reviewer.PATH_PARAM):

    try:
        comments = await Comment.find(Comment.reviewer == reviewer).to_list() 
        if comments is not None:
            pure_comments=list ()
            for comment in comments:
                pure_comments.append(comment.comment)
            return pure_comments
        else:
            raise HTTPException(status_code = 404, detail = "Comment does not exist") # 404`，用于「未找到」响应。
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable")

@app.get("/comments/{display_name}", status_code = 200)    
async def get_comment_by_photographer(display_name: str = D_name.PATH_PARAM):

    try:
        comment = await Comment.find(Comment.display_name == display_name).to_list()   
        if comments is not None:
            pure_comments=list ()
            for comment in comments:
                pure_comments.append(comment.comment)
            return pure_comments
        else:
            raise HTTPException(status_code = 404, detail = "Comment does not exist") # 404`，用于「未找到」响应。
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable")

@app.delete("/photographer/{display_name}/{photo_id}/{reviewer}", status_code = 200)
async def delete_photographer(display_name: str = D_name.PATH_PARAM, photo_id: str = Photo_id.PATH_PARAM, reviewer: str = Reviewer.PATH_PARAM):
    try:
        comment = await Comment.find_one(Comment.display_name == display_name and Comment.reviewer == reviewer and Comment.photo_id == photo_id)    
        if comment:
            await comment.delete()
            return {"message": "Comment deleted successfully"}
        else:
            raise HTTPException(status_code = 404, detail = "Comment does not exist") # 404`，用于「未找到」响应。
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=503, detail="Mongo unavailable")    


if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port=80, log_level="info",reload=True)
    #logger.setLevel(logging.DEBUG)
else:
    # logger.setLevel(gunicorn_logger.level)
    pass
