from app import create_app,db
from app.models import User
from config import Config
app = create_app(Config)

@app.cli.command()
def test():
    'run the unit tests..'
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


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
if __name__=='__main__':
    app.run(debug=True)