from base64 import b64encode
from datetime import datetime,timedelta
import json,re,unittest
from app import create_app,db
from app.models import User,Post
from tests import TestConfig
from tests.common_test import CommonMethods

class APITestCase(CommonMethods):
    def test_404(self):
        response = self.client.get('/api/wrong/urlll')
        self.assertEqual(response.status_code,404)
        