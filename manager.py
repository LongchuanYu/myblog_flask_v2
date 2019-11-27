from app import create_app,db
from app.models import User
app = create_app()


#注册一个shell上下文处理器的函数
#在flask shell中可以执行该函数
#比如>>>db 
#比如>>>User
@app.shell_context_processor
def make_shell_context():
    return {
        'db':db,
        'User':User
    }