import pytest
import mock
import twisted.internet
import twisted.test

from pappyproxy import http
from pappyproxy import mangle
from pappyproxy.proxy import ProxyClient, ProxyClientFactory, ProxyServer
from testutil import mock_deferred, func_deleted, func_ignored_deferred, func_ignored, no_tcp
from twisted.internet.protocol import ServerFactory
from twisted.test.iosim import FakeTransport
from twisted.internet import defer, reactor

####################
## Fixtures

@pytest.fixture
def unconnected_proxyserver(mocker):
    mocker.patch("twisted.test.iosim.FakeTransport.startTLS")
    mocker.patch("pappyproxy.proxy.load_certs_from_dir", new=mock_generate_cert)
    factory = ServerFactory()
    factory.protocol = ProxyServer
    protocol = factory.buildProtocol(('127.0.0.1', 0))
    protocol.makeConnection(FakeTransport(protocol, True))
    return protocol
    
@pytest.fixture
def proxyserver(mocker):
    mocker.patch("twisted.test.iosim.FakeTransport.startTLS")
    mocker.patch("pappyproxy.proxy.load_certs_from_dir", new=mock_generate_cert)
    factory = ServerFactory()
    factory.protocol = ProxyServer
    protocol = factory.buildProtocol(('127.0.0.1', 0))
    protocol.makeConnection(FakeTransport(protocol, True))
    protocol.lineReceived('CONNECT https://www.AAAA.BBBB:443 HTTP/1.1')
    protocol.lineReceived('')
    protocol.transport.getOutBuffer()
    return protocol
    
@pytest.fixture
def proxy_connection():
    @defer.inlineCallbacks
    def gen_connection(send_data):
        factory = ProxyClientFactory(http.Request(send_data))
        protocol = factory.buildProtocol(None)
        tr = FakeTransport(protocol, True)
        protocol.makeConnection(tr)
        sent = yield protocol.data_defer
        defer.returnValue((protocol, sent, factory.data_defer))
    return gen_connection

## Autorun fixtures
    
# @pytest.fixture(autouse=True)
# def no_mangle(mocker):
#     # Don't call anything in mangle.py
#     mocker.patch("mangle.mangle_request", notouch_mangle_req)
#     mocker.patch("mangle.mangle_response", notouch_mangle_rsp)
    
@pytest.fixture(autouse=True)
def ignore_save(mocker):
    mocker.patch("pappyproxy.http.Request.deep_save", func_ignored_deferred)

####################
## Mock functions

def mock_generate_cert(cert_dir):
    private_key = ('-----BEGIN PRIVATE KEY-----\n'
                   'MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDAoClrYUEB7lM0\n'
                   'zQaKkXZVG2d1Bu9hV8urpx0gNXMbyZ2m3xb+sKZju/FHPuWenA4KaN5gRUT+oLfv\n'
                   'tnF6Ia0jpRNWnX0Fyn/irdg1BWGJn7k7mJ2D0NXZQczn2+xxY05599NfGWqNKCYy\n'
                   'jhSwPsUK+sGJqi7aSDdlS97ZTjrQVTTFsC0+kSu4lS5fsWXxqrKLa6Ao8W7abVRO\n'
                   'JHazh/cxM4UKpgWU+E6yD4o4ZgHY+SMTVUh/IOM8DuOVyLEWtx4oLNiLMlpWT3qy\n'
                   '4IMpOF6VuU6JF2HGV13SoJfhsLXsPRbLVTAnZvJcZwtgDm6NfKapU8W8olkDV1Bf\n'
                   'YQEMSNX7AgMBAAECggEBAII0wUrAdrzjaIMsg9tu8FofKBPHGFDok9f4Iov/FUwX\n'
                   'QOXnrxeCOTb5d+L89SH9ws/ui0LwD+8+nJcA8DvqP6r0jtnhov0jIMcNVDSi6oeo\n'
                   '3AEY7ICJzcQJ4oRn+K+8vPNdPhfuikPYe9l4iSuJgpAlaGWyD/GlFyz12DFz2/Wu\n'
                   'NIcqR1ucvezRHn3eGMtvDv2WGaN4ifUc30k8XgSUesmwSI6beb5+hxq7wXfsurnP\n'
                   'EUrPY9ts3lfiAgxzTKOuj1VR5hn7cJyLN8jF0mZs4D6eSSHorIddhmaNiCq5ZbMd\n'
                   'QdlDiPvnXHT41OoXOb7tDEt7SGoiRh2noCZ1aZiSziECgYEA+tuPPLYWU6JRB6EW\n'
                   'PhbcXQbh3vML7eT1q7DOz0jYCojgT2+k7EWSI8T830oQyjbpe3Z86XEgH7UBjUgq\n'
                   '27nJ4E6dQDYGbYCKEklOoCGLE7A60i1feIz8otOQRrbQ4jcpibEgscA6gzHmunYf\n'
                   'De5euUgYW+Rq2Vmr6/NzUaUgui8CgYEAxJMDwPOGgiLM1cczlaSIU9Obz+cVnwWn\n'
                   'nsdKYMto2V3yKLydDfjsgOgzxHOxxy+5L645TPxK6CkiISuhJ93kAFFtx+1sCBCT\n'
                   'tVzY5robVAekxA9tlPIxtsn3+/axx3n6HnV0oA/XtxkuOS5JImgEdXqFwJZkerGE\n'
                   'waftIU2FCfUCgYEArl8+ErJzlJEIiCgWIPSdGuD00pfZW/TCPCT7rKRy3+fDHBR7\n'
                   '7Gxzp/9+0utV/mnrJBH5w/8JmGCmgoF+oRtk01FyBzdGgolN8GYajD6kwPvH917o\n'
                   'tRAzcC9lY3IigoxbiEWid0wqoBVoz4XaEkH2gA44OG/vQcQOOEYSi9cfh6sCgYBg\n'
                   'KLaOXdJvuIxRCzgNvMW/k+VFh3pJJx//COg2f2qT4mQCT3nYiutOh8hDEoFluc+y\n'
                   'Jlz7bvNJrE14wnn8IYxWJ383bMoLC+jlsDyeaW3S5kZQbmehk/SDwTrg86W1udKD\n'
                   'sdtSLU3N0LCO4jh+bzm3Ki9hrXALoOkbPoU+ZEhvPQKBgQDf79XQ3RNxZSk+eFyq\n'
                   'qD8ytVqxEoD+smPDflXXseVH6o+pNWrF8+A0KqmO8c+8KVzWj/OfULO6UbKd3E+x\n'
                   '4JGkWu9yF1lEgtHgibF2ER8zCSIL4ikOEasPCkrKj5SrS4Q+j4u5ha76dIc2CVu1\n'
                   'hkX2PQ1xU4ocu06k373sf73A4Q==\n'
                   '-----END PRIVATE KEY-----')
    ca_key = ('-----BEGIN CERTIFICATE-----\n'
              'MIIDjzCCAncCFQCjC8r+I4xa7JoGUJYGOTcqDROA0DANBgkqhkiG9w0BAQsFADBg\n'
              'MQswCQYDVQQGEwJVUzERMA8GA1UECBMITWljaGlnYW4xEjAQBgNVBAcTCUFubiBB\n'
              'cmJvcjEUMBIGA1UEChMLUGFwcHkgUHJveHkxFDASBgNVBAMTC1BhcHB5IFByb3h5\n'
              'MB4XDTE1MTEyMDIxMTEzOVoXDTI1MTExNzIxMTEzOVowYDELMAkGA1UEBhMCVVMx\n'
              'ETAPBgNVBAgTCE1pY2hpZ2FuMRIwEAYDVQQHEwlBbm4gQXJib3IxFDASBgNVBAoT\n'
              'C1BhcHB5IFByb3h5MRQwEgYDVQQDEwtQYXBweSBQcm94eTCCASIwDQYJKoZIhvcN\n'
              'AQEBBQADggEPADCCAQoCggEBAMCgKWthQQHuUzTNBoqRdlUbZ3UG72FXy6unHSA1\n'
              'cxvJnabfFv6wpmO78Uc+5Z6cDgpo3mBFRP6gt++2cXohrSOlE1adfQXKf+Kt2DUF\n'
              'YYmfuTuYnYPQ1dlBzOfb7HFjTnn3018Zao0oJjKOFLA+xQr6wYmqLtpIN2VL3tlO\n'
              'OtBVNMWwLT6RK7iVLl+xZfGqsotroCjxbtptVE4kdrOH9zEzhQqmBZT4TrIPijhm\n'
              'Adj5IxNVSH8g4zwO45XIsRa3Higs2IsyWlZPerLggyk4XpW5TokXYcZXXdKgl+Gw\n'
              'tew9FstVMCdm8lxnC2AObo18pqlTxbyiWQNXUF9hAQxI1fsCAwEAAaNFMEMwEgYD\n'
              'VR0TAQH/BAgwBgEB/wIBADAOBgNVHQ8BAf8EBAMCAQYwHQYDVR0OBBYEFNo5o+5e\n'
              'a0sNMlW/75VgGJCv2AcJMA0GCSqGSIb3DQEBCwUAA4IBAQBdJDhxbmoEe27bD8me\n'
              'YTcLGjs/StKkSil7rLbX+tBCwtkm5UEEejBuAhKk2FuAXW8yR1FqKJSZwVCAocBT\n'
              'Bo/+97Ee+h7ywrRFhATEr9D/TbbHKOjCjDzOMl9yLZa2DKErZjbI30ZD6NafWS/X\n'
              'hx5X1cGohHcVVzT4jIgUEU70vvYfNn8CTZm4oJ7qqRe/uQPUYy0rwvbd60oprtGg\n'
              'jNv1H5R4ODHUMBXAI9H7ft9cWrd0fBQjxhoj8pvgJXEZ52flXSqQc7qHLg1wO/zC\n'
              'RUgpTcNAb2qCssBKbj+c1vKEPRUJfw6UYb0s1462rQNc8BgZiKaNbwokFmkAnjUg\n'
              'AvnX\n'
              '-----END CERTIFICATE-----')
    return (ca_key, private_key)

def notouch_mangle_req(request, conn_id):
    orig_req = http.Request(request.full_request)
    orig_req.port = request.port
    orig_req.is_ssl = request.is_ssl
    d = mock_deferred(orig_req)
    return d

def notouch_mangle_rsp(response, conn_id):
    req = http.Request()
    orig_rsp = http.Response(response.full_response)
    req.response = orig_rsp
    d = mock_deferred(req)
    return d

def req_mangler_change(request, conn_id):
    req = http.Request('GET /mangled HTTP/1.1\r\n\r\n')
    d = mock_deferred(req)
    return d

def rsp_mangler_change(request, conn_id):
    req = http.Request()
    rsp = http.Response('HTTP/1.1 500 MANGLED\r\n\r\n')
    req.response = rsp
    d = mock_deferred(req)
    return d

####################
## Unit test tests

def test_proxy_server_fixture(unconnected_proxyserver):
    unconnected_proxyserver.transport.write('hello')
    assert unconnected_proxyserver.transport.getOutBuffer() == 'hello'
    
@pytest.inlineCallbacks
def test_mock_deferreds():
    d = mock_deferred('Hello!')
    r = yield d
    assert r == 'Hello!'

def test_deleted():
    with pytest.raises(NotImplementedError):
        reactor.connectTCP("www.google.com", "80", ServerFactory)
    with pytest.raises(NotImplementedError):
        reactor.connectSSL("www.google.com", "80", ServerFactory)
    
####################
## Proxy Server Tests

def test_proxy_server_connect(unconnected_proxyserver, mocker):
    mocker.patch("twisted.internet.reactor.connectSSL")
    unconnected_proxyserver.lineReceived('CONNECT https://www.dddddd.fff:433 HTTP/1.1')
    unconnected_proxyserver.lineReceived('')
    assert unconnected_proxyserver.transport.getOutBuffer() == 'HTTP/1.1 200 Connection established\r\n\r\n'
    assert unconnected_proxyserver._request_obj.is_ssl
    
def test_proxy_server_basic(proxyserver, mocker):
    mocker.patch("twisted.internet.reactor.connectSSL")
    mocker.patch('pappyproxy.proxy.ProxyServer.setRawMode')
    proxyserver.lineReceived('GET / HTTP/1.1')
    proxyserver.lineReceived('')

    assert proxyserver.setRawMode.called
    args, kwargs = twisted.internet.reactor.connectSSL.call_args
    assert args[0] == 'www.AAAA.BBBB'
    assert args[1] == 443
    
@pytest.inlineCallbacks
def test_proxy_client_basic(mocker, proxy_connection):
    mocker.patch('pappyproxy.mangle.mangle_request', new=notouch_mangle_req)
    mocker.patch('pappyproxy.mangle.mangle_response', new=notouch_mangle_rsp)
    # Make the connection
    (prot, sent, resp_deferred) = yield proxy_connection('GET / HTTP/1.1\r\n\r\n')
    assert sent == 'GET / HTTP/1.1\r\n\r\n'
    prot.lineReceived('HTTP/1.1 200 OK')
    prot.lineReceived('Content-Length: 0')
    prot.lineReceived('')
    ret_req = yield resp_deferred
    response = ret_req.response.full_response
    assert response == 'HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n'

@pytest.inlineCallbacks
def test_proxy_client_mangle_req(mocker, proxy_connection):
    mocker.patch('pappyproxy.mangle.mangle_request', new=req_mangler_change)
    mocker.patch('pappyproxy.mangle.mangle_response', new=notouch_mangle_rsp)
    
    # Make the connection
    (prot, sent, resp_deferred) = yield proxy_connection('GET / HTTP/1.1\r\n\r\n')
    assert sent == 'GET /mangled HTTP/1.1\r\n\r\n'

@pytest.inlineCallbacks
def test_proxy_client_basic(mocker, proxy_connection):
    mocker.patch('pappyproxy.mangle.mangle_request', new=notouch_mangle_req)
    mocker.patch('pappyproxy.mangle.mangle_response', new=rsp_mangler_change)
    # Make the connection
    (prot, sent, resp_deferred) = yield proxy_connection('GET / HTTP/1.1\r\n\r\n')
    prot.lineReceived('HTTP/1.1 200 OK')
    prot.lineReceived('Content-Length: 0')
    prot.lineReceived('')
    ret_req = yield resp_deferred
    response = ret_req.response.full_response
    assert response == 'HTTP/1.1 500 MANGLED\r\n\r\n'