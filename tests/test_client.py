import threading
import unittest
import xmlrpc.server

import xmlrpc_client_requests.client


# lifted unchanged from cpython/Lib/test/test_xmlrpc.py

ADDR = PORT = URL = None

def http_server(evt, numrequests, requestHandler=None, encoding=None):
    class TestInstanceClass:
        def div(self, x, y):
            return x // y

        def _methodHelp(self, name):
            if name == 'div':
                return 'This is the div function'

        class Fixture:
            @staticmethod
            def getData():
                return '42'

    class MyXMLRPCServer(xmlrpc.server.SimpleXMLRPCServer):
        def get_request(self):
            # Ensure the socket is always non-blocking.  On Linux, socket
            # attributes are not inherited like they are on *BSD and Windows.
            s, port = self.socket.accept()
            s.setblocking(True)
            return s, port

    if not requestHandler:
        requestHandler = xmlrpc.server.SimpleXMLRPCRequestHandler
    serv = MyXMLRPCServer(("localhost", 0), requestHandler,
                          encoding=encoding,
                          logRequests=False, bind_and_activate=False)
    try:
        serv.server_bind()
        global ADDR, PORT, URL
        ADDR, PORT = serv.socket.getsockname()
        #connect to IP address directly.  This avoids socket.create_connection()
        #trying to connect to "localhost" using all address families, which
        #causes slowdown e.g. on vista which supports AF_INET6.  The server listens
        #on AF_INET only.
        URL = "http://%s:%d"%(ADDR, PORT)
        serv.server_activate()
        serv.register_introspection_functions()
        serv.register_multicall_functions()
        serv.register_function(pow)
        serv.register_function(lambda x: x, 'têšt')
        @serv.register_function
        def my_function():
            '''This is my function'''
            return True
        @serv.register_function(name='add')
        def _(x, y):
            return x + y
        testInstance = TestInstanceClass()
        serv.register_instance(testInstance, allow_dotted_names=True)
        evt.set()

        # handle up to 'numrequests' requests
        while numrequests > 0:
            serv.handle_request()
            numrequests -= 1

    except TimeoutError:
        pass
    finally:
        serv.socket.close()
        PORT = None
        evt.set()


class BaseServerTestCase(unittest.TestCase):
    requestHandler = None
    request_count = 1
    threadFunc = staticmethod(http_server)

    def setUp(self):
        # enable traceback reporting
        xmlrpc.server.SimpleXMLRPCServer._send_traceback_header = True

        self.evt = threading.Event()
        # start server thread to handle requests
        serv_args = (self.evt, self.request_count, self.requestHandler)
        thread = threading.Thread(target=self.threadFunc, args=serv_args)
        thread.start()
        self.addCleanup(thread.join)

        # wait for the server to be ready
        self.evt.wait()
        self.evt.clear()

    def tearDown(self):
        # wait on the server thread to terminate
        self.evt.wait()

        # disable traceback reporting
        xmlrpc.server.SimpleXMLRPCServer._send_traceback_header = False


class ClientTestCase(BaseServerTestCase):

    def test_simple(self):
        p = xmlrpc_client_requests.client.ServerProxy(URL)
        self.assertEqual(p.pow(6,8), 6**8)


if __name__ == '__main__':
    unittest.main()
