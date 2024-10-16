import requests
import json
# def get_cover_url(project_id):
#     headers = {
#         # Already added when you pass json=
#         # 'Content-Type': 'application/json',
#         'Authorization': 'Bearer ca91f7cf432a4d3ec6103497ae331582',
#     }

#     json_data = {
#         'project_ids': [
#             project_id,
#         ],
#     }

#     response = requests.post(
#         'https://rk5qfgtbe2.execute-api.us-east-1.amazonaws.com/text2image.list-by-project',
#         headers=headers,
#         json=json_data,
#     )
#     return response.content

# with open ("/home/magiclight/Projects/qingyun/new_version_test/prior_all_label.txt","r") as f:
#     actioninfo = f.readlines()
#     actioninfo = [line.strip() for line in actioninfo]
# action_dic = {}
# for i in actioninfo:
#     temp = i.split(",")
#     imgid = temp[0]
#     imgid = imgid.split(".")[0]
#     action = temp[4]
#     action_dic[imgid] = action
# print(action_dic)
# print(111)
# with open ("/home/magiclight/Projects/qingyun/111.txt","r") as f:
#     lines = f.readlines()
# print(222)
# count = 0
# for line in lines:
#     try:
#         count+=1
#         line = line.strip()
#         img_id,project_id= line.split(",")
#         print(project_id)
#         data = json.loads(get_cover_url(project_id))
#         url = data["data"][0]["result"]["url"]
#         url = url.replace("0_w","0")

#         action = action_dic[img_id]
#         with open("text.txt","a") as f:
#             f.write(f"{img_id},{url},{action}\n")
#         print(url)
#         print(count)
#         # r = requests.get(url)
#         # with open("/home/magiclight/Projects/qingyun/layout/" + img_id, 'wb') as p:
#         # with open("/home/magiclight/Projects/qingyun/layout/" + project_id +".jpg", 'wb') as p:
#         #     p.write(r.content) 
#     except:
#         with open("/home/magiclight/Projects/qingyun/failed_id_openpose2.txt","a") as f:
#             f.write(f"{project_id}\n")
#         continue
# exit()

from magic.config import config
from magic.task.base import TaskBase
from magic.task.error import TaskError
from magic.logger.magic_logger import get_log_level
from magic.utils.fuzzy_download import fuzzy_download_to_file
from magic.utils.fuzzy_download import fuzzy_download_to_folder
from magic.storage.s3 import default_s3_client
from magic.utils.wrapper import retry_for_requests
import os
# with open("/home/magiclight/Projects/qingyun/new_version_0514_1631/layout_cover.txt","r") as f:
#     lines = f.readlines()
folder_path = "/home/ubuntu/yangel/prompt_generation/古装男"
# count = 0
clothes_type = {}
count = 0
for root,dir,files in os.walk(folder_path):
    # count+=1
    # print(dir)
    # print(count)
    # for i in dir:
    for file in files:
#     print(file)
        # if file.endswith(".png") or file.endswith(".jpg"):
        image_path = os.path.join(root,file)
        # line = line.strip()
        # img_id,project_id = line.split(",")
        output_bucket = "magic-web-server"
        display_key = f'gufeng_clothes_lib/male/{count}.jpg'
        default_s3_client.upload_from_file(
            local_filepath=image_path,
            file_key=display_key,
            bucket=output_bucket,
            content_type="image/jpeg",
        )
        print(f'Upload display image: s3://{output_bucket}/{display_key}')
        count +=1
        # clothes_type[clothes_class] = count
