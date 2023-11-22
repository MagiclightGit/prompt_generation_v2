'''
@date    : 2023-11-22 16:53:27
@author  : yangel(fflyangel@foxmail.com)
@brief   :
-----
Last Modified: 2023-11-22 17:10:45
Modified By: yangel(fflyangel@foxmail.com)
-----
@history :
================================================================================
   Date   	 By 	(version) 	                    Comments
----------	----	---------    ----------------------------------------------
================================================================================
Copyright (c) 2023 - 2023 All Right Reserved, MagicLight
'''

import requests
import json
import logging

class OPUpDb(object):
    def __init__(
            self
        ):
        self.request_url = "http://test.magiclight.ai/api/image"
        self.header = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }


    def run(self, inputs):
        projectId, fictioId, chapterId, paraId, image_id, image_url, prompt = inputs

        # up to db

        requset_body = [
            {
                "projectId": projectId,
                "chapterId": chapterId,
                "paraId": paraId,
                "layoutInfo": prompt,
                # "imgId": image_id,
                # "type": 1 if image_id else 0,  #类型，0： 段落，1： 图片
                # "data": json.dumps(item, ensure_ascii = False)
            }
        ]
        response = requests.post(self.request_url, headers=self.header, json=requset_body)
        # logging.info(f"db upload result: {response}")
        # sleep?

        return 
