recd = [{
    "sender":{
        "id":1
    }
},{
    "sender":{
        "id":2
    }
},{
    "sender":{"id":1}
}]
s = set()
for r in recd:
    s.add(r['sender'])

z=1