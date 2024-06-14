"""
Author: guojianyuan
Date: 2023-11-14 13:15:10
Description: 
"""
import time
import json
from custom_ops.op_construct_request import OpConstructRequest
from custom_ops.translator import translate_fromCh2Eng_raw, translate_fromEng2Ch_raw
import re
import logging
class OpPromptGenerate(OpConstructRequest):
    def __init__(self,
        df_server_url = 'http://0.0.0.0:7001/sd_generator',
        timeout = 300):
        super(OpPromptGenerate, self).__init__(df_server_url, timeout)
    def contains_chinese(self, text):
        pattern = re.compile(r'[\u4e00-\u9fff]')  # Unicode range for Chinese characters
        return bool(re.search(pattern, text))

    def run(self, flow_id, project_id, chid, para_id, ip_bible, model_info) :
        human_prompts = ""
        env_prompt = ""
        # lora_info_dict = {}
        sub_pos_prompts = {}
        # person_prompt = {}
        pos_prompts = {}
        pos_prompts["person_prompt"] = []
        neg_prompts = ""
        scene_type_xl = ip_bible["scene"]["scene_type"]
        pos_prompts_xl = {}
        pos_prompts_xl["person_prompt"] = []
        neg_prompts_xl = ""
        sub_pos_prompts_xl =  {}
        scene_display_prompt_xl = ""
        common_prompt_xl = ""
        scene_extra_prompt_xl = ""
        scene_extra_prompt_cn_xl = ""
        # layout = ''
        # base nagative prompt
        # neg_prompt_style = "test"
        model_info = self.pares_model_info(model_info)
        if self.neg_prompt_style == "bright":
            # mengyang neg prompt；效果更加明亮
            # base_neg_prompts = "nsfw,easynegative,bad-hands-5,negative_hand-neg, (same person: 2.0),(worst quality,low quality:2),(deformed iris:1.4),(deformed pupils:1.4),(poorly drawn face:1.21),(empty eyes:1.4),monochrome,ugly,disfigured,overexposure, watermark,text,bad anatomy,extra hands,(extra fingers:1.6), (too many fingers:1.6),(fused fingers:1.6),bad arm,distorted arm,(extra arms:2),fused arms,extra nipples, liquid hand,inverted hand,disembodied limb, oversized head"
            base_neg_prompts = "nsfw,easynegative,bad-hands-5,negative_hand-neg, (same person: 2.0),(worst quality,low quality:2),(deformed iris:1.4),(deformed pupils:1.4),(poorly drawn face:1.21),(empty eyes:1.4),monochrome,ugly,disfigured,overexposure, watermark,text,bad anatomy,(extra hands:2),(extra fingers:1.6), (too many fingers:1.6),(fused fingers:1.6),bad arm,distorted arm,(extra arms:2),fused arms,extra legs,deformed legs,extra nipples, liquid hand,inverted hand,disembodied limb, oversized head"
        elif self.neg_prompt_style == "dark":
            base_neg_prompts = "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
        elif self.neg_prompt_style == "test":
            base_neg_prompts = "nsfw, text, watermark, (easynegative:1.3), extra fingers,(bad feet:2.0), fewer fingers, low quality, worst quality, watermark,sketch, duplicate, ugly, huge eyes, text, logo, monochrome, worst face, (bad and mutated hands:1.3), (worst quality:2.0), (low quality:2.0), (blurry:2.0), (bad hands), (missing fingers), (multiple limbs:1.2), bad anatomy, (interlocked fingers:1.2), Ugly Fingers, (extra digit and hands and fingers and legs and arms:1.4), (deformed fingers:1.2), (long fingers:1.2),(bad-artist-anime)"
        else:
            base_neg_prompts = "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"



        #增加ipbible传空值兜底
        # if ip_bible["scene"]["simple_caption_en_new"] == "" and ip_bible["scene"]["prompt"] == "":
        #     if ip_bible["para_content_en"] != "":
        #         ip_bible["scene"]["simple_caption_en_new"] = ip_bible["para_content_en"]
        #         ip_bible["scene"]["prompt"] = ip_bible["para_content_en"]
        #         sub_pos_prompts["cwr-type"] = "best quality, ultra-detailed," + ip_bible["para_content_en"]
        #         sub_pos_prompts["object"] = "best quality, ultra-detailed," + ip_bible["para_content_en"]
        #         sub_pos_prompts["scenery"] = "best quality, ultra-detailed," + ip_bible["para_content_en"]
        #     else:
        #         default_content  = translate_fromCh2Eng_raw(ip_bible["para_content"])
        #         ip_bible["scene"]["simple_caption_en_new"] = default_content
        #         ip_bible["scene"]["prompt"] = default_content
        #         sub_pos_prompts["cwr-type"] = "best quality, ultra-detailed," + default_content
        #         sub_pos_prompts["object"] = "best quality, ultra-detailed," + default_content
        #         sub_pos_prompts["scenery"] = "best quality, ultra-detailed," + default_content
        # #如果ipbible传来的prompt有中文则翻译
        # if self.contains_chinese(ip_bible["scene"]["prompt"]):
        #         ip_bible["scene"]["prompt"] = translate_fromCh2Eng_raw(ip_bible["scene"]["prompt"])

        #表情动作映射：
        emoji_map = {"happy": ",wide smile, raised cheeks, and crow's feet around the eyes,",
                     "sad" :",downturned mouth, drooping eyelids, furrowed brow,",
                     "cry" :",downturned mouth, drooping eyelids, furrowed brow,",
                     "angry":",face flushed, staring, mouth closed,raised eyebrows,",
                     "surprised": ",wide open eyes, a raised brow, big mouth open,",
                     "shocked": ",wide open eyes, a raised brow, big mouth open,",
                     "sleepy": ",drooping eyelids, half-closed eyes, and a slightly dazed expression,",
                     "annoyed": ",mouth turned down slightly, eyes narrowed, and a tense jaw,",
                     "fearful": ",wide-open eyes, a furrowed brow, and a slightly open mouth,"
                     }
        # period_map = {"古代":",(ancient chinese:1.2),(ancient chinese clothes:1.2),",
        #               "现代":"",
        #               "赛博朋克":"(Cyberpunk atmosphere:1.2), (futuristic style:1.2),",
        #               "星际":"(interstellar style:1.2),(futuristic style:1.2),"}

        style_id = ip_bible["style_id"]
        scene_type = ip_bible["scene"]["scene_type"]
        para_action = ip_bible["action"]

        #风格提示词：
        common_prompt = ""
        common_neg_promt = ""
        base_neg_prompts_xl = ""
        #动漫未来
        if style_id == "4":
            common_prompt = "best quality, ultra_detailed,(Cyberpunk atmosphere:1.2), (futuristic style:1.2),"
        #动漫星际
        elif style_id == "星际":
            common_prompt = "best quality, ultra_detailed,(interstellar style:1.2),(futuristic style:1.2),"
        #动漫末世
        elif style_id == "1":
            common_prompt = "best quality, ultra_detailed,(dark style:1.4),(gloomy atmosphere:1.4),"
        #Magicmix
        elif style_id == "6":
            common_prompt = "best quality, ultra_detailed,(realistic:1.2),(photorealistic:1.2),"
            common_neg_promt = "anime,comic,"
            # if ip_bible["period"] in period_map:
            #     common_prompt = common_prompt + period_map[ip_bible["period"]]
        #古风
        elif style_id == "8":
            common_prompt = "best quality, ultra_detailed,(chinese style:1.2), (ancient chinese:1.2),"
            common_neg_promt = "(text),(water mark:1.4),"
        #SDXL动漫
        elif style_id == "10":
            base_neg_prompts = "nsfw,aidxlv05_neg, FastNegative,unaestheticXL2v10,lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name"
            common_prompt = "best quality, ultra_detailed,comic,line art style,simple background,"
            # if ip_bible["period"] in period_map:
            #     common_prompt = common_prompt + period_map[ip_bible["period"]]
        #SDXL动漫c
        elif style_id == "11":
            base_neg_prompts = "nsfw,aidxlv05_neg, FastNegative,unaestheticXL2v10,lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name"
            common_prompt = "best quality, ultra_detailed, masterpiece, 8k,(anime style:1.2),"
        #SDXL写实
        elif style_id == "12":
            base_neg_prompts = "noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            # common_prompt = "f1.8, cinematic lighting, realistic style,"
            common_prompt = "f1.8, realistic style,"
        #手绘插画风
        elif style_id == "21":
            common_prompt = "best quality,masterpiece,ultra high res,delicate eyes,childpaiting,crayon drawing,"
            base_neg_prompts = "(negative_hand-neg:1.2),(((bad-hands-5))),EasyNegative,"
        #Magicmix2
        elif style_id == "13":
            common_prompt = "(ultra-detailed,CG ,unity ,8k wallpaper),(masterpiece),(realistic),(photorealistic:1.2),"
            base_neg_prompts = "ng_deepnegative_v1_75t, (badhandv4:1.2), (same person: 2.0), (worst quality:2), (low quality:2), (normal quality:2), lowres, bad anatomy, bad hands, ((monochrome)), ((grayscale)) watermark, moles"
        #写实juggernaut
        elif style_id == "7":
            common_prompt = " (highly detailed),(HDR),intricately detailed,high contrast,highres,absurdres,hyper realistic,8K UHD DSLR,Fujifilm XT3,"
            base_neg_prompts = "(worst quality, low quality, normal quality, lowres, low details, same person ,oversaturated, undersaturated, overexposed, underexposed, grayscale, bw, bad photo, bad photography, bad art)++++, (watermark, signature, text font, username, error, logo, words, letters, digits, autograph, trademark, name)+, (blur, blurry, grainy), morbid, ugly, asymmetrical, mutated malformed, mutilated, poorly lit, bad shadow, draft, cropped, out of frame, cut off, censored, jpeg artifacts, out of focus, glitch, duplicate, (airbrushed, cartoon, anime, semi-realistic, cgi, render, blender, digital art, manga, amateur)++, (3D ,3D Game, 3D Game Scene, 3D Character), (bad hands, bad anatomy, bad body, bad face, bad teeth, bad arms, bad legs, deformities)++"
        #写实XL
        elif style_id == "23":
            common_prompt_xl = "f1.8,relistic,cinematic style,"
            base_neg_prompts_xl = "noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,(realistic:1.2),(photorealistic:1.2),"
            common_neg_promt = "anime,comic,"
            if ip_bible["period"] == "星际":
                common_prompt_xl = "Cyberpunk atmosphere, futuristic style,"
        #迪士尼XL
        elif style_id == "24":
            common_prompt_xl = "f1.8, pixar style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed, pixar style, masterpiece,"
        #动漫现代XL
        elif style_id == "25":
            common_prompt = "best quality, ultra_detailed,anime,"
            common_prompt_xl = "f1.8, anime style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        #日式动漫XL
        elif style_id == "26":
            common_prompt = "best quality, ultra_detailed,"
            common_prompt_xl = "f1.8, Japanese Anime Style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        #动漫未来XL
        elif style_id == "27":
            common_prompt = "best quality, ultra_detailed,(Cyberpunk atmosphere:1.2),(interstellar style:1.2),(futuristic style:1.2),"
            common_prompt_xl = "f1.8, anime style,"
            # base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            base_neg_prompts_xl = "ugly, realism, photorealistic, historical, medieval,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        #动漫末世XL
        elif style_id == "28":
            common_prompt = "best quality, ultra_detailed,anime,(dark style:1.4),(gloomy atmosphere:1.4),"
            common_prompt_xl = "f1.8, anime style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        #美漫风XL
        elif style_id == "29":
            common_prompt = "best quality, ultra_detailed, comic art,"
            common_prompt_xl = "f1.8, comic,"
            base_neg_prompts_xl = "photograph,realistic, stock photo,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        #古风XL
        elif style_id == "30":
            common_prompt = "best quality, ultra_detailed,(chinese style:1.2), (ancient chinese:1.2),"
            common_prompt_xl = "f1.8, anime,chinese style,chinese ancient,"
            base_neg_prompts_xl = "photograph,realistic, stock photo,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        #简约XL
        elif style_id == "31":
            common_prompt = "best quality, ultra_detailed,"
            common_prompt_xl = "f1.8, Tiktok Comic Style,"
            base_neg_prompts_xl = "photograph,realistic, stock photo,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        #粘土风
        elif style_id == "32" or style_id == "36":
            common_prompt = "best quality, ultra_detailed,"
            common_prompt_xl = "f1.8, Clay Style,"
            base_neg_prompts_xl = "photograph,realistic, stock photo,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        elif style_id == "33":
            common_prompt = "best quality, ultra_detailed,"
            common_prompt_xl = "f1.8, Colorful Line Drawing Style,"
            base_neg_prompts_xl = "photograph,realistic, stock photo,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
        elif style_id == "34":
            common_prompt = "best quality, ultra_detailed,"
            common_prompt_xl = "f1.8, Edgerunner Style,"
            # base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            base_neg_prompts_xl = "ugly,photograph,realistic, stock photo,,historical, medieval,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"    
        elif style_id == "37":
            common_prompt_xl = "f1.8, pixar style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        elif style_id == "39":
            common_prompt_xl = "f1.8, Chinese Horror Comic Style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        elif style_id == "40":
            common_prompt_xl = "f1.8,magiclight animee style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        elif style_id == "41":
            common_prompt_xl = "f1.8,relistic,cinematic style,Dune movie style"
            base_neg_prompts_xl = "noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
            common_neg_promt = "anime,comic,"
        elif style_id == "42":
            common_prompt_xl = "f1.8,Shan Hai Style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        elif style_id == "43":
            common_prompt_xl = "f1.8,Genshin Style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        elif style_id == "44":
            common_prompt_xl = "f1.8,league of legends style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        elif style_id == "45":
            common_prompt_xl = "f1.8,ku18 comic style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        elif style_id == "46":
            common_prompt_xl = "f1.8,Dream Comic style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        elif style_id == "47":
            common_prompt_xl = "f1.8,rick and morty style,"
            base_neg_prompts_xl = "realistic,noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed"
            common_prompt = "best quality, ultra_detailed,"
        else:
            common_prompt = "best quality, ultra_detailed,(anime:1.2),"
        base_neg_prompts_xl = "nsfw,text,watermark," + base_neg_prompts_xl
        #display_prompt
        scene_display_prompt = ip_bible["scene"]["display_prompt"]
        scene_display_prompt_xl = ip_bible["scene"]["display_prompt"]
        role_display_prompt = ip_bible["scene"]["role_display_prompt"]
        #extra_prompt
        scene_extra_prompt = ip_bible["scene"]["extra_prompt"]
        scene_extra_prompt_xl = ip_bible["scene"]["extra_prompt"]
        scene_extra_prompt_cn = ip_bible["scene"]["extra_prompt_cn"]
        scene_extra_prompt_cn_xl = ip_bible["scene"]["extra_prompt_cn"]
        #tags
        scene_tags = ip_bible["scene"]["tags"]
        temp_prompt = ""
        if scene_tags == "#AI角色拜年":
            temp_prompt = "happy,(chinese new year:1.2),"
        common_prompt = common_prompt + temp_prompt

        #simple caption 直译的环境
        trans_env_prompt = ip_bible["scene"]["prompt"]

        #分析的环境
        # processed_env_prompt = ip_bible["scene"]["prompt"]
        processed_env_prompt = ip_bible["scene"]["prompt"]
        #场景链路
        xl_style_id = ["23","24","25","26","27","28","29","30","31","32","33","34","36","37","39","40","41","42","43","44","45","46","47"]
        if ip_bible["num_person"] < 1:
              # make scene_prompts with ChatGPT
            # set_prompt = '根据以下设定回答问题："StableDiffusion是一款利用深度学习的文生图模型，支持通过使用提示词来产生新的图像，描述要包含或省略的元素。 我在这里引入StableDiffusion算法中的Prompt概念，又被称为提示符，每个提示符通常1个单词，有时2到3个单词。 下面的prompt是用来指导AI绘画模型创作图像的。它们包含了图像的各种细节，如人物的外观、背景、颜色和光线效果，以及图像的主题和风格。 以下是用prompt帮助AI模型生成图像的例子：cold , solo, 1girl, detailed eyes, shine golden eyes, long liver hair, expressionles, long sleeves, puffy sleeves, white wings, shinehalo, heavymetal, metaljewelry, cross-lacedfootwear, Whitedoves。"'
            # trigger_prompt = '问题如下：给出一套详细中文描述场景"{}"。注意：每个提示符由1-2个单词组成，prompt至少有3个，至多有6个。直接开始给出英文prompt，不需要用自然语言描述。'.format(
            #     ip_bible["para_content"] + '\n 请采用json格式返回：{"prompt": [] }，例子如下：{"prompt": [ "old house","sunny", "sea view", "many children" ] }')
            # final_prompt =set_prompt + trigger_prompt
            # chatgpt_try = 0
            # response = ''
            # while chatgpt_try < 3:
            #     s = time.time()
            #     response = self.chatgpt_api_func.ask_question(final_prompt)
            #     logging.info(f"response: {response}")
            #     if response != '':
            #         break
            #     else:
            #         chatgpt_try += 1
            # if response == '':
            #     response = ip_bible["scene"]["prompt"]
            # if isinstance(response,dict):
            #     env_prompt = ','.join(response.get("prompt",[])[0:20])
            # # add environments_en
            # if len(env_prompt) ==0:
            #     logging.info(f"env_prompt is EMPTY")
            #     env_prompt = ip_bible["scene"]["prompt"]

            # if "scene" in ip_bible:
            #     # env_prompt = "best quality, ultra detailed, anime, {},{}".format(ip_bible["scene"].get(
            #     #     "prompt", ip_bible["scene"]["simple_caption_en_new"]),people_or_not)
            #     env_prompt = "{}{}".format(common_prompt,ip_bible["scene"]["prompt"])
                
            # env_prompt = processed_env_prompt
            env_prompt = trans_env_prompt
            env_prompt = env_prompt.lower()
            words_to_remove = ["girl's","girls'","girl","boy's","boys'","boy ","males'","male's","male ","females'","female's","female","man's","man ","woman's","woman "]
            for phrase in words_to_remove:
                env_prompt = env_prompt.replace(phrase, '')
            

            if style_id == "12":
                env_prompt = ip_bible["scene"]["prompt"]
            # add environments_en
            # env_prompt = env_prompt + ", " + ip_bible["scene"].get("environments_en", "")
            pos_prompts["env_prompt"] = env_prompt
            
            if style_id in xl_style_id:
                pos_prompts["env_prompt"] = env_prompt
                # pos_prompts_xl["env_prompt"] = ip_bible["scene"]["location_en"]
                pos_prompts_xl["env_prompt"] = ip_bible["scene"]["prompt"]

            # 场景链路原文兜底图片
            # if ip_bible["scene"]["simple_caption_en_new"] != "":
            #     sub_pos_prompts["cwr-type"] = "best quality, ultra-detailed,{}, {}, {}, {}".format(
            #         people_or_not,ip_bible["scene"]["simple_caption_en_new"], ip_bible["scene"].get("environments_en", ""),ip_bible["scene"].get("prompt", ""))



            # if ip_bible["scene"]["simple_caption_en_new"] != "":
            #     sub_pos_prompts["cwr-type"] =env_prompt
            #     if style_id in xl_style_id:
            #         # sub_pos_prompts_xl["cwr-type"] =ip_bible["scene"]["location_en"]
            #         sub_pos_prompts_xl["cwr-type"] =ip_bible["scene"]["prompt"]


            neg_prompts = common_neg_promt + base_neg_prompts
            neg_prompts_xl = base_neg_prompts_xl
        else:
            # # 生成设定
            # if layout:
            #     layout = json.loads(layout)
            # else:
            #     layout = []
            
            # # make scene_prompts with ChatGPT
            # set_prompt = '根据以下设定回答问题："StableDiffusion是一款利用深度学习的文生图模型，支持通过使用提示词来产生新的图像，描述要包含或省略的元素。 我在这里引入StableDiffusion算法中的Prompt概念，又被称为提示符，每个提示符通常1个单词，有时2到3个单词。 下面的prompt是用来指导AI绘画模型创作图像的。它们包含了图像的各种细节，如人物的外观、背景、颜色和光线效果，以及图像的主题和风格。 以下是用prompt帮助AI模型生成图像的例子：cold , solo, 1girl, detailed eyes, shine golden eyes, long liver hair, expressionles, long sleeves, puffy sleeves, white wings, shinehalo, heavymetal, metaljewelry, cross-lacedfootwear, Whitedoves。"'
            # trigger_prompt = '问题如下：给出一套详细prompt描述场景"{}"。注意：每个提示符由1-2个单词组成，prompt至少有3个，至多有6个。直接开始给出prompt，不需要用自然语言描述。'.format(
            #     ip_bible["scene"].get("simple_caption_en_new", ip_bible["para_content"]) + '\n 请采用以下json格式返回：{"prompt": [ "diminterior", "dampinterior", "oldhouse", "stormynight" ] }'
            # )
            # final_prompt = set_prompt + "/n" + trigger_prompt
            # chatgpt_try = 0
            # while chatgpt_try < 3:
            #     s = time.time()
            #     response = self.chatgpt_api_func.ask_question(final_prompt)
            #     logging.info(f"response: {response}")
            #     if response != '':
            #         break
            #     else:
            #         chatgpt_try += 1

            # if response == '':
            #     response = ip_bible["scene"].get("simple_caption_en_new", ip_bible["para_content"])

            # if isinstance(response,dict):
            #     env_prompt = ','.join(response.get("prompt",[])[0:20])
            # # add environments_en
            # if len(env_prompt) ==0:
            #     logging.info(f"env_prompt is EMPTY")

            # env_prompt = ip_bible["scene"].get("environments_en", "") + ", " + ip_bible["scene"].get("prompt", "")+ "," +env_prompt
            env_prompt = processed_env_prompt
            
            
            env_prompt = env_prompt.lower()
            # remove gender information
            words_to_remove = ["girl's","girls'","girl","boy's","boys'","boy","males'","male's","male","females'","female's","female","man's","man","woman's","woman"]
            for phrase in words_to_remove:
                env_prompt = env_prompt.replace(phrase, '')

            if style_id == "12":
                    env_prompt = ip_bible["scene"]["prompt"]
            if style_id in xl_style_id:
                # env_prompt_xl = ip_bible["scene"]["location_en"]
                env_prompt_xl = ip_bible["scene"]["prompt"]
            # TODO 新增判断逻辑，修改prompt的组成，增加用layout的信息
            # TODO 新增判断逻辑，修改prompt的组成，增加用layout的信息
            if ip_bible["num_person"] == 1:
                display_prompt = ""
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
                    # 表情description
                    if style_id in ["6","12","7","13","23"]:
                        emoji = cur_role_info["emoji_en"][0]
                        if emoji in emoji_map:
                            human_prompts = emoji + emoji_map[emoji]
                        elif emoji == "":
                            human_prompts = ""
                        else:
                            human_prompts = f"{emoji},"
                        action = cur_role_info['actions_en']
                        if len(action) > 0:
                            info_prompts = [f"{info.lower()}," for info in action if info != ""]
                            human_prompts += f"{', '.join(info_prompts)} "
                            # human_prompts = ""
                    else:
                        emoji = cur_role_info["emoji_en"][0]
                        if emoji in emoji_map:
                            human_prompts = emoji + emoji_map[emoji]
                        elif emoji == "":
                            human_prompts = ""
                        else:
                            human_prompts = f"({emoji}:1.2),"
                        #动作description
                        action = cur_role_info['actions_en']
                        if len(action) > 0:
                            info_prompts = [f"({info.lower()}:1.2)," for info in action if info != ""]
                            human_prompts += f"{', '.join(info_prompts)} "

                    display_prompt = cur_role_info["display_prompt"]
                    # need_info_keys = ['emoji_en', 'actions_en']
                    # for info_key in need_info_keys:
                    #     info_list = cur_role_info[info_key]
                    #     if len(info_list) > 0:  
                    #         info_prompts = [f"({info.lower()}:1.2)," for info in info_list if info != ""]``
                    #         human_prompts +=  f"{', '.join(info_prompts)} "
                    
                except Exception:
                    pass

                # # TODO 增加prompts判断和shoot DONE
                # human_prompts = f"best quality, ultra_detailed, anime, detailed_face, (solo:2.0), {human_prompts}"
                # base_prompt = "best quality, ultra_detailed, anime"
                # human_prompts = f"detailed_face,{human_prompts}"
                pos_prompts['env_prompt'] =ip_bible["scene"]["prompt"]
                if style_id == "12":
                    pos_prompts['env_prompt'] = ip_bible["scene"]["prompt"]
                if style_id in xl_style_id:
                    pos_prompts['env_prompt'] = env_prompt
                    pos_prompts_xl['env_prompt'] = env_prompt_xl
                role_id = str(ip_bible["roles"][0]["id"])
                person_prompt = {
                    "index": 0,
                    "entity_id": role_id,
                    "prompt": human_prompts,
                    "display_prompt": display_prompt
                }
                pos_prompts['person_prompt'].append(person_prompt)
                if style_id in xl_style_id:
                    pos_prompts_xl['person_prompt'] = 'person_prompt'

                # 单人链路原文兜底图片
                # if ip_bible["scene"]["simple_caption_en_new"] != "":
                #     # sub_pos_prompts["cwr-type"] = "{}{},{}".format(common_prompt,human_prompts,ip_bible["scene"]["prompt"])
                #     sub_pos_prompts["cwr-type"] =ip_bible["scene"]["prompt"]
                
                if style_id == "12":
                    sub_pos_prompts["cwr-type"] = ip_bible["scene"]["prompt"]
                if style_id in xl_style_id:
                    sub_pos_prompts["cwr-type"] = env_prompt
                    sub_pos_prompts_xl["cwr-type"] = env_prompt_xl
                # single_limit_words = "(2people:2.0), (duplicate:1.2), tiling, multiple people, multiple face"
                # if self.neg_prompt_style == "bright":
                #     # mengyang neg prompt；效果更加明亮
                #     base_neg_prompts = "nsfw,EasyNegativeV2,FastNegativeV2,bad-hands-5,easynegative,negative_hand-neg,ng_deepnegative_v1_75t,(same person: 2.0),(worst quality,low quality:2),(deformed iris:1.4),(deformed pupils:1.4),(poorly drawn face:1.21),(empty eyes:1.4),monochrome,ugly,disfigured,overexposure, watermark,text,bad anatomy,extra hands,extra fingers, too many fingers,fused fingers,bad arm,distorted arm,(extra arms:2),fused arms,extra nipples, liquid hand,inverted hand,disembodied limb, oversized head"
                # elif self.neg_prompt_style == "dark":
                #     base_neg_prompts = "nsfw,EasyNegativeV2,FastNegativeV2,bad-hands-5,easynegative,negative_hand-neg,ng_deepnegative_v1_75t, lowres, bad anatomy, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
                # elif self.neg_prompt_style == "test":
                #     base_neg_prompts = "nsfw,EasyNegativeV2,FastNegativeV2,bad-hands-5,easynegative,negative_hand-neg,ng_deepnegative_v1_75t, text, watermark, (EasyNegativeV2:1.3), extra fingers,(bad feet:2.0), fewer fingers, low quality, worst quality, watermark,sketch, duplicate, ugly, huge eyes, text, logo, monochrome, worst face, (bad and mutated hands:1.3), (worst quality:2.0), (low quality:2.0), (blurry:2.0), (bad-hands-5), (missing fingers), (multiple limbs:1.2), bad anatomy, (interlocked fingers:1.2), Ugly Fingers, (extra digit and hands and fingers and legs and arms:1.4), (deformed fingers:1.2), (long fingers:1.2),(bad-artist-anime)"
                # else:
                #     base_neg_prompts = "nsfw,EasyNegativeV2,FastNegativeV2,bad-hands-5,easynegative,negative_hand-neg,ng_deepnegative_v1_75t, lowres, bad anatomy, bad-hands-5, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
                
                neg_prompts = common_neg_promt + base_neg_prompts
                neg_prompts_xl = base_neg_prompts_xl
            if ip_bible["num_person"] == 2:
                # TODO pos_prompt拼接，由layout拍摄手法, 人物prompt的制作，rp_split_ratio，性别摆放 DONE
                # TODO layout shoot, look (个人的状态), rp_split_ratio DONE
                # TODO 增加表情和动作 DONE
                
                # lo_shoot = ""
                # people_prmp = {}
                if style_id in ["6","12","7","13","23"]:
                    for i, i_role in enumerate(ip_bible["roles"]):
                        role_id = i_role["id"]
                        lora_prompts = []
                        lora_prompts = self.add_action_realistic(lora_prompts, i_role)
                        display_prompt = i_role["display_prompt"]
                        person_prompt = {
                            "index": i,
                            "entity_id": role_id,
                            "prompt": lora_prompts,
                            "display_prompt" : display_prompt
                        }
                        pos_prompts['person_prompt'].append(person_prompt)
                else:
                    for i, i_role in enumerate(ip_bible["roles"]):
                        role_id = i_role["id"]
                        # 不读取lora信息
                        # lora_info, lora_prompts = self.parse_lora_info(model_info[role_id])
                        lora_prompts = []
                        lora_prompts = self.add_action(lora_prompts, i_role)
                        display_prompt = i_role["display_prompt"]
                        person_prompt = {
                            "index": i,
                            "entity_id": role_id,
                            "prompt": lora_prompts,
                            "display_prompt" : display_prompt

                        }
                        pos_prompts['person_prompt'].append(person_prompt)
                if style_id in xl_style_id:
                    pos_prompts_xl['person_prompt'] = pos_prompts['person_prompt']
                    # lora_info_dict[role_id] = lora_info

                # 拼接pos prompt
                # env_prompt = "best quality, ultra_detailed, 2people, {}, {}".format(lo_shoot, env_prompt)
                pos_prompts['env_prompt'] = ip_bible["scene"]["prompt"]
                # pos_prompts['person_prompt'] = people_prmp
                if style_id == "12":
                    pos_prompts['env_prompt'] = ip_bible["scene"]["prompt"]
                if style_id in xl_style_id:
                    pos_prompts['env_prompt'] = env_prompt
                    pos_prompts_xl['env_prompt'] = env_prompt_xl
                # 多人链路原文兜底图片
                # if ip_bible["scene"]["simple_caption_en_new"] != "":
                #     cwr_p_prompts = "best quality, ultra_detailed, 2people, {}, {}, {}".format(
                #         ip_bible["scene"]["simple_caption_en_new"], ip_bible["scene"].get("environments_en", ""),ip_bible["scene"].get("prompt", ""))


                # if ip_bible["scene"]["simple_caption_en_new"] != "":
                #     # cwr_p_prompts = "{}{}".format(common_prompt,ip_bible["scene"]["prompt"])
                #     sub_pos_prompts["cwr-type"]  =ip_bible["scene"]["prompt"]   
            

                if style_id == "12":
                    sub_pos_prompts["cwr-type"] = ip_bible["scene"]["prompt"]
                if style_id in xl_style_id:
                    sub_pos_prompts["cwr-type"] = env_prompt
                    sub_pos_prompts_xl["cwr-type"] = env_prompt_xl
                neg_prompts = common_neg_promt + base_neg_prompts
                neg_prompts_xl = base_neg_prompts_xl
                # object/scenery prompt
        # if "object" in ip_bible["scene"]["subject_en"].keys():
        #     sub_pos_prompts["object"] = "best quality, ultra_detailed, anime," + \
        #         "({}), (close_up), ".format(ip_bible["scene"]["subject_en"]["object"]) + \
        #         ip_bible["scene"].get("environments_en", "")

        # if "scenery" in ip_bible["scene"]["subject_en"].keys():
        #     sub_pos_prompts["scenery"] = "best quality, ultra_detailed, anime," + \
        #         "({}), (scenery), {}, ".format(ip_bible["scene"]["subject_en"]["scenery"],people_or_not) + \
        #         ip_bible["scene"].get("environments_en", "") + \
        #             ip_bible["scene"].get("prompt", "")
        # env_prompt = common_prompt + trans_env_prompt
        env_prompt = processed_env_prompt
        # if style_id == "12":
        #     env_prompt = ip_bible["scene"]["prompt"]
        if "scenery" in ip_bible["scene"]["subject_en"].keys():
            # sub_pos_prompts["scenery"] = "(wide-shot), " + common_prompt + ip_bible["scene"]["prompt"]
            sub_pos_prompts["scenery"] = "wide shot," + env_prompt
        if style_id == "12":
            sub_pos_prompts["scenery"] = ip_bible["scene"]["prompt"]
        if style_id in xl_style_id:
            sub_pos_prompts["scenery"] =ip_bible["scene"]["prompt"]
            # sub_pos_prompts_xl["scenery"] =ip_bible["scene"]["location_en"]
            sub_pos_prompts_xl["scenery"] =ip_bible["scene"]["prompt"]
        return [pos_prompts, neg_prompts, sub_pos_prompts, scene_display_prompt, common_prompt, scene_tags, scene_type, scene_extra_prompt, scene_extra_prompt_cn, pos_prompts_xl, neg_prompts_xl, sub_pos_prompts_xl, scene_display_prompt_xl, common_prompt_xl, scene_type_xl, scene_extra_prompt_xl, scene_extra_prompt_cn_xl,para_action,style_id,role_display_prompt]
