from typing import Any, Union, Annotated
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, HttpUrl, AfterValidator, EmailStr


app = FastAPI()

class BaseUser(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserIn(BaseUser):
    password: str


class BaseUserLogin(BaseModel):
    username: str | None = None
    email: str | None = None

class UserLoginRequest(BaseUserLogin):
    password: str

class UserLoginResponse(BaseUserLogin):
    token: str

userList = [
    {"username": "rahmat", "email": "rahmat@mail.com", "full_name": "Rahmat Hidayat", "password": "123"},
    {"username": "alice", "email": "alice@example.com", "full_name": "Alice Wonderland", "password": "password123"},
    {"username": "bob", "email": "bob@example.com", "full_name": "Bob Builder", "password": "supersecret"},
    {"username": "strinsg", "email": "bob@example.com", "full_name": "Bob Builder", "password": "string"}
]

@app.get("/")
async def read_root():
    return "Hello World"

@app.post("/user/", response_model=BaseUser)
async def create_user(user: UserIn) -> Any:
    if user.full_name is None:
        raise HTTPException(status_code=400, detail="Enter a full_name")

    for db_user in userList:
        if db_user["username"] == user.username:
            raise HTTPException(status_code=400, detail=f"Username '{user.username}' is already taken.")
        if db_user["email"] == user.email:
            raise HTTPException(status_code=400, detail=f"Email '{user.email}' is already registered.")
    
    user_dict = user.model_dump()
    userList.append(user_dict)
    print(userList)
    return user_dict

@app.post("/login/", response_model=UserLoginResponse)
async def login_user(user_request: UserLoginRequest) -> Any:
    
    if user_request.username and user_request.password == None:
        raise HTTPException(status_code=404, detail="Enter username or email")
    print(user_request)
    found_user = None

    for db_user in userList:
        if user_request.username and db_user.get("username") == user_request.username:
            found_user = db_user
            break
        if user_request.email and db_user.get("email") == user_request.email:
            found_user = db_user
            break

    print(found_user)
    if not found_user or found_user.get("password") != user_request.password:
        raise HTTPException(401, detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    
    response_data = {
        "username": found_user.get("username"),
        "email": found_user.get("email"),
        "token": "fake-jwt-token-for-demonstration"
    }
    
    return response_data