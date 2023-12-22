from functools import partial
import html
import xmlrpc.client

import requests


class ServerProxy:

    def __init__(self, url, verify=True):
        self.url = url
        self.verify = verify

    def dispatch(self, method_name, *args):
        headers = {
            'Content-Type': "text/xml",
            'User-Agent': "Python-xmlrpc/1.2.3",
        }
        data = xmlrpc.client.dumps(args, method_name, encoding='utf-8').encode('utf-8', 'xmlcharrefreplace')
        result = requests.post(f'{self.url}', headers=headers, data=data, verify=self.verify)
        if result.status_code == 200:
            result_data, method = xmlrpc.client.loads(result.content)
            if len(result_data) == 1:
                return result_data[0]
            else:
                return result_data

    def __getattr__(self, attr):
        return partial(self.dispatch, attr)
