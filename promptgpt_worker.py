import os
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(dir_path, 'magic_common'))

import argparse
import json
import logging
import requests

import yaml
from magic.config import config
from magic.task.base import TaskBase
from magic.task.worker import MagicWorker
from magic.utils.fuzzy_download import fuzzy_download_to_file
from magic.utils.task import retry_submit_new_task

from custom_ops.op_get_fiction_info import OPIpBibleObtain
from custom_ops.op_prompt_generate import OpPromptGenerate


def setup_logging_config(log_file=None):
    if log_file is not None:
        logging.basicConfig(
            level= logging.INFO,
            filename=log_file,
            filemode= 'a',
            format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
        )
    else:
        logging.basicConfig(
            level= logging.INFO,
            format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
        )


def get_api_url(path):
    api_base = os.environ.get('MAGIC_API_HOST')
    return f'{api_base}/{path}'


def ensure_folders():
    os.makedirs(os.path.join(dir_path, 'logs'), exist_ok=True)
    os.makedirs(os.path.join(dir_path, 'tmp'), exist_ok=True)


def inject_os_envs_from_yaml_config(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    envs = data.get('envs')
    logging.info(f'Inject environment variable: {envs}')
    os.environ.update(envs)
    config.reload_from_envs()


class PromptGenerateTask(TaskBase):

    TASK_TYPE = 'promptgpt'

    TYPE_IPBIBLE = 1
    TYPE_LAYOUT = 2

    def _setup_args(self, body):
        self.project_id = body.get('project_id', '')
        self.flow_id = body.get('flow_id', '')
        self.user_id = body.get('user_id', '')
        self.task_id = body.get('task_id', '')
        self.force_add = body.get("force_add", "no")
        self.params = json.loads(body.get('param', '{}'))
        self.chapter_id = self.params.get('chapter_id', '')
        self.para_id = self.params.get("para_id", "")
        self.scene_id = self.params.get("scene_id", "")
        self.flow_id = self.params.get("flow_id", "")
        if not self.task_id:
            self.task_id = f"{self.chapter_id}_{self.para_id}"

    def _get_download_path(self, type_, filename):
        fic_path = None
        if type_ == PromptGenerateTask.TYPE_IPBIBLE:
            fic_path = f"./tmp/ipbible_{filename}"
        elif type_ == PromptGenerateTask.TYPE_LAYOUT:
            fic_path = f"./tmp/layout_{filename}"
        return fic_path

    def _download_fiction(self):
        filename = f"fiction_{self.project_id}_{self.chapter_id}_{self.flow_id}.json"
        file_key = f"ipbible/{filename}"
        # FIXME
        s3_uri = f's3://{config.IPBIBLE_OUTPUT_BUCKET}/{file_key}'
        self.logger.info(f"Downloading {s3_uri}")
        download_path = self._get_download_path(PromptGenerateTask.TYPE_IPBIBLE, filename)
        fuzzy_download_to_file(s3_uri, download_path)
        return download_path

    def _get_lora_id(self, project_id, entity_id):
        url = get_api_url('api/world-view')
        headers = {
            'accept': 'application/json',
        }
        params = {
            'projectId': project_id,
            "entityId": entity_id,
        }
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            self.logger.error(f"msg: get role id failed. projectId: {project_id}, entity_id: {entity_id}")
            return ''
        data = response.json()
        lora_list = data['data']['data']
        if len(lora_list) == 0:
            self.logger.warning(f"db data len equal to 0")
            return ''
        return lora_list[0].get("loraId", "")

    def _get_lora_info(self, lora_id):
        url = get_api_url('api/roles-lora')
        headers = {'accept': 'application/json'}
        params = {'id': lora_id}
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            self.logger.error(f"msg: get role info failed. lora_id: {lora_id}")
            return ''
        data = response.json()
        lora_list = data['data']['data']
        if len(lora_list) == 0:
            self.logger.warning(f"db data len equal to 0")
            return ''
        return lora_list[0].get("loraModelInfo", {})

    def _get_input_info(self, parse_roles=False):
        fiction_path = self._download_fiction()
        with open(fiction_path, 'r') as frd:
            data = json.load(frd)
        model_info = {}
        if not parse_roles:
            return fiction_path, model_info

        chapter_info = data.get("chapter_info", {})
        paras = chapter_info.get("paras", [])
        roles = []
        for para in paras:
            id_ = para['para_id']
            if id_ != self.para_id:
                continue
            roles = para['roles']

        for role in roles:
            role_id = role['id']

            lora_id = self._get_lora_id(self.project_id, role_id)
            lora_model_info = self._get_lora_info(lora_id)
            if role_id not in model_info:
                model_info[role_id] = json.dumps(lora_model_info, ensure_ascii=False)
        model_info = json.dumps(model_info, ensure_ascii=False)
        return fiction_path, model_info

    def _run_single_task(self):
        self.logger.info(f"start process: {self.project_id}_{self.chapter_id}_{self.para_id}")
        fiction_path, model_info = self._get_input_info()

        fiction_parser = OPIpBibleObtain(self.project_id, self.chapter_id, self.para_id)
        ipbible, prompts_layout, ret_msg = fiction_parser.run([fiction_path, self.project_id, self.chapter_id, self.para_id, self.flow_id])
        self.logger.info(f"prompts_layout: {prompts_layout}")

        op_prompt_generate = OpPromptGenerate()
        op_prompt_generate.init()
        pos_prompts, neg_prompts, sub_pos_prompts, display_prompt, common_style_prompt,tags,scene_type,extra_prompt,extra_prompt_cn = op_prompt_generate.run(self.flow_id, self.project_id, self.chapter_id, self.para_id, ipbible, model_info)
        self.logger.info(f"pos_prompts: {pos_prompts}\nneg_prompts: {neg_prompts}\nsub_pos_prompts: {sub_pos_prompts}\ndisplay_prompt:{display_prompt}\ncommon_style_prompt:{common_style_prompt}\ntemplate_tags:{tags}\nscene_type:{scene_type}\nextra_prompt:{extra_prompt}\nextra_prompt_cn:{extra_prompt_cn}\n")

        next_params = {
            'project_id': self.project_id,
            'chapter_id': self.chapter_id,
            'para_id': self.para_id,
            "flow_id": self.flow_id,
            "user_id": self.user_id,
            "image_id": "",
            "scene_id": self.scene_id,
            "gpt_prompt": {
                "display_prompt": display_prompt,
                "pos_prompts": pos_prompts,
                "neg_prompts": neg_prompts,
                "sub_pos_prompts": sub_pos_prompts,
                "common_style_prompt": common_style_prompt,
                "template_tags": tags,
                "scene_type": scene_type,
                "extra_prompt": extra_prompt,
                "extra_prompt_cn": extra_prompt_cn
            },
            "layout_prompt": prompts_layout,
        }
        retry_submit_new_task({
            'type': 'layout',
            'project_id': self.project_id,
            'flow_id': self.flow_id,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'force_add': self.force_add,
            'param': json.dumps(next_params),
        })

    def process_task(self, body):
        self._setup_args(body)
        self._run_single_task()


def run_worker():
    aws_region = os.environ.get('AWS_REGION')
    sqs_queue_url = os.environ.get('AWS_SQS_QUEUE_URL')
    task_cls = PromptGenerateTask
    worker = MagicWorker(task_cls, sqs_queue_url, region=aws_region)
    logging.info(f'Worker started, listening {sqs_queue_url}')
    worker.set_task_concurrency(5)
    worker.loop_forever()


def parse_option():
    parser = argparse.ArgumentParser('prompt generation server', add_help=False)
    parser.add_argument("--yaml_config", type=str, default="server_config.yaml", help="yaml config")
    parser.add_argument("--log-to-stdout", action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_option()
    if args.log_to_stdout:
        setup_logging_config(None)
    else:
        setup_logging_config('./logs/prompt_generate.log')

    yaml_file = args.yaml_config
    if not os.path.isfile(yaml_file):
        print(f'file {yaml_file} not exist')
        exit(0)

    inject_os_envs_from_yaml_config(yaml_file)
    ensure_folders()
    run_worker()
