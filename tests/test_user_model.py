# -*- coding: utf-8
import unittest
from app.models import User
from tests import TestConfig
from tests.common_test import CommonMethods

class UserModelTestCase(CommonMethods):
    def test_password_hashing(self):
        u = User(name='john')
        u.set_password('pass1234')
        self.assertTrue(u.check_password('pass1234'))
        self.assertFalse(u.check_password('fasfdsa1'))
    def test_avatar(self):
        u = User(username='john',email='test@qq.com')
        self.assertEqual(u.avatar(128),'https://www.gravatar.com/avatar/bf58432148b643a8b4c41c3901b81d1b?d=identicon&s=128')