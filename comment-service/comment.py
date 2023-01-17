#!/usr/bin/env python3

from fastapi import Path, Body
from pydantic import BaseModel, Field 
from typing import List
from beanie import Document, init_beanie


class Co:
    STR = "comment"
    MAX_LENGTH = 140

class D_name:
    STR = "The display name of the photographer"
    MAX_LENGTH = 16
    PATH_PARAM = Path(..., title = STR, max_length = MAX_LENGTH)

class Photo_id:
    STR = "Photo id"
    MAX_LENGTH = 32
    PATH_PARAM = Path(..., title = STR, max_length = MAX_LENGTH)

class Reviewer:
    STR = "The display name of the reviewer"
    MAX_LENGTH = 16
    PATH_PARAM = Path(..., title = STR, max_length = MAX_LENGTH)

class CommentDesc(BaseModel):
    comment: str = Field (None, title = Co.STR, max_length = Co.MAX_LENGTH)
    display_name: str = Field (None, title = D_name.STR, max_length = D_name.MAX_LENGTH)
    photo_id: str = Field (None, title = Photo_id.STR, max_length = Photo_id.MAX_LENGTH)
    reviewer: str = Field (None, title = Reviewer.STR, max_length = Reviewer.MAX_LENGTH)

class Comment(Document, CommentDesc):
    pass

COMMENT_EXAMPLE = {
    "comment": "nice",
    "display_name": "rdoisneau",
    "photo_id": "0",
    "reviewer": "rdoisneau",
    }

COMMENT_BODY = Body(..., example = COMMENT_EXAMPLE)



