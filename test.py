def hello():
    print(1/0)
try:
    hello()
except Exception as e:
    print(isinstance(str(e),str))
    print(e)