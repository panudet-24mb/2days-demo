from sqlite3 import connect
from fastapi import FastAPI, Body, Depends ,HTTPException, Security
import pymongo 
import pydantic 
import datetime
import jwt
from bson import json_util, ObjectId
import json
from typing import Optional
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
client = pymongo.MongoClient("mongodb://admin:admin_password@mongo:27017/")

def get_db_connection() -> pymongo.database.Database:
    db = client["2day"]
    return db

app = FastAPI()

class User(pydantic.BaseModel):
    username: str
    password: str
    user_code : str
    firstname:str
    lastname: str
    citizen_id : str
    create_at : Optional[str] = None
    delete_at : Optional[str] = None
    update_at : Optional[str] = None
    class Config:
        schema_extra = {
            "example": {
                "username": "admin",
                "password": "admin",
                "user_code": "admin",
                "firstname" : "Panudet",
                "lastname" : "Panumas",
                "citizen_id" : "100000001" , 
            
            
            }
        }
        
        
    

@app.get("/api/demo/")
async def root():
    return {"message": "Hello World"}


@app.post("/api/demo/user")
async def create_user(user : User):
    connection = get_db_connection()
    dt = datetime.datetime.now()
    #########################################################################
    #ให้เช็คเงื่อนว่า ถ้าสร้าง user ห้าม User_code , Username , CitizenID  ซ้ำกันในระบบ# 
    #########################################################################
    user.create_at = dt
    connection.user.insert_one(
        user.dict()
    )
    return {"message": "User created"}

@app.get(
    "/api/demo/user/{username}",
)
async def get_user(username: str):
    #########################################################################
    #GET ห้ามโชว์ Password ในระบบ 
    #########################################################################
    connection = get_db_connection()
    user = connection.user.find_one({"username": username})
    if user:
        user =  json_util.dumps(user , indent = 4)
        user = json.loads(
            user
        )
        return { "code": 200 , "data" : user }
    else:
        return { "code": 1000 , "message" : "No username found","data" : {}}


@app.post(
    "/api/demo/login",
)   
async def login(
    username: str,
    password: str,
):
    connection = get_db_connection()
    user = connection.user.find_one({"username": username})
    if user is None:
        return {"code": 100 , "message": "User not found"}
    if user["password"] != password:
        return {"code": 101 ,"message": "Password is incorrect"}
    user = json.loads(json_util.dumps(user))
    user_id = user["_id"]
    encoded_jwt = jwt.encode({"user_id": user_id["$oid"]}, "secret", algorithm="HS256")
    return {"code": 200 ,"message": "Login success" , "token" : encoded_jwt}

def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, "secret", algorithms=["HS256"])
        return decoded_token 
    except:
        return {}
security = HTTPBearer()


async def find_one_user(object_id):
    connection = get_db_connection()
    user = connection.user.find_one({"_id": ObjectId(object_id)})
    return user
    

    
#เขียน เงื่อนไข หากทำการ checkin แล้วจะไม่สามารถ Checkin ได้ซ้ำ 
#parameter มีสองประเภทก็คือ checkin , checkout 
#ต้องเช็คด้วยว่า checkin ได้ครั้งเดียว 
#ต้องเช็คว่ามีการ checkin ก่อนหน้านี้หรือไม่
#ต้องเช็คว่า checkout ได้ครั้งเดียว 
#ต้องเช็คว่ามีการ checkout ก่อนหน้านี้หรือไม่

@app.post(
    "/api/demo/create_time_log")
async def create_time_log(
     log_type: str,
   credentials: HTTPAuthorizationCredentials = Security(security), 
    ):
    user_token =credentials.credentials
    user_info = decodeJWT(user_token)
   
    user = await find_one_user(user_info["user_id"])
    if user is None:
        return {"message": "User not found"}

    connection = get_db_connection()
    connection.time_log.insert_one({
        "time_log" : datetime.datetime.now(),
        "log_type" : log_type ,
        "user_id" : user["_id"]}
    )
    return {"message": "Time log created"}



#เขียนเพื่อให้พี่เบล์ดูว่า ตอนนี้ user checkin , checkout ข้อมูลการเข้างาน ของวันนี้
@app.get(
    "/api/demo/check/time_log")
async def check_user_time_log(
      credentials: HTTPAuthorizationCredentials = Security(security), 
    ):
    user_token =credentials.credentials
    user_info = decodeJWT(user_token)
    user_id = (user_info["user_id"])
    connection = get_db_connection()
    dateNow = datetime.datetime.now()
    #find today time log 
    data = connection.time_log.find(
        {"user_id": ObjectId(user_id)
         ,
         "time_log": {"$gte": dateNow.replace(hour=0, minute=0, second=0, microsecond=0),
         }
        }
    )
    
    if data is None:
        return {"message": "user are not checkin , checkout"  , "data" : [] , "code" : 201}
    

    data = json_util.dumps(data , indent = 4)
    data = json.loads(data)
    
    user_state = None
    for index in range(len(data)):     
        if data[index]["log_type"] == "check-in":
            user_state = "check-in" 
        if data[index]["log_type"] == "check-out":
            user_state = "check-out" 
            
    if user_state == "check-in":
        return {"message": "user are checkin" , "data" : data , "code" : 202}
    if user_state == "check-out":
        return {"message": "user are checkout" , "data" : data , "code" : 203}
    
        
   

