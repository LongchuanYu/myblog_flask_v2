from datetime import datetime,timedelta,date
import base64,os
import jwt

class Test:
    name="ly"
    age=11
    def say(self):
        print(self.name)
        print(self.age)
    def __repr__(self):
        return "wawawa"

print(Test())