import pytest
from app import create_app
@pytest.fixture
def app():return create_app({'TESTING':True,'WTF_CSRF_ENABLED':False,'SQLALCHEMY_DATABASE_URI':'sqlite:///:memory:'})
def login(c,email='medico@clinica.demo'):return c.post('/login',data={'email':email,'password':'demo123'},follow_redirects=True)
def test_login(client):assert 'Panel principal' in login(client).text
def test_health(client):assert client.get('/api/health').json['status']=='ok'
def test_reception_denied_history(client):login(client,'recepcion@clinica.demo');assert client.get('/patients/1/history').status_code==403
