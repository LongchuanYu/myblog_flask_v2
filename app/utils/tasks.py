import time,sys
from rq import get_current_job
from app import create_app,db
from app.models import User,Message,Task
from app.utils.email import send_email
from config import Config

app = create_app(Config)
app.app_context().push()

def test_rq(num):
    print('Starting task')
    for i in range(num):
        print(i)
        time.sleep(1)
    print('Task completed')
    return 'Done'


def send_messages(*args,**kwargs):
    try:
        sender = User.query.get(kwargs.get('user_id'))
        recipients = User.query.filter(User.id != kwargs.get('user_id'))
        for user in recipients:
            message = Message()
            message.body = kwargs.get('body')
            # 发送方是自己
            message.sender = sender
            # 接收方是所有其他用户
            message.recipient = user
            db.session.add(message)
            db.session.commit()
            text_body='''
            你好，
            这是liyang的博客管理团队发出的群邮件
            '''
            html_body = '''
            <p>你好 {0},</p>
            <p>{1}</p>
            <p> ----来自于Admin的邮件</p>
            '''.format(user.username,message.body)
            send_email('[myBlog] 温馨提醒',
                       sender=app.config['MAIL_SENDER'],
                       recipients=[user.email],
                       text_body=text_body,
                       html_body=html_body,
                       sync=True)
        job = get_current_job()  # 当前后台任务
        task = Task.query.get(job.get_id())  # 通过任务ID查出对应的Task对象
        task.complete = True
        db.session.commit()

    except Exception:
        app.logger.error('群发失败：',exc_info=sys.exc_info())
        