"""
Author: guojianyuan
Date: 2023-11-14 13:15:10
Description: 
"""
import time
import json
from custom_ops.op_construct_request import OpConstructRequest
class OpPromptGenerate(OpConstructRequest):
    def __init__(self,
        df_server_url = 'http://0.0.0.0:7001/sd_generator',
        timeout = 300):
        super(OpPromptGenerate, self).__init__(df_server_url, timeout)

    def run(self, flow_id, project_id, chid, para_id, ip_bible, model_info) :
        human_prompts = ""
        env_prompt = ""
        lora_info_dict = {}
        sub_pos_prompts = {}
        # person_prompt = {}
        pos_prompts = {}
        pos_prompts["person_prompt"] = []
        neg_prompts = ""
        # layout = ''
        # base nagative prompt
        # neg_prompt_style = "test"
        model_info = self.pares_model_info(model_info)
        if self.neg_prompt_style == "bright":
            # mengyang neg prompt；效果更加明亮
            base_neg_prompts = "easynegative, (same person: 2.0),(worst quality,low quality:2),(deformed iris:1.4),(deformed pupils:1.4),(poorly drawn face:1.21),(empty eyes:1.4),monochrome,ugly,disfigured,overexposure, watermark,text,bad anatomy,bad hand,extra hands,extra fingers, too many fingers,fused fingers,bad arm,distorted arm,(extra arms:2),fused arms,extra nipples, liquid hand,inverted hand,disembodied limb, oversized head"
        elif self.neg_prompt_style == "dark":
            base_neg_prompts = "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
        elif self.neg_prompt_style == "test":
            base_neg_prompts = "nsfw, text, watermark, (easynegative:1.3), extra fingers,(bad feet:2.0), fewer fingers, low quality, worst quality, watermark,sketch, duplicate, ugly, huge eyes, text, logo, monochrome, worst face, (bad and mutated hands:1.3), (worst quality:2.0), (low quality:2.0), (blurry:2.0), (bad hands), (missing fingers), (multiple limbs:1.2), bad anatomy, (interlocked fingers:1.2), Ugly Fingers, (extra digit and hands and fingers and legs and arms:1.4), (deformed fingers:1.2), (long fingers:1.2),(bad-artist-anime)"
        else:
            base_neg_prompts = "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
        if ip_bible["num_person"] < 1:
            if "scene" in ip_bible:
                env_prompt = "best quality, ultra detailed, anime, {}".format(ip_bible["scene"].get(
                    "prompt", ip_bible["scene"]["simple_caption_en_new"]))
                
            role_id = ""
            single_limit_words = ""

            # add environments_en
            env_prompt = env_prompt + ", " + ip_bible["scene"].get("environments_en", "")
            pos_prompts["env_prompt"] = env_prompt
            
            # 场景链路原文兜底图片
            if ip_bible["scene"]["caption_with_roles_en"] != "":
                sub_pos_prompts["cwr-type"] = "best quality, ultra-detailed, (solo), {}, {}, {}".format(
                    ip_bible["scene"]["caption_with_roles_en"], ip_bible["scene"].get("environments_en", "")+ip_bible["scene"].get("prompt", ""))
            neg_prompts = base_neg_prompts
        else:
            # # 生成设定
            # if layout:
            #     layout = json.loads(layout)
            # else:
            #     layout = []
            
            # # make scene_prompts with ChatGPT
            set_prompt = '根据以下设定回答问题："StableDiffusion是一款利用深度学习的文生图模型，支持通过使用提示词来产生新的图像，描述要包含或省略的元素。 我在这里引入StableDiffusion算法中的Prompt概念，又被称为提示符，每个提示符通常1个单词，有时2到3个单词。 下面的prompt是用来指导AI绘画模型创作图像的。它们包含了图像的各种细节，如人物的外观、背景、颜色和光线效果，以及图像的主题和风格。 以下是用prompt帮助AI模型生成图像的例子：cold , solo, 1girl, detailedeyes, shinegoldeneyes, longliverhair, expressionles, long sleeves, puffy sleeves, white wings, shinehalo, heavymetal, metaljewelry, cross-lacedfootwear, Whitedoves。"'
            trigger_prompt = '问题如下：给出一套详细prompt描述场景"{}"。注意：每个提示符由1-2个单词组成，prompt至少有3个，至多有6个。直接开始给出prompt，不需要用自然语言描述。'.format(
                ip_bible["scene"].get("simple_caption_en_new", ip_bible["para_content"])
            )
            final_prompt = set_prompt + "/n" + trigger_prompt
            chatgpt_try = 0
            while chatgpt_try < 3:
                s = time.time()
                response = self.chatgpt_api_func.ask_question(final_prompt)
                if response != '':
                    break
                else:
                    chatgpt_try += 1
            
            if response == '':
                response = ip_bible["scene"].get("simple_caption_en_new", ip_bible["para_content"])
            
            env_prompt = ','.join(response.split(',')[0:20])
            
            # add environments_en
            env_prompt = ip_bible["scene"].get("environments_en", "") + ", " + ip_bible["scene"].get("prompt", "")+ "," +env_prompt
            # TODO 新增判断逻辑，修改prompt的组成，增加用layout的信息
            # TODO 新增判断逻辑，修改prompt的组成，增加用layout的信息
            if ip_bible["num_person"] == 1:
                try:
                    cur_role_info = ip_bible["roles"][0]

                    # lora 此时不读取lora信息
                    # role_id = cur_role_info["id"]

                    # lora_info, lora_prompts = self.parse_lora_info(model_info[role_id])
                    
                    # lora_info_dict[role_id] = lora_info

                    # # human prompts 用于强化人物的prompts
                    # human_prompts += f"{', '.join(lora_prompts)}, "

                    human_prompts = ""

                    # add some person descriptions from IP bible
                    need_info_keys = ['emoji_en', 'actions_en']
                    for info_key in need_info_keys:
                        info_list = cur_role_info[info_key]
                        if len(info_list) > 0:  
                            info_prompts = [f"({info.lower()}:1.2)" for info in info_list]
                            human_prompts +=  f"{', '.join(info_prompts)}, "
                except Exception:
                    pass

                # # TODO 增加prompts判断和shoot DONE
                human_prompts = f"best quality, ultra_detailed, anime, detailed_face, (solo:2.0), {human_prompts}"

                pos_prompts['env_prompt'] = env_prompt
                role_id = str(ip_bible["roles"][0]["id"])
                person_prompt = {
                    "index": 0,
                    "entity_id": role_id,
                    "prompt": human_prompts
                }
                pos_prompts['person_prompt'].append(person_prompt)

                # 单人链路原文兜底图片
                if ip_bible["scene"]["caption_with_roles_en"] != "":

                    sub_pos_prompts["cwr-type"] = "best quality, ultra-detailed, (solo), {}, {}, {},{}".format(human_prompts,
                            ip_bible["scene"]["caption_with_roles_en"], ip_bible["scene"].get("environments_en", ""),ip_bible["scene"].get("prompt", ""))
                
                single_limit_words = "(2people:2.0), (duplicate:1.2), tiling, multiple people, multiple face"
                # if self.neg_prompt_style == "bright":
                #     # mengyang neg prompt；效果更加明亮
                #     base_neg_prompts = "nsfw,EasyNegativeV2,FastNegativeV2,bad-hands-5,easynegative,negative_hand-neg,ng_deepnegative_v1_75t,(same person: 2.0),(worst quality,low quality:2),(deformed iris:1.4),(deformed pupils:1.4),(poorly drawn face:1.21),(empty eyes:1.4),monochrome,ugly,disfigured,overexposure, watermark,text,bad anatomy,extra hands,extra fingers, too many fingers,fused fingers,bad arm,distorted arm,(extra arms:2),fused arms,extra nipples, liquid hand,inverted hand,disembodied limb, oversized head"
                # elif self.neg_prompt_style == "dark":
                #     base_neg_prompts = "nsfw,EasyNegativeV2,FastNegativeV2,bad-hands-5,easynegative,negative_hand-neg,ng_deepnegative_v1_75t, lowres, bad anatomy, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
                # elif self.neg_prompt_style == "test":
                #     base_neg_prompts = "nsfw,EasyNegativeV2,FastNegativeV2,bad-hands-5,easynegative,negative_hand-neg,ng_deepnegative_v1_75t, text, watermark, (EasyNegativeV2:1.3), extra fingers,(bad feet:2.0), fewer fingers, low quality, worst quality, watermark,sketch, duplicate, ugly, huge eyes, text, logo, monochrome, worst face, (bad and mutated hands:1.3), (worst quality:2.0), (low quality:2.0), (blurry:2.0), (bad-hands-5), (missing fingers), (multiple limbs:1.2), bad anatomy, (interlocked fingers:1.2), Ugly Fingers, (extra digit and hands and fingers and legs and arms:1.4), (deformed fingers:1.2), (long fingers:1.2),(bad-artist-anime)"
                # else:
                #     base_neg_prompts = "nsfw,EasyNegativeV2,FastNegativeV2,bad-hands-5,easynegative,negative_hand-neg,ng_deepnegative_v1_75t, lowres, bad anatomy, bad-hands-5, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
                
                neg_prompts = base_neg_prompts + single_limit_words

            if ip_bible["num_person"] == 2:
                # TODO pos_prompt拼接，由layout拍摄手法, 人物prompt的制作，rp_split_ratio，性别摆放 DONE
                # TODO layout shoot, look (个人的状态), rp_split_ratio DONE
                # TODO 增加表情和动作 DONE
                
                lo_shoot = ""
                people_prmp = {}
                for i, i_role in enumerate(ip_bible["roles"]):
                    role_id = i_role["id"]
                    # 不读取lora信息
                    # lora_info, lora_prompts = self.parse_lora_info(model_info[role_id])
                    lora_prompts = []
                    lora_prompts = self.add_action(lora_prompts, i_role)
                    
                    person_prompt = {
                        "index": i,
                        "entity_id": role_id,
                        "prompt": lora_prompts
                    }
                    pos_prompts['person_prompt'].append(person_prompt)

                    # lora_info_dict[role_id] = lora_info

                # 拼接pos prompt
                env_prompt = "best quality, ultra_detailed, 2people, {}, {}".format(lo_shoot, env_prompt)
                pos_prompts['env_prompt'] = env_prompt
                # pos_prompts['person_prompt'] = people_prmp

                # 多人链路原文兜底图片
                if ip_bible["scene"]["caption_with_roles_en"] != "":
                    cwr_p_prompts = "best quality, ultra_detailed, 2people, {}, {}, {}".format(
                        ip_bible["scene"]["caption_with_roles_en"], ip_bible["scene"].get("environments_en", ""),ip_bible["scene"].get("prompt", ""))
                    
                    sub_pos_prompts["cwr-type"] = cwr_p_prompts

                neg_prompts = base_neg_prompts
                    # object/scenery prompt
        if "object" in ip_bible["scene"]["subject_en"].keys():
            sub_pos_prompts["object"] = "best quality, ultra_detailed, anime" + \
                "({}), (close_up), no people, ".format(ip_bible["scene"]["subject_en"]["object"]) + \
                ip_bible["scene"].get("environments_en", "")

        if "scenery" in ip_bible["scene"]["subject_en"].keys():
            sub_pos_prompts["scenery"] = "best quality, ultra_detailed, anime" + \
                "({}), (scenery), no people, ".format(ip_bible["scene"]["subject_en"]["scenery"]) + \
                ip_bible["scene"].get("environments_en", "") + \
                    ip_bible["scene"].get("prompt", "")
        return [pos_prompts, neg_prompts, sub_pos_prompts] 
    