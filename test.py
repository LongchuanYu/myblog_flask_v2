from flask import jsonify
class Test:
    def say(self,msg):
        print(msg)
    def seta(self):
        setattr(self,"hello","123")
    def geta(self):
        print(self.hello)
t=Test()
t.seta()
t.geta()