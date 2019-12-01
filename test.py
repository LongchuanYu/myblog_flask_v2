from datetime import datetime,timedelta
import base64,os
# now = datetime.utcnow()
# print(now + timedelta(seconds=3600))
# print(now + timedelta(seconds=60))
# print(None>now+timedelta(seconds=60))
# import os 

print(base64.b64encode(os.urandom(24)))

print( base64.b64encode(os.urandom(24)).decode('utf-8'))


# now + timedelta(seconds=expires_in) 》 now + timedelta(seconds=60)