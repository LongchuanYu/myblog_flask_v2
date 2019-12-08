from datetime import datetime,timedelta,date
import base64,os
import jwt

mytime = date(2019,12,12)
print(datetime.utcnow())
print(datetime.utcnow().microsecond())
print(mytime.isoformat())