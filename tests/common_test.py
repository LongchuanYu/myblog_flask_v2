import unittest
from flask import current_app
from app import create_app,db
from tests import TestConfig

class CommonMethods(unittest.TestCase):
    def setUp(self):
        # print('setup!!!!!')
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    def tearDown(self):
        # print('teardown!!!!')
        db.session.remove()
        db.drop_all()
        self.app_context.pop()