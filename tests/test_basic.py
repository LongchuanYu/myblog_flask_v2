import unittest
from flask import current_app
from app import create_app,db
from tests import TestConfig
from tests.common_test import CommonMethods
class BasicsTestCase(CommonMethods):
    def test_app_exists(self):
        self.assertFalse(current_app is None)
    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])