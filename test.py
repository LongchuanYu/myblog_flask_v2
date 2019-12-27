from datetime import datetime,timedelta,date
import base64,os
import jwt

class Test:
    name="ly"
    age=11
    @property
    def say(self):
        return self.age+100
    def __repr__(self):
        return "wawawa"
test=Test()
print(test.say)