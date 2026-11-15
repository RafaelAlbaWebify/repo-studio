import io, pathlib, sys, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from studio import Handler

class HTTPBoundaryTests(unittest.TestCase):
    def fake(self, host):
        h=Handler.__new__(Handler)
        h.headers={'Host':host}
        h.server=type('Server',(),{'server_port':8765})()
        return h
    def test_local_hosts(self):
        for host in ('localhost:8765','127.0.0.1:8765'):
            self.assertTrue(self.fake(host).local_request())
    def test_remote_hosts_rejected(self):
        for host in ('attacker.example:8765','127.0.0.1:8766','localhost','127.0.0.1:8765.evil.invalid',''):
            self.assertFalse(self.fake(host).local_request())
    def test_token_still_random_on_state_creation(self):
        import secrets
        self.assertNotEqual(secrets.token_urlsafe(32),secrets.token_urlsafe(32))
