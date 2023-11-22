'''
Description: operation to runner
Author: guoping
Date: 2023-06-12 14:30:21
Acknowledgements: TBD
'''

import os
import json
import tempfile
import traceback
from urllib.request import urlopen

import yaml

from inferno.logger import logger
from inferno.operators.op_base import InfernoOperatorBase


class InfernoOperatorRunner(InfernoOperatorBase):
    def run_pipeline(self, **kwargs):
        raise NotImplementedError('Run pipeline method is not implemented!')

    def download_default_configs(self, config_url):
        with urlopen(config_url) as f:
            configs = yaml.load(f, Loader=yaml.FullLoader)
        assert configs is not None, f'Failed to download configs from {config_url}'
        return configs['formal'] if os.getenv('SUMERU_ENV', 'devnet') == 'formal' else configs['test']

    def run(self, inputs):
        try:
            logger.info(f'Inputs: {inputs}')
            with tempfile.TemporaryDirectory() as self.tmp_dir:
                outputs = self.run_pipeline(inputs)
            return [{'ret': 0, 'msg': 'success', 'data': json.dumps(outputs, ensure_ascii=False)}]
        except InfernoOperatorException as err:
            logger.error(traceback.format_exc())
            logger.error(f'Error: {err}')
            raise RuntimeError(str(err))
            # return [{'ret': err.ret, 'msg': err.msg, 'data': ''}]


class InfernoOperatorException(Exception):
    def __init__(self, ret=0, msg=''):
        self.__ret = ret
        self.__msg = msg

    @property
    def ret(self):
        return self.__ret

    @property
    def msg(self):
        return self.__msg

    def __str__(self):
        return json.dumps({'ret': self.__ret, 'msg': self.__msg}, ensure_ascii=False)
