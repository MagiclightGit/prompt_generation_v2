'''
Description: Base API for venus
Author: guoping
Date: 2023-06-01 20:23:22
Acknowledgements: https://iwiki.woa.com/pages/viewpage.action?pageId=4008002223
'''

import json
import time
from urllib.request import urlretrieve

import requests

from inferno.logger import logger
from venus_api_base.venus_openapi import PyVenusOpenApi
from venus_api_base.exceptions import VenusBaseError
from venus_ml.session import new_session
from venus.ml.model import ModelInfo, ModelInfoBuilder, ModelFileType
from venus.ml.model import market_model_info, market_model_save, market_model_download


class VenusAPI(object):
    def __init__(self, secret_id, secret_key, retry=3, **kwargs):
        self.retry = retry
        self.header = {'Content-Type': 'application/json'}
        self.prefix = 'http://v2.open.venus.oa.com'
        self.api = PyVenusOpenApi(secret_id, secret_key)
        logger.info('Successfully connected to Venus API')

    def post(self, url, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        for _ in range(self.retry):
            try:
                return self.api.post(self.prefix + url, self.header, data)
            except VenusBaseError as err:
                logger.error(f'Venus Error: {err}')
                time.sleep(0.1)
        return None

    def get(self, url):
        for _ in range(self.retry):
            try:
                return self.api.get(self.prefix + url)
            except VenusBaseError as err:
                logger.error(f'Venus Error: {err}')
                time.sleep(0.1)
        return None

    def upload(self, url, data, header=None):
        for _ in range(self.retry):
            try:
                return self.api.request(self.prefix + url, data, header, 'UPLOAD')
            except VenusBaseError as err:
                logger.error(f'Venus Error: {err}')
                time.sleep(0.1)
        return None

    def put(self, upload_url, data, headers=None):
        for _ in range(self.retry):
            try:
                rsp = requests.put(upload_url, data=data, headers=headers)
                return rsp.status_code == 200
            except requests.RequestException as err:
                logger.error(f'Venus Error: {err}')
                time.sleep(0.1)
        return False

    def create_draw_task(self, draw_config):
        rsp = self.post('/aidraw/api/draw', draw_config)
        return rsp['data']['taskid_list'][0]

    def draw_img(self, draw_config, check_interval=5, check_times=100):
        task_id = self.create_draw_task(draw_config)
        for idx in range(check_times):
            rsp = self.get(f'/aidraw/api/get_result?task_id={task_id}')
            if len(rsp['data'][0]['pic_urls']) > 0:
                return rsp['data'][0]['pic_urls'][0].replace('https://', 'http://').split('?')[0]
            time.sleep(check_interval)
            logger.info(f'waiting for drawing ... {check_interval * (idx + 1)}s')
        return None

    def get_upload_url(self):
        rsp = self.get('/aidraw/api/get_pre_upload_url?file_type=application/zip')
        cos_key = rsp['data']['cos_key']
        upload_url = rsp['data']['upload_url'].replace('https://', 'http://')
        return cos_key, upload_url

    def create_upload_task(self, img_zip):
        cos_key, upload_url = self.get_upload_url()
        with open(img_zip, 'rb') as data:
            self.put(upload_url, data)
        return cos_key

    def upload_imgs(self, img_zip, check_interval=5, check_times=100):
        cos_key = self.create_upload_task(img_zip)
        for idx in range(check_times):
            rsp = self.get(f'/aidraw/api/report_upload?cos_key={cos_key}')
            if rsp['code'] == 0:
                return cos_key
            time.sleep(check_interval)
            logger.info(f'waiting for uploading ... {check_interval * (idx + 1)}s')
        return None

    def create_finetune_task(self, train_config):
        rsp = self.post('/aidraw/api/finetune/create', train_config)
        task_id = rsp['data']['task_id']
        task_version = rsp['data']['task_version']
        train_task_param = f'task_id={task_id}&task_run_time={task_version}'
        return train_task_param

    def create_sdscript_task(self, train_config):
        rsp = self.post('/aidraw/api/finetune/sdscript/create', train_config)
        task_id = rsp['data']['task_id']
        task_version = rsp['data']['task_version']
        train_task_param = f'task_id={task_id}&task_run_time={task_version}'
        return train_task_param

    def get_train_task_detail(self, train_task_param):
        return self.get(f'/aidraw/api/finetune/instance/details?{train_task_param}')

    def train_lora(self, train_config, check_interval=10, check_times=100):
        # train_task_param = self.create_finetune_task(train_config)
        train_task_param = self.create_sdscript_task(train_config)
        for idx in range(check_times):
            rsp = self.get(f'/aidraw/api/finetune/model/list?{train_task_param}')
            if len(rsp['data']['list']) > 0:
                train_result = rsp['data']['list'][0]
                return train_result
            time.sleep(check_interval)
            logger.info(f'waiting for training ... {check_interval * (idx + 1)}s')
        return None

    def download_trained_model(self, train_result, save_path, train_type='sd-script'):
        model_name = train_result['model_name']
        model_version = train_result['model_version']
        params = f'model_name={model_name}&model_version={model_version}&train_type={train_type}'
        rsp = self.get(f'/aidraw/api/finetune/model/download?{params}')
        urlretrieve(rsp['data']['download_urls'][0], save_path)
        return save_path


class VenusModel(object):
    def __init__(self, secret_id, secret_key, app_group, retry=3, **kwargs):
        self.app_group = app_group
        self.session = self.create_session(secret_id, secret_key, app_group, retry)
        assert self.session is not None, 'Failed to create venus model session'
        logger.info('Successfully connected to Venus Model')

    def create_session(self, secret_id, secret_key, app_group, retry):
        for _ in range(retry):
            try:
                session = new_session(secret_id, secret_key, app_group)
                return session
            except Exception as err:  # pylint: disable=broad-except
                time.sleep(1)
        logger.error(f'Venus Model Session Error: {err}')
        return None

    def dict_to_info(self, d) -> ModelInfo:
        return ModelInfo.model_validate(d)

    def info_to_dict(self, model_info: ModelInfo):
        model_info_dict = model_info.model_dump(by_alias=True)
        for key in model_info_dict:
            if isinstance(model_info_dict[key], str) and model_info_dict[key] != '' and model_info_dict[key][0] == '{':
                model_info_dict[key] = json.loads(model_info_dict[key])
        return model_info_dict

    def make_lora_param(self, model_info_dict, weight=1):
        instance_info = model_info_dict['instanceInfo']
        return {
            'model_name': instance_info['modelName'],
            'model_version': instance_info['modelVersion'],
            'prompt': '<lora:' + instance_info['files'][0]['name'].split('.')[0] + f':{weight:.2f}>',
        }

    def create_model(self, model_path, image_path, lora_id, rtx='jackieysong') -> ModelInfo:
        builder = (
            ModelInfoBuilder(
                market_name=lora_id,
                app_group_id=self.app_group,
                model_type='LoRA',  # Checkpoint / LoRA / Embeddings / LLModelBase
                share_user=rtx,
                maintainer=rtx,
                base_model='SD 1.5',  # SD 1.4 / SD 1.5 / SD 2.1
                share_range='AppGroup',
            )
            .add_file(model_path, file_type=ModelFileType.Model)
            .set_cover_image(image_path)
            .add_application('LoRA')
            .add_share_app_group(self.app_group)
        )
        model_info = builder.build()
        model_info = market_model_save(model_info, self.session)
        return model_info

    def update_model(self, model_path, image_path, model_info: ModelInfo, replace=True) -> ModelInfo:
        builder = (
            ModelInfoBuilder.from_exist_model_info(model_info, new_empty_version=replace)
            .add_file(model_path, file_type=ModelFileType.Model)
            .set_cover_image(image_path)
        )
        model_info_new = builder.build()
        model_info_new = market_model_save(model_info_new, self.session)
        return model_info_new

    def query_model(self, market_id, instance_id=None):
        return market_model_info(market_id, instance_id, self.session)

    def download_model(self, local_path, market_id, instance_id=None, **kwargs):
        return market_model_download(local_path, market_id, instance_id, session=self.session, **kwargs)
