from datetime import datetime,timedelta
import base64,os
import jwt

payload={
    "aud":'liyang',
    "exp":'2019/12/06'
}


ret = jwt.encode(payload,"hello",algorithm="HS256")
print(ret)