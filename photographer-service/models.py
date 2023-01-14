#!/usr/bin/env python3

from fastapi import Path, Body
from pydantic import BaseModel, Field 
from typing import List
from beanie import Document, init_beanie

# Field ，Body可用于提供有关字段和验证的额外信息，如设置必填项和可选，设置最大值和最小值，字符串长度等限制, 示例
# Pydantic是一个用于数据建模/解析的Python库，具有高效的错误处理和自定义验证机制。 截至目前，Pydantic主要用于FastAPI框架中，用于解析请求和响应，因为Pydantic内置了对JSON编码和解码的支持


class Dname:
    STR = "The display name of the photographer"
    MAX_LENGTH = 16
    PATH_PARAM = Path(..., title = STR, max_length = MAX_LENGTH)

class Fname:
    STR = "The first name of the photographer"
    MAX_LENGTH = 32

class Lname:
    STR = "The last name of the photographer"
    MAX_LENGTH = 32

class Interests:
    STR = "The interests of the photographer"

class PhotographerDesc(BaseModel):
    display_name: str = Field (None, title = Dname.STR, max_length = Dname.MAX_LENGTH)
    first_name: str = Field (None, title = Fname.STR, max_length = Dname.MAX_LENGTH)
    last_name: str = Field (None, title = Lname.STR, max_length = Lname.MAX_LENGTH)
    interests: List[str] = Field (None, title = Interests.STR)

class Photographer(Document, PhotographerDesc):
    pass

PHOTOGRAPHER_EXAMPLE = {
    "display_name": "rdoisneau",
    "first_name": "robert",
    "last_name": "doisneau",
    "interests": ["street", "portrait"],
    }

PHOTOGRAPHER_BODY = Body(..., example = PHOTOGRAPHER_EXAMPLE)

class PhotographerDigest(BaseModel):
    display_name: str #这是typing的语法：在声明变量时，变量的后面可以加一个冒号，后面再写上变量的类型，如 int、list 等等。
    link: str

class Photographers(BaseModel):
    items: List[PhotographerDigest] # typing 模块提供了非常 “强 “的类型支持
    has_more: bool


