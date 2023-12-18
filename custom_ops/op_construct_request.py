"""
Author: guojianyuan
Date: 2023-11-15 16:23:15
Description: 
"""
import time
import traceback
import json
import tempfile
import secrets
import tarfile
import re
import os
import yaml
import random
import string
import copy
import requests
from typing import Dict, NoReturn
from urllib.request import urlretrieve, urlopen
from pathlib import Path
import logging

from tqdm import tqdm
from custom_ops.utils.openai_chatgpt import TruboOpenaiGptClient
#from custom_ops.utils.mysql import MysqlDB
from custom_ops.utils.sql_operator import SQLOperator
# import custom_ops.op_prompt_generate 


class OpConstructRequest(object):
    def __init__(
        self,
        #df_server_url = 'http://172.190.57.101:7001/sd_generator',
        df_server_url = 'http://0.0.0.0:7001/sd_generator',
        timeout = 300
    ):
        # 设置参考 https://iwiki.woa.com/pages/viewpage.action?pageId=4008002223
        self.size_id = 8  # 1024x576
        self.cfg_scale = 7.5
        self.step_num = 25
        self.batch_size = 1
        # self.sampler_id = 4  # 20 - DPM++ SDE Karras
        self.sampler_id = 20
        self.upload_id = 0  # upload_id 图生图使用
        self.task_type = "txt2img"
        # self.denoising_strength = 0.5  # webUI 中的denoising参数   
        self.chatgpt_api_func = TruboOpenaiGptClient()

        self.others_lora = {"lora_model_id":"1000085",
                    "meta":{"weight":0.0, 
                            "names" : ["路人"],
                            "prompts" : "1human, upper body, no earrings, <lora:hhdyg1-000010:0.0>"},
                    "base_model_id":"1000037"
                }

        self.default_lora = {   
                                "model_name": "market_4d8ea30d821b839e",
                                "model_version": "20230705164807",
                                "prompt": "1male, white shirt, <lora:shenyong-000008:0>"
                            }

        # 拍摄手法
        self.layout_map = {
            "close_scene": "upper_body",
            "middle_scene": "full_body",
            "far_scene": "wide_shot",
            "back_view": "back_view",
            "top_view": "from above",
            "front_view": "look at viewer",
            "side_view": "side view",
            "其他": "",
            "正向": "look at viewer",
            "左向": "side view",
            "右向": "side view",
            "背向": "from back",
            "男": "male",
            "女": "female"
        }

        # rp weight
        self.rp_weight = {
            0: 0,
            1: 0,
            2: 0.8
        }

        # layout
        self.lo_cosprefix = {
            "bbox": "https://testdocsplitblobtrigger.blob.core.windows.net/layout-bbox/",
            "depth": "https://testdocsplitblobtrigger.blob.core.windows.net/layout-depth/",
            "segement":  "https://testdocsplitblobtrigger.blob.core.windows.net/layout-segement/",
            "lineart": "https://testdocsplitblobtrigger.blob.core.windows.net/layout-lineart/",
            "openpose": "https://testdocsplitblobtrigger.blob.core.windows.net/layout-openpose/",
            "instance": "s3://layout-data/layout-instance/",
        }

        # mdb
        #self.mdb = MysqlDB(**(self.server_config["mysql"]))
        host = "prototype.cdtoyz6oo1ls.rds.cn-north-1.amazonaws.com.cn"
        #host = "script-light.cluster-cdtoyz6oo1ls.rds.cn-north-1.amazonaws.com.cn"
        user = "admin"
        #password = "dream-big1000"
        password = "dreambigger234"
        db_name = "prototype"

        self.mdb = SQLOperator(host, user, password, db_name)

        self.diffuser_server_url = df_server_url
        self.timeout = timeout
        
    def init(self):
        with open("./trpc_python.yaml", "r") as f:
            self.server_config = yaml.load(f, Loader=yaml.FullLoader)
        # 随机路人

        # hires.fix enable
        self.use_hires = self.server_config["use_hires"]["flag"]
        # generation api type
        self.gen_api_type = "diffusers"
        # negative prompt style
        self.neg_prompt_style = self.server_config["neg_prompt_style"]["style"]  # ["bright", "dark"]

        # ctrl_weights
        self.ctrl_pose_weight = self.server_config["weights"]["ctrl_pose_weight"]
        self.ctrl_depth_weight = self.server_config["weights"]["ctrl_depth_weight"]
        self.multip_ctrl_pose_weight = self.server_config["weights"]["multip_ctrl_pose_weight"]
        self.multip_ctrl_depth_weight = self.server_config["weights"]["multip_ctrl_depth_weight"]

        if self.gen_api_type == "diffusers":
            # base model for diffusers service
            '''
            self.df_client = InfernoTrpcClient(pb_module_dir="../inferno_pb")

            # 正式环境/测试环境
            diffusers_env = self.server_config["call_api"]["env"]  # ["Production", "Development", "Test-Production"]
            logger.info("The server environment: {}".format(diffusers_env))
            
            if diffusers_env == "Test-Production":
                self.df_client.set_options(
                    service_target = "polaris://trpc.aigc.diffusers_server_test.Inferno",
                    service_namespace="Production",
                    caller_service_name="trpc.aigc.diffusers_server.Inferno",
                    caller_namespace="Production",
                    caller_envname="formal",
                    timeout=240000,
                )
            else:
                self.df_client.set_options(
                    #  ip://ip:port
                    # service_target="ip://9.218.62.137:16324",
                    service_target = "polaris://trpc.aigc.diffusers_server.Inferno",
                    # Development 测试环境
                    service_namespace=diffusers_env,
                    caller_service_name="trpc.aigc.diffusers_server.Inferno",
                    caller_namespace=diffusers_env,
                    caller_envname="formal",
                    timeout=240000,
                )
            '''
            self.df_base_model = self.server_config["model_config"]["base_model"]
    
    def get_lora_by_name(self, model_info, name_list):
        for key, lora_info in model_info.items():
            for name in name_list:
                if name in lora_info["meta"]["names"]:
                    return lora_info
            
        return self.others_lora

    def parse_lora_info(self, lora_info_raw):
        # {"style_model_prompts": {"model_name": "market_4d8ea30d821b839e", "model_version": "20230705164807", "prompt": "<lora:shenyong-000008:0.3>"}, "trigger": "shenyong", "characteristic": "white shirt"}
        # lora_info_raw = json.loads(lora_info_raw)
        # 如果style_model_prompts没有了，这边需要及时更新
        
        weight = 0.7

        if isinstance(lora_info_raw, str):
            lora_info_raw = json.loads(lora_info_raw) 
        try:
            prefix, _ = lora_info_raw['style_model_prompts']['prompt'].rsplit(':', 1)
            lora_info_raw['style_model_prompts']['prompt'] = f'{prefix}:{weight}>'

            lora_info = {}
            lora_info["model_name"] = lora_info_raw["style_model_prompts"]["model_name"]
            lora_info["model_version"] = lora_info_raw["style_model_prompts"]["model_version"]
            # lora_info["prompt"] = ", ".join([lora_info_raw["characteristic"],
            #                                 lora_info_raw["trigger"],
            #                                 lora_info_raw["style_model_prompts"]["prompt"]])
            lora_info["prompt"] = ", ".join([lora_info_raw["trigger"],
                                            lora_info_raw["characteristic"]])
            lora_info["trigger"] = lora_info_raw["trigger"]
            lora_info["model_url"] = lora_info_raw["lora_model_url"]
            lora_info["weight"] = lora_info_raw["lora_weight"]
            
            lora_prompts = [lora_info_raw["characteristic"], lora_info_raw["trigger"]]
        except Exception as err:
            logging.error("parse lora info failed, error: {}".format(err))
            return {}, []

        return lora_info, lora_prompts

    def pares_model_info(self, model_info):
        if len(model_info) == 0:
            return None
        
        try:
            new_dict = {}
            for k, v in json.loads(model_info).items():
                new_dict[k] = json.loads(v)
        except Exception as e:
            logging.info("Parse model info error. model_info: {}".format(model_info))
            model_info = None

        return new_dict
    
    def add_action(self, lora_prompts, i_role):
        # 增加人物动作和表情
        need_info_keys = ["emoji_en", "actions_en"]
        for info_key in need_info_keys:
            info_list = i_role[info_key]
            if len(info_list) > 0:  
                info_prompts = [f"({info.lower()}:1.2)" for info in info_list]
                lora_prompts.extend(info_prompts)
                
        lora_prompts = ", ".join(lora_prompts)
        return lora_prompts

    def pprmp_rank(self, model_info, ip_roles_info, lo_prompt):
        people_prmp = {}
        lora_info_dict = {}
        ip_roles = copy.deepcopy(ip_roles_info)

        for i, i_prompt in enumerate(lo_prompt):
            flag = False
            for j, i_role in enumerate(ip_roles):
                if i_role["gender_en"] == self.layout_map.get(i_prompt["gender"], ""):
                    role_id = i_role["id"]
                    lora_info, lora_prompts = self.parse_lora_info(model_info[role_id])
                    lora_info_dict[role_id] = lora_info
                    lora_prompts = self.add_action(lora_prompts, i_role)
                    people_prmp[role_id] = lora_prompts
                    ip_roles.pop(j)
                    flag = True
                    continue

            if flag:
                continue

            role_id = ip_roles[0]["id"]
            lora_info, lora_prompts = self.parse_lora_info(model_info[role_id])
            lora_prompts = self.add_action(lora_prompts, ip_roles[0])
            people_prmp[role_id] = lora_prompts
            lora_info_dict[role_id] = lora_info
            ip_roles.pop(0)

        return people_prmp, lora_info_dict
    
    # layout: [{}]
    def run(self, flow_id, project_id, chid, para_id, ipbible, model_info, batch_size, layout, style_info):
        # get from IP bible
        inputs = [flow_id, project_id, chid, para_id, ipbible, model_info, batch_size, layout, style_info]
        # logging.info(f"{inputs}")

        human_prompts = ""
        scene_prompts = ""
        # lora_info_list = []
        lora_info_dict = {}
        sub_pos_prompts = {}
        debug_dict = {
            "project_id": project_id,
            "chid": chid,
            "paraid": para_id,
            "flowid": flow_id,
            "content": ipbible.get("para_content", "") if type(ipbible) == dict else "",
            "ipbible": json.dumps(ipbible, ensure_ascii=False),
            "flow_name": "character_generation_openapi_单人场景生成",
            "img_url": "{}",  # img_url
            "prompt": "{}",  # prompt
            "code": -1,  # code
            "time_cost": 0.,  # time_cost
            "layout_img_url": ""  # layout url
        }
        # process - lora-info
        logging.info("model info: {}, model_info_len: {}".format(model_info, len(model_info))) 

        # prompt_generater = custom_ops.op_prompt_generate.OpPromptGenerate()
        # prompt_generater.init()
        # pos_prompts, neg_prompts, sub_pos_prompts = prompt_generater.run(flow_id, fid, chid, para_id, ipbible, model_info)
        # env_prompt = pos_prompts['env_prompt']
        # person_prompt = pos_prompts['person_prompt']

        # ret_call_dict for return call results of different control information
        ret_call_dict = {"no-ctrl": None,
                         "openpose": None,
                         "depth": None}
        model_info = self.pares_model_info(model_info)
        # 生成设定
        if layout:
            layout = json.loads(layout)
            logging.info(f"{flow_id}_{project_id}_{chid}_{para_id} Layout info [0]: {layout}")
        else:
            layout = {}
            logging.info(f"Layout info is {layout}")
        
        # get prompt from layout
        env_prompt = layout.get("env_prompt", "")
        person_prompt = layout.get("person_prompt", [])
        sub_pos_prompts = layout.get("sub_prompt", {})
        neg_prompts = layout.get("neg_prompt", "")

        # generate first roles, human_prompts
        if len(ipbible) == 0:
            logging.info("ip bible is empty.")
            return [ret_call_dict, None, debug_dict]

        if model_info == None:
            logging.info("Parse model_info error. model_info: {}".format(model_info))
            return [ret_call_dict, None, debug_dict]
        
        num_person = len(person_prompt)
        prompts_data = layout.get("prompts_data", {})
        # num_person = prompts_data.get("num_person", 0)
        # if len(layout) > 0:
        if num_person > 0:     # 新链路无人的情况也会有layout，此时判断人物数量
            # batch size
            tmp_batch_size = 1  # 有layout时的batch size
        else:
            # tmp_batch_size = 4  # 没有layout时的batch size
            tmp_batch_size = 1  # 没有layout时的batch size
        
        batch_size = tmp_batch_size

        if batch_size < 1:
            batch_size = 1
                # TODO 增加双人模块的兜底逻辑，兜底逻辑 DONE 分拆在上面的判断逻辑中

        # ctrl_weights设定，暂无明显定论，可能需要进一步实验
        # if ipbible["num_person"] == 1:
        if num_person == 1:     # 人物数量从layout中获取
            ctrl_pose_weight = self.ctrl_pose_weight
            ctrl_depth_weight = self.ctrl_depth_weight
        # elif ipbible["num_person"] == 2:
        elif num_person == 2:
            ctrl_pose_weight = self.multip_ctrl_pose_weight
            ctrl_depth_weight = self.multip_ctrl_depth_weight
        else:
            ctrl_pose_weight = 0
            ctrl_depth_weight = 0
        if self.gen_api_type == "diffusers":
            # for diffusers, 0: no controlnet, 1: openpose, 2: depth
            lo_instance_url = ""
            if len(layout) > 0 and layout["urls"]:
                lo_img_key = layout["urls"].split("/")[-1]
                lo_openpose_url = os.path.join(self.lo_cosprefix["openpose"], lo_img_key)
                lo_depth_url = os.path.join(self.lo_cosprefix["depth"], lo_img_key)
                lo_lineart_url = os.path.join(self.lo_cosprefix["lineart"], lo_img_key)
                lo_instance_url = os.path.join(self.lo_cosprefix["instance"], lo_img_key) 
                lo_instance_url = lo_instance_url[:-3] + "png"

                # debug上报lineart url
                # {img_url: ['https://aigc-test-1258344701.cos.ap-nanjing.myqcloud.com/roles/fd0015lpra7/15/23088a864d3389c9/2_0.jpg']}

                debug_dict["layout_img_url"] = json.dumps({"img_url": lo_lineart_url})

                lo_idx = layout["idx"]
                
                ctrl_type = {
                    "no-ctrl": [],

                    # single controlnet
                    # "openpose": [{
                    #     "model": "https://aigc-1258344701.cos.ap-nanjing.tencentcos.cn/models/human_pose_synthesis/controlnets/openpose/diffusion_pytorch_model.safetensors",
                    #     "weight": 0.3,
                    #     "img_url": lo_openpose_url,
                    #     "config": "https://aigc-1258344701.cos.ap-nanjing.tencentcos.cn/models/human_pose_synthesis/controlnets/openpose/config.json",
                    #     "name": "openpose",
                    # }],

                    # "depth": [{
                    #     "model": "https://aigc-1258344701.cos.ap-nanjing.tencentcos.cn/models/human_pose_synthesis/controlnets/depth/diffusion_pytorch_model.safetensors",
                    #     "weight": 0.3,
                    #     "img_url": lo_depth_url,
                    #     "config": "https://aigc-1258344701.cos.ap-nanjing.tencentcos.cn/models/human_pose_synthesis/controlnets/depth/config.json",
                    #     "name": "openpose",
                    # }]

                    # TODO 增加多人物时controlnet的weights DONE
                    "multi-ctrl": [
                        {
                            "model": "https://testdocsplitblobtrigger.blob.core.windows.net/controlnet-model/openpose/diffusion_pytorch_model.safetensors",
                            "weight": ctrl_pose_weight, #if num_person == 2 else 0.5,
                            "img_url": lo_openpose_url,
                            "config": "https://testdocsplitblobtrigger.blob.core.windows.net/controlnet-model/openpose/config.json",
                            "name": "openpose",
                        },
                        {
                            "model": "https://testdocsplitblobtrigger.blob.core.windows.net/controlnet-model/depth/diffusion_pytorch_model.safetensors",
                            "weight": ctrl_depth_weight, #if num_person == 2 else 0.4,
                            "img_url": lo_depth_url,
                            "config": "https://testdocsplitblobtrigger.blob.core.windows.net/controlnet-model/depth/config.json",
                            "name": "depth",
                        },
                    ],
                }
                if lo_idx == "2":
                    pass
                    # 屏蔽有控制信号时 特写及环境的生成
                    # if "object" in ipbible["scene"]["subject_en"].keys():
                    #     ctrl_type["object"] = []
                    
                    # if "scenery" in ipbible["scene"]["subject_en"].keys():
                    #     ctrl_type["scenery"] = []

                    # if ipbible["scene"]["caption_with_roles_en"] != "":
                    #     ctrl_type["cwr-type"] = []
                
            else:
                # 无layout 场景生成
                ctrl_type = {
                    "no-ctrl": []
                }
                lo_idx = "N"

                if "object" in ipbible["scene"]["subject_en"].keys():
                    ctrl_type["object"] = []
                
                if "scenery" in ipbible["scene"]["subject_en"].keys():
                    ctrl_type["scenery"] = []
                
                if ipbible["scene"]["caption_with_roles_en"] != "":
                    ctrl_type["cwr-type"] = []
                # TODO 根据ip bible中的人数，构建regional prompter DONE

            rp_split_ratio = 0.5
            rp_bbox = []
            # if ipbible["num_person"] < 1:
            pos_prompts = ""
            if num_person < 1:
                # pos_prompts = env_prompt
                pos_prompts = env_prompt + "," + style_info.get('trigger', '')
            # elif ipbible["num_person"] == 1:
            elif num_person == 1:
                try:
                    role_id = prompts_data["person_id"][0][0]
                    lora_info, _ = self.parse_lora_info(model_info[role_id])
                    lora_info_dict[role_id] = lora_info
                except Exception:
                    pass

                # 此逻辑在layout中完成（）
                # 获取bbox info 并计算rp_split_ratio
                for item in layout["bounding_box_info"]:
                    bbox = item.get("bounding_box", [0.5, 0.5, 1, 1])
                    rp_bbox.append(bbox)
                    break

                # TODO 增加prompts判断和shoot 
                try:
                    lo_shoot = self.layout_map.get(layout["layout_scene"], "")
                except:
                    logging.info("'layout_scene' Layout of {}_{}_{}_{} has ERROR. Layout: {}".format(
                        flow_id, project_id, chid, para_id, layout
                    ))
                    lo_shoot = ""
                
                # try:
                #     lo_look = self.layout_map.get(json.loads(layout["prompt"])[0]["look"], "")
                # except:
                #     logging.info("'look' Layout of {}_{}_{}_{} ERROR. Layout: {}".format(
                #         flow_id, project_id, chid, para_id, layout
                #     ))
                #     lo_look = ""
                
                # shoot_tech = lo_shoot
                # if len(shoot_tech) > 0:
                #     if len(lo_look) > 0:
                #         lo_shoot = "{}, {}".format(lo_shoot, lo_look)
                # else:
                #     if len(lo_look) > 0:
                #         shoot_tech = lo_look
                # if len(shoot_tech) > 0:
                #     prompts_list = ['{}, {},'.format(list(person_prompt[0].values())[0], shoot_tech)]
                # else: 
                #     prompts_list = list(person_prompt.values())
                # prompts_list.append(env_prompt)
                # pos_prompts = " ".join(prompts_list)
                trigger = lora_info_dict[role_id].get('prompt', "")
                # pos_prompts = f"{person_prompt[0]['prompt']},{lo_shoot},{trigger},{env_prompt}"
                # 完全对其旧版本prompt
                if "(solo:2.0)," in  person_prompt[0]['prompt']:
                    # pos_prompts = person_prompt[0]['prompt'].replace("(solo:2.0),", f"(solo:2.0), {lo_shoot}, {trigger}") + f",{env_prompt}"
                    # 增加风格trigger，后续需要在prompt中写入
                    pos_prompts = person_prompt[0]['prompt'].replace("(solo:2.0),", f"(solo:2.0), {style_info.get('trigger', '')}, {lo_shoot}, {trigger}") + f",{env_prompt}"

                else:
                    # pos_prompts = f"{person_prompt[0]['prompt']},{lo_shoot},{trigger},{env_prompt}"
                    pos_prompts = f"{person_prompt[0]['prompt']},{style_info.get('trigger', '')},{lo_shoot},{trigger},{env_prompt}"
                # pos_prompts = f"{trigger},{lo_shoot},{env_prompt}"
            # elif ipbible["num_person"] == 2:
            elif num_person == 2:
                lo_shoot = ""
                # bb_look = ["", ""]
                rp_split_ratio = 0.5
                try:
                    for person_id in prompts_data["person_id"]:
                        role_id = person_id[0]
                        lora_info, _ = self.parse_lora_info(model_info[role_id])
                        # lora_prompts = self.add_action(lora_prompts, i_role)
                        lora_info_dict[role_id] = lora_info

                    # _, lora_info_dict = self.pprmp_rank(
                    # model_info, ipbible["roles"], json.loads(layout["prompt"]))
                    # 拍摄手法
                    lo_shoot = self.layout_map.get(layout["layout_scene"], "")
                    # 人物朝向
                    # bb_look = [self.layout_map.get(item["look"], "") for item in json.loads(layout["prompt"])]
                    # 获取bbox info 
                    for item in layout["bounding_box_info"]:
                        bbox = item.get("bounding_box", [])
                        rp_bbox.append(bbox)
                    # 计算split_ratio
                    bb_0 = layout["bounding_box_info"][0]["bounding_box"]
                    bb_1 = layout["bounding_box_info"][1]["bounding_box"]
                    rp_split_ratio = 0.5 * (bb_0[0] + bb_1[0])
                except Exception:
                    # logging.error(f"get lora info failed.")
                    for item in person_prompt:
                        role_id = item.get("entity_id", "")
                        if not role_id:
                            continue
                        lora_info, lora_prompts = self.parse_lora_info(model_info[role_id])
                        # lora_prompts = self.add_action(lora_prompts, i_role)
                        lora_info_dict[role_id] = lora_info
                # 拼接pos prompt
                pos_prompts = f"{env_prompt}, {style_info.get('trigger', '')}, {lo_shoot}"
                # logging.info(f"person_prompt: {person_prompt}")
                # for index, person_id in enumerate(prompts_data["person_id"]):
                #     role_id = person_id[0]
                #     trigger = lora_info_dict[role_id].get('prompt', "")
                # 冗余分配
                trigger_list = []
                assgin_id = set()
                for item in person_prompt:
                    role_id = item.get("entity_id")                    
                    if not role_id:
                        trigger = ""
                        prompt = ""
                    else:
                        trigger = lora_info_dict[role_id].get('prompt', "")
                        prompt = item.get('prompt', '')
                        assgin_id.add(role_id)
                    trigger_list.append([trigger, prompt])
                # 查找未找到entity_id的数据,再次分配
                for item in trigger_list:
                    if not item[0]:
                        for person_id in prompts_data["person_id"]:
                            role_id = person_id[0]
                            if role_id in assgin_id:
                                continue
                            item[0] = lora_info_dict[role_id].get('prompt', "")
                            assgin_id.add(role_id)
                            break
                # 拼接pos prompt
                for item in trigger_list:
                    pos_prompts = f"{pos_prompts} ADDCOL {item[0]}, {item[1]}"

                # for item in person_prompt:
                #     role_id = item.get("entity_id")                    
                #     if not role_id:
                #         trigger = ""
                #     else:
                #         trigger = lora_info_dict[role_id].get('prompt', "")
                #     pos_prompts = f"{pos_prompts} ADDCOL {trigger}, {item.get('prompt', '')}"
                    # pos_prompts = f"{pos_prompts} ADDCOL {trigger}, {person_prompt[index]['prompt']}"
                    # pos_prompts = f"{pos_prompts} ADDCOL {trigger}"
                # person_prompt_list = list(person_prompt.values())
                # for i in range(ipbible["num_person"]):
                #     temp = []
                #     if len(person_prompt_list[i]) > 0:
                #         temp.append(person_prompt_list[i])

                #     if len(bb_look[i]) > 0:
                #         temp.append(bb_look[i])

                #     temp = ", ".join(temp)

                #     prompts_list.append(temp)
                
                # pos_prompts = " ADDCOL ".join(prompts_list)

            # TODO 根据ip bible中的人数，构建regional prompter DONE
            # if ipbible["num_person"] < 2:
            # if num_person < 2:
            #     rp_config = {
            #         "rp_weight": 0,
            #     }
            # else:
            #     rp_config = {
            #         "rp_weight": 0.8,
            #         "rp_split_ratio": rp_split_ratio  # 由输入的bbox计算，默认0.5
            #     }
            rp_config = {
                "rp_weight": self.rp_weight.get(num_person, 0),
                "rp_split_ratio": rp_split_ratio,  # 由输入的bbox计算，默认0.5
                "rp_bbox": rp_bbox,
                "rp_instance": lo_instance_url,
            }
            # 轮询dict中的信息
            debug_prompt = {}
            res = []
            for c_type, c_value in ctrl_type.items():
                # 随机key保证重复生成不会被覆盖
                random_key = "".join(random.sample(string.ascii_letters, 4))
                log_id = f"{flow_id}_{project_id}_{chid}_{para_id}_{random_key}_{c_type}_lo{lo_idx}"
                input_data = {
                    "project_id": project_id,
                    "flow_id": flow_id,
                    "task_type": "text2img",
                    "task_key": log_id,
                    "infer_data": {
                        "base_config": {
                            "base_model": self.df_base_model,
                            "width": 1024,
                            "height": 576,
                            "guidance_scale": 7.5,
                            "step": 25,
                            "batch_size": 1,
                            "num_generation": batch_size,
                            "prompt": pos_prompts,
                            "negative_prompt": neg_prompts,
                            "seed": -1,
                        },
                        "highres_fix_config": {
                            "is_highres": True,
                            "highres_strength": 0.3,
                            "highres_step": 20,
                            "highres_upscale": 2,
                        },

                        # TODO 新增双人链路rp_weights的修改，也要增加split DONE
                        "regional_prompter_config": rp_config,
                        "face_highres_fix_config": {
                            "use_face_highres": True,
                            "steps": 20,
                            "strength": 0.3
                        },
                        "face_highres_fix_config": {
                            "use_face_highres": True,
                            "steps": 20,
                            "strength": 0.5,
                            "callback_cos_key": "",
                        },
                        "lora_configs": [
                            # {
                            #     "model": "https://testdocsplitblobtrigger.blob.core.windows.net/lora-model/add_detail.safetensors",
                            #     "weight": 0.5,
                            #     "type": "base",
                            # }
                            {
                                "model": style_info.get("lora_model_url", ""),
                                "weight": style_info.get("lora_weight", 0.5),
                                "trigger": style_info.get("trigger", ""),
                                "type": "style",
                            }
                        ],
                        "text_inversions": [
                            {
                                "model": "https://testdocsplitblobtrigger.blob.core.windows.net/lora-model/text_inversions/FastNegativeV2.pt",
                                "token": "FastNegativeV2"
                            },
                            {
                                "model": "https://testdocsplitblobtrigger.blob.core.windows.net/lora-model/text_inversions/EasyNegativeV2.safetensors",
                                "token": "EasyNegativeV2"
                            },
                            {
                                "model": "https://testdocsplitblobtrigger.blob.core.windows.net/lora-model/text_inversions/easynegative.safetensors",
                                "token": "easynegative"
                            },
                            {
                                "model": "https://testdocsplitblobtrigger.blob.core.windows.net/lora-model/text_inversions/bad-hands-5.pt",
                                "token": "bad-hands-5"
                            },
                            {
                                "model": "https://testdocsplitblobtrigger.blob.core.windows.net/lora-model/text_inversions/ng_deepnegative_v1_75t.pt",
                                "token": "ng_deepnegative_v1_75t"
                            },
                            {
                                "model": "https://testdocsplitblobtrigger.blob.core.windows.net/lora-model/text_inversions/negative_hand-neg.pt",
                                "token": "negative_hand-neg"
                            }
                        ],
                        # controlnet 示例
                        # "controlnet_configs":
                        # [{
                        #     "model": "https://aigc-1258344701.cos.ap-nanjing.tencentcos.cn/models/human_pose_synthesis/controlnets/openpose/diffusion_pytorch_model.safetensors",
                        #     "weight": 0.36,
                        #     "img_url": "https://aigc-1258344701.cos.ap-nanjing.myqcloud.com/test/pose/pose_test.png",
                        #     "config": "https://aigc-1258344701.cos.ap-nanjing.tencentcos.cn/models/human_pose_synthesis/controlnets/openpose/config.json",
                        #     "name": "openpose",
                        # },
                    },
                }
                # 增加调用时LoRA信息
                if c_type in ["object", "scenery", "cwr-type"]:
                    input_data["infer_data"]["base_config"]["prompt"] = sub_pos_prompts[c_type]
                    input_data["infer_data"]["controlnet_configs"] = c_value
                    input_data["infer_data"]["base_config"]["num_generation"] = 1

                    if c_type in ["cwr-type"]:
                        for role_id, lora_info in lora_info_dict.items():
                            logging.info("LoRA INFO. project_id: {}, chid: {}, para_id: {}, role_id: {}, lora_info: {}, c_type: {}".format(
                                project_id, chid, para_id, role_id, lora_info, c_type))
                            i_lora_info = {}
                            i_lora_info["model"] = lora_info.get("model_url", "")
                            i_lora_info["weight"] = lora_info.get("weight", "")
                            i_lora_info["trigger"] = lora_info.get("trigger", "")

                            # 这里可能后期改成由调度层配置
                            i_lora_info["type"] = "role"
                            input_data["infer_data"]["lora_configs"].append(i_lora_info)
                            input_data["infer_data"]["controlnet_configs"] = c_value
                else:
                    for role_id, lora_info in lora_info_dict.items():
                        logging.info("LoRA INFO. project_id: {}, chid: {}, para_id: {}, role_id: {}, lora_info: {}, c_type: {}".format(
                            project_id, chid, para_id, role_id, lora_info, c_type))
                        i_lora_info = {}
                        i_lora_info["model"] = lora_info.get("model_url", "")
                        i_lora_info["weight"] = lora_info.get("weight", "")
                        i_lora_info["trigger"] = lora_info.get("trigger", "")

                        # 这里可能后期改成由调度层配置
                        i_lora_info["type"] = "role"
                        input_data["infer_data"]["lora_configs"].append(i_lora_info)
                        input_data["infer_data"]["controlnet_configs"] = c_value

                # logging.info("Input_data for diffusers server: {}".format(input_data))
                # 新增调用字段在debug_prompt
                debug_prompt[c_type] = json.dumps(input_data, ensure_ascii=False)

                df_req = {
                    # "input_data": json.dumps(input_data)
                    "input_data": input_data
                }

                #print("input_data: {}".format(json.dumps(df_req)))

                if num_person >= 2 and (c_type in ["object", "scenery"]):
                    logging.info("ipbible num person: {}, c_type: {}".format(num_person, c_type))
                    continue
                
                if num_person >= 1 and (c_type in ["no-ctrl"]):
                    continue

                role_id = ''
                if num_person == 1:
                    role_id = person_prompt[0]["entity_id"]
                elif num_person == 2:
                    role_id = prompts_data["person_id"][-1][0]
                # logging.info("call diffuser: {}".format(json.dumps(df_req)))
                res.append(df_req)

            return res

                # aigc_generator_cmd = "insert into t_aigc_generator_prompt \
                # (img_fid, prompt) value \
                # ('{}','{}');".format(
                #     log_id,
                #     json.dumps(df_req, ensure_ascii = False).replace('\'','')
                # )

                # self.mdb.WriteToTable(aigc_generator_cmd)
                # response = requests.post(url = self.diffuser_server_url, data = df_req, timeout = self.timeout)
                # res = json.loads(response.text)
                # res = TaskCallback()
                # logging.info("diffuser result: {}".format(res))
                # if res['code'] != 0:
                #     ret_call_dict[c_type] = 6
                # else:
                #     res_url_list = res['url_list']
                #     logging.info("{} with control type {}".format(res['flow_id'], res_url_list))
                #     ret_call_dict[c_type] = res_url_list

                # req = self.df_client.create_request()
                # req.log_id = log_id
                # req.flow_name = "diffusers_engine"

                # req = add_data_item(req, input_data)

                # t_s = time.time()
                # response = self.df_client.serve(req)
                # logging.info("Control type {} cost time {}s".format(c_type, time.time() - t_s))
                # logging.info("Response with control type {}: {}".format(c_type, response))
                
                # if response.code != 0:
                #     ret_call_dict[c_type] = 6
                # else:
                #     for name, data in response.outputs.items():
                #         res_url_list = json.loads(data.data_ref.str_data)
                #         logging.info("{} with control type {}: {}".format(name, c_type, res_url_list))
                    
            # end for loop
            # debug_dict["prompt"] = json.dumps(debug_prompt)
            # return [input_data, ret_call_dict, role_id, debug_dict]