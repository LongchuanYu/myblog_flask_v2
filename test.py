from hashlib import md5
email="test@qq.com"
print(email.lower().encode('utf-8'))
print(md5(email.lower().encode('utf-8')))
ret = md5(email.lower().encode('utf-8')).hexdigest()
print(ret)