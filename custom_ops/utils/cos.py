'''
Description: API for COS database implemented by qcloud-inner-cos
Author: guoping
Date: 2023-03-30 20:17:10
Acknowledgements: TBD
'''

import os
import re
import time
from urllib.request import urlretrieve
from urllib.parse import urlparse

from inferno.logger import logger
from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosException


class CosDB(object):
    def __init__(self, target, retry=3, **kwargs):
        sumeru_env = os.getenv('SUMERU_ENV', 'devnet')
        cos_config, self.bucket = self.parse_args(target, sumeru_env)
        enable_old_domain = True if sumeru_env == 'devnet' else False
        self.cos_config = CosConfig(EnableOldDomain=enable_old_domain, **cos_config)
        self.client = CosS3Client(self.cos_config)
        self.retry = retry
        logger.info(f'Successfully connected to {target}')

    def parse_args(self, target, sumeru_env):
        if isinstance(target, dict):
            target = target['formal'] if sumeru_env == 'formal' else target['test']
        reg = re.compile(r'^cos:\/\/(?P<secretid>\S*?):(?P<secretkey>\S*@*\S*?)@(?P<bucket>\S*?)\.(?P<region>\S*?)$')
        res = reg.fullmatch(target)
        cos_config = {
            'SecretId': res.group('secretid'),
            'SecretKey': res.group('secretkey'),
            'Region': res.group('region'),
        }
        return cos_config, res.group('bucket')

    def get_url(self, cos_path):
        return self.cos_config.uri(self.bucket, cos_path)

    def get_filename(self, url):
        return urlparse(url).path.lstrip('/')

    def to_inner_url(self, url):
        if isinstance(url, str):
            url = url.replace('.cos.', '.cos-internal.')
            url = url.replace('myqcloud.com', 'tencentcos.cn')
            url = url.replace('https://', 'http://')
            return url
        elif isinstance(url, (list, tuple, set)):
            return [self.to_inner_url(u) for u in url]
        elif isinstance(url, dict):
            return {key: self.to_inner_url(value) for key, value in url.items()}
        else:
            raise NotImplementedError(f'Invalid url type: {type(url)}')

    def to_outer_url(self, url):
        if isinstance(url, str):
            url = url.replace('.cos-internal.', '.cos.')
            url = url.replace('tencentcos.cn', 'myqcloud.com')
            url = url.replace('http://', 'https://')
            return url
        elif isinstance(url, (list, tuple, set)):
            return [self.to_outer_url(u) for u in url]
        elif isinstance(url, dict):
            return {key: self.to_outer_url(value) for key, value in url.items()}
        else:
            raise NotImplementedError(f'Invalid url type: {type(url)}')

    def upload(self, cos_path, file_str):
        for _ in range(self.retry):
            try:
                self.client.put_object(Bucket=self.bucket, Key=cos_path, Body=file_str)
                return self.get_url(cos_path)
            except CosException as err:
                logger.error(f'COS Error: {err}')
                time.sleep(0.1)
        return None

    def download(self, cos_path):
        for _ in range(self.retry):
            try:
                resp = self.client.get_object(Bucket=self.bucket, Key=cos_path)
                resp = resp['Body'].get_raw_stream().read().decode()
                return resp
            except (CosException, KeyError, TypeError, AttributeError) as err:
                logger.error(f'COS Error: {err}')
                time.sleep(0.1)
        return None

    def check(self, cos_path):
        try:
            self.client.head_object(Bucket=self.bucket, Key=cos_path)
            return self.get_url(cos_path)
        except CosException:
            return None

    def delete(self, cos_path):
        for _ in range(self.retry):
            try:
                self.client.delete_object(Bucket=self.bucket, Key=cos_path)
                return self.get_url(cos_path)
            except (CosException, KeyError, TypeError, AttributeError) as err:
                logger.error(f'COS Error: {err}')
                time.sleep(0.1)
        return None

    def upload_file(self, cos_path, local_path):
        for _ in range(self.retry):
            try:
                self.client.upload_file(Bucket=self.bucket, Key=cos_path, LocalFilePath=local_path)
                return self.get_url(cos_path)
            except CosException as err:
                logger.error(f'COS Error: {err}')
                time.sleep(0.1)
        return None

    def download_file(self, cos_path, local_path):
        for _ in range(self.retry):
            try:
                self.client.download_file(Bucket=self.bucket, Key=cos_path, DestFilePath=local_path)
                return self.get_url(cos_path)
            except (CosException, KeyError, TypeError, AttributeError) as err:
                logger.error(f'COS Error: {err}')
                time.sleep(0.1)
        return None

    def copy_file(self, old_url, cos_path, tmp_path=None):
        local_path = tmp_path or f'/tmp/tempfile_{int(time.time())}'
        urlretrieve(old_url, local_path)
        self.upload_file(cos_path, local_path)
        if tmp_path is None:
            os.remove(local_path)
        return self.get_url(cos_path)
