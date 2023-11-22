'''
Description: API for TRPC services
Author: guoping
Date: 2022-03-31 10:53:10
Acknowledgements: https://git.woa.com/polaris/polaris-python/blob/python3/examples/getinstance/wr/main.py
'''

import os
import uuid

import requests

from trpc.log import logger
from polaris.pkg.config.api import Configuration
from polaris.api.consumer import create_consumer_by_config
from polaris.pkg.model.service import GetOneInstanceRequest


CONSUMER = None  # IMPORTANT: consumer对象维护了数据缓存，需要全局复用


class PolarisService(object):
    def __init__(self, service_name, namespace=None, timeout=5000, **kwargs):
        namespace = namespace or ('Production' if os.getenv('SUMERU_ENV') == 'formal' else 'Development')
        self.request = GetOneInstanceRequest(uuid.uuid1(), service_name, namespace, use_discover_cache=False)
        self.timeout = timeout
        self.headers = {'content-type': 'application/json'}
        self.init_consumer()
        logger.info(f'Successfully connected to {service_name}')

    def init_consumer(self):
        polaris_config = Configuration()
        polaris_config.set_default()
        global CONSUMER
        if CONSUMER is not None:
            CONSUMER.destroy()
        CONSUMER = create_consumer_by_config(polaris_config)

    def post(self, url_postfix, data):
        resp = CONSUMER.get_one_instance(self.request)
        ip, port = resp.get_host(), resp.get_port()
        url = f'http://{ip}:{port}/{url_postfix}'
        resp = requests.post(url, json=data, timeout=self.timeout)
        return resp.json()

    def get(self, url_postfix):
        resp = CONSUMER.get_one_instance(self.request)
        ip, port = resp.get_host(), resp.get_port()
        url = f'http://{ip}:{port}/{url_postfix}'
        resp = requests.get(url)
        return resp
