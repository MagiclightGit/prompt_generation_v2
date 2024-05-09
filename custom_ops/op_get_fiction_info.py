'''
@date    : 2023-11-16 11:32:04
@author  : yangel(fflyangel@foxmail.com)
@brief   :
-----
Last Modified: 2023-11-22 15:49:21
Modified By: yangel(fflyangel@foxmail.com)
-----
@history :
================================================================================
   Date   	 By 	(version) 	                    Comments
----------	----	---------    ----------------------------------------------
================================================================================
Copyright (c) 2023 - 2023 All Right Reserved, MagicLight
'''

# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
import datetime
import traceback
from typing import Dict, NoReturn
import logging

from shlex import quote


class OPIpBibleObtain(object):
    def __init__(
            self,
            project_id: str,
            chid: str,
            para_id: int
    ):
        self.project_id = project_id
        self.chid = chid
        self.para_id = para_id
        
        self.subject_map = {
            "20": "two man",
            "21": "two man",
            "22": "two man",
            "02": "two woman",
            "11": "a man and a woman",
            "12": "a man and a woman",
            "10": "a man",
            "01": "a woman"
        }
        self.subject_map_ = {
            1: "one person",
            2: "two people",
        }
        self.style_map = {
            '现代都市': "现代",
            '末世悬疑': "现代",
            '未来科幻': "现代",
            "中国现代": "现代",
            "古代": "中国古代",
            "西式古代":"西式古代",
            "中国古代":"中国古代",
            "现代":"现代",
            "科幻&未来":"科幻&未来"
        }

    def load_list_field(self, field):
        if type(field) == list:
            return field
        elif type(field) == str:
            return json.loads(field)
        else:
            raise TypeError("current field type error")
        
    def parse_fiction_info(self, fiction_path):

        # 解析prompt
        prompts_data = {}
        with open(fiction_path, "r") as f:
            data = json.load(f)
        chapter_info = data["chapter_info"]
        chapter_style = chapter_info.get("era_cn","")
        style_id = chapter_info.get("style_id","1")
        paras = chapter_info["paras"]
        for para in paras:
            # 查找对应段落id
            if para["para_id"] != self.para_id:
                continue

            # logging.info("para_id: {}, para: {}".format(para['para_id'], para))

            prompts_data["para_content_en"] = para["para_content_en"]
            prompts_data["period"] = chapter_style
            prompts_data["style_id"] = style_id
            prompts_data["action"] = para.get("para_action","")
            

        
            # # 查找场景id
            # scene_id = para["scene_id"]
            # scene = chapter_info["scenes"][scene_id]
            # prompts_data["scene_id"] = scene_id
            # prompts_data["style"] = scene["style"]
            # prompts_data["interior_exterior"] = scene["interior_exterior"]
            # prompts_data["detail_caption_en"] = scene["detail_caption_en"]
            # prompts_data["simple_caption_en"] = scene["simple_caption_en"]

            # 查找人物数量
            num_person = len(para["roles"]) # + len(para["minor_roles"])
            
            max_num_person = 2  # 设定每段中的最大人数
            # logging.info(f"max_num_person: {max_num_person}, {num_person}")

            prompts_data["num_person"] = min(max_num_person, num_person)

            # 加载需要的人物信息
            prompts_data["roles"] = []
            for role in para["roles"]:
                cur_role = {}
                role_id = role["id"]
                cur_role["id"] = role_id
                cur_role["name_list"] = [chapter_info["roles"][role_id]["name"]]
                cur_role["name_list"].extend(self.load_list_field(chapter_info["roles"][role_id]["other_names"]))
                cur_role["actions_en"] = self.load_list_field(role.get("actions_en", []))
                cur_role["emoji_en"] = self.load_list_field(role.get("emoji_en", []))
                cur_role["caption_en"] = role.get("caption_en", "")
                cur_role["gender_en"] = role.get("gender_en", "")
                cur_role["display_prompt"] = role.get("display_prompt","")
                
                prompts_data["roles"].append(cur_role)

            # 获取姿态
            # prompts_data["pose"] = []
            # for role in para["roles"]:
            #     if role["actions"]:
            #         prompts_data["pose"].append(role["actions"])
            # for minor_roles in para["minor_roles"]:
            #     if minor_roles["actions"]:
            #         prompts_data["pose"].append(minor_roles["actions"])

            # 获取场景id，并且加载场景配置
            scene_id = para["scene_id"]
            if scene_id in chapter_info['scenes']:
                load_scene_info = chapter_info['scenes'][scene_id]
                cur_scene = {}
                cur_scene['location_en'] = load_scene_info['location_en']
                cur_scene['weather_en'] = load_scene_info['weather_en']
                cur_scene['style_en'] = load_scene_info['style_en']
                cur_scene['simple_caption_en'] = load_scene_info['simple_caption_en']
                if 'detail_caption_cn_new' in load_scene_info:
                    cur_scene['detail_caption_cn_new'] = load_scene_info['detail_caption_cn_new']
                if 'simple_caption_en_new' in load_scene_info:
                    cur_scene['simple_caption_en_new'] = load_scene_info['simple_caption_en_new']
                cur_scene["environments_cn"] = ", ".join([load_scene_info["location_cn"],
                                                          load_scene_info["interior_exterior_cn"],
                                                          load_scene_info["time_cn"],
                                                          load_scene_info["style_cn"],
                                                          load_scene_info["weather_cn"]])
                # cur_scene["environments_en"] = ", ".join([load_scene_info["location_en"],
                #                                           load_scene_info["interior_exterior_en"],
                #                                           load_scene_info["time_en"],
                #                                           load_scene_info["style_en"],
                #                                           load_scene_info["weather_en"]])
                cur_scene["location"] =load_scene_info["location_en"]
                
                #获取场景类型
                cur_scene["scene_type"] = load_scene_info["scene_type"]
                cur_scene["prompt"] = load_scene_info["prompt"]
                cur_scene["extra_prompt"] = load_scene_info["extra_prompt"]
                cur_scene["extra_prompt_cn"] = load_scene_info["extra_prompt_cn"]
                cur_scene["caption_with_roles_en"] = load_scene_info.get("caption_with_roles_en", "")
                cur_scene["style"] = load_scene_info.get("style_cn","未知")
                cur_scene["display_prompt"] = load_scene_info.get("display_prompt","")
                cur_scene["tags"] = load_scene_info.get("tags","")

                try:
                    cur_scene["subject_en"] = json.loads(load_scene_info["subject_en"])
                except Exception as e:
                    logging.info("Parse 'subject_en' ERROR: {}".format(e))
                    cur_scene["subject_en"] = {}

                prompts_data["scene"] = cur_scene
            
            # add caption
            prompts_data["para_content"] = para["para_content_cn"]

        # logging.info("Parsed ip_bible is {}".format(prompts_data))
        
        return prompts_data

    def parse_fiction_info_for_layout(self, fiction_path, project_id, chid, para_id):

        # 解析prompt
        prompts_data = {}
        with open(fiction_path, "r") as f:
            data = json.load(f)
        chapter_info = data["chapter_info"]
        paras = chapter_info["paras"]
        for para in paras:
            # 查找对应段落id
            if para["para_id"] != para_id:
                continue

            prompts_data["conversation_id"] = para.get("conversation_id", "c_-1")
            prompts_data["project_id"] = project_id
            prompts_data["chapter_id"] = chid
            prompts_data["para_id"] = para_id

            prompts_data["para_content"] = []
            para_content_en = ""
            tmp_para_content_en = para.get("para_content_en", [])
            for item in tmp_para_content_en:
                para_content_en += item
            prompts_data["para_content"].append(para_content_en)

            # 查找场景id
            scene_id = para["scene_id"]
            scene = chapter_info["scenes"][scene_id]
            # prompts_data["style"] = scene.get("style_cn", "未知")
            # ipbible 风格映射
            
            # if(prompts_data["style"]=="中国现代"):
            #     prompts_data["style"] = "现代"
            # if(prompts_data["style"]=="古代"):
            #     prompts_data["style"] = "中国古代"
            ipbible_style = scene.get("style_cn", "未知")
            prompts_data["style"] = self.style_map.get(ipbible_style,"现代")          
            prompts_data["location"] = scene.get("interior_exterior_cn", "室外")

            # 查找人物数量
            # num_person = len(para["roles"]) + len(para["minor_roles"])
            num_person = len(para["roles"])
            prompts_data["num_person"] = num_person
            # logging.info(f"num_person: {num_person}")
            if num_person == 0:
                ret_msg = {
                    "ret": 0,
                    "num_person": num_person,
                    "msg": f"no roles in project_id {project_id}, chid {chid}, para_id {para_id}",
                }
                # raise ValueError(f"no roles in fid {fid}, chid {chid}, para_id {para_id}")
                logging.info(f"{ret_msg}")
                return prompts_data, ret_msg

            # 获取主角人物id
            prompts_data["person_id"] = []

            # 获取姿态及性别
            prompts_data["pose"] = []
            prompts_data["gender"] = {"male":0, "female":0}

            # res = self.get_chatgpt_result(prompts_data["para_content"])
            # try:
            #     res = json.loads(res)
            #     prompts_data["pose"] = res['姿态']
            # except:
            #     logging.error("get chatgpt result err = {}".format(traceback.format_exc()))
            gender_set = {"male","female","unknown"}
            for role in para["roles"]:
                prompts_data["pose"].append(role.get("actions_cn", ""))
                gender_en = role.get("gender_en", "unknown").lower()
                if gender_en not in gender_set:
                    gender_en = "unknown"
                prompts_data["person_id"].append((role["id"],gender_en))
                if gender_en in prompts_data["gender"].keys():
                    prompts_data["gender"][gender_en] += 1
                if gender_en == "unknown":
                    prompts_data["gender"]["male"] += 1
                    prompts_data["gender"]["female"] += 1
                
            # 关键属性查找-动作
            
            # 构建主语
            # subject = self.subject_map.get(str(prompts_data["gender"]["male"]) + str(prompts_data["gender"]["female"]), "")
            # if len(para["roles"]) == 1 and subject == self.subject_map["11"]:
            #     subject = self.subject_map["10"]
            subject  = self.subject_map_.get(num_person, "")
            # 构建谓宾
            verb_object = ""
            for role in para["roles"]:
                actions_en = role.get("actions_en", "\"[]\"")
                # role["actions_en"] is string not list
                # para_content_highlight += (role["actions_en"][2:-2] + ", ")
                # role["actions_en"]为空时索引不会溢出
                verb_object += f"{actions_en[2:-2].lower()}"
                # @世伟优先把和描述相关的动作排在第一，故这里只取第一个动作
                break
            # verb_object = para.get("group_actions", "")
            para_content_highlight = subject + " " + verb_object
            
            # 关键属性查找-场景
            para_content_highlight += f",{scene.get('location_en', '')}"
            prompts_data["para_content"].append(para_content_highlight)

            # for minor_roles in para["minor_roles"]:
            #     if minor_roles["actions_cn"]:
            #         prompts_data["pose"].append(minor_roles["actions_cn"])

            ret_msg = {"ret": 0, "num_person": num_person, "msg": "success"}

        return prompts_data, ret_msg

    def run(self, inputs):
        fiction_info_path, project_id, chid, para_id, flow_id = inputs
        ret_msg = {"ret": 0, "msg": "succ"}
        prompts_data = {}
        layout_data = {}
        try:
            prompts_data = self.parse_fiction_info(fiction_info_path)
            layout_data, _ = self.parse_fiction_info_for_layout(fiction_info_path, project_id, chid, para_id)
        except Exception as err:
            ret_msg["ret"] = 1
            err_info = "fiction parser failed! err: {}".format(str(err)) 
            ret_msg["msg"] = err_info
            logging.error(err_info)
        return [prompts_data, layout_data, ret_msg]