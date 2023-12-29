import logging
import requests
import json

class TruboOpenaiGptClient(object):
    def __init__(self, url=None, timeout=20):
        self.url = url or "http://a902c36a7f8f74f7598f245345559af3-159765183.us-east-1.elb.amazonaws.com:7010/gpt-aigc-gen"
        # self.url = url or "http://0.0.0.0:7002/gpt-aigc-gen"
        # self. url = "http://a902c36a7f8f74f7598f245345559af3-159765183.us-east-1.elb.amazonaws.com:7010/rawgpt"
        self.timeout = timeout
        self.try_count = 3
        
    @staticmethod
    def __call__(self, dialog: str, max_context=0):
        logging.info("__call__ function")
        return ""
    
    def ask_question(self, query):
        header = {
            'accept': 'application/json',
            'Content-Type': 'application/json',
        }
        gpt_request_data = {
            # "query": query
            "prompt": query
            # "clip_res": clip_res
        }
        # print(f"req_data: {gpt_request_data}")
        flag = True
        for i in range(self.try_count):
            try:
                # resp = requests.post(self.url, headers=headers, data = gpt_request_data, timeout= self.timeout)
                resp = requests.post(self.url, data = json.dumps(gpt_request_data), timeout= self.timeout, headers = header)
                resp.raise_for_status()  # 这将在遇到 4xx 或 5xx 响应时抛出 HTTPError
                res = resp.text
                res = json.loads(res)
                flag = True
                # logging.info("req: {} \n \t\t res: {}".format(gpt_request_data, res))
            except requests.exceptions.HTTPError as http_err:
                res = ''
                flag = False
                logging.error("http error: {}, req: {}".format(str(http_err), query))
            except Exception as err:
                res = ''
                flag = False
                logging.error("single chat error: {}, req: {}".format(str(err), query))
            if flag == True:
                break
        return res
    
    def single_chat_test(self, query, 
                        temperature = 0.4, 
                        max_tokens = 4096,
                        response_format = {"type":"text"}
                        ):   
            
            system_prompt = "你善于分析小说和剧本等文案，也深谙动漫和电影拍摄方法，可以专业的回答各种文案分析和拍摄的问题。" 

            if "<SEP>" in query:
                query, system_prompt =  query.split("<SEP>")       

            messages = [{"role": "system", "content": f"{system_prompt}"}, 
                        {"role": "user", "content": query}
                        ]
    
            #logging.info("mycheck")
            #logging.info(str(messages))

            gpt_request_data = {
                "model": "gpt-3.5-turbo-1106", #"gpt-4-1106-preview", #"gpt-3.5-turbo-1106", 
                "response_format": response_format, #{"type":"text"}, #{"type":"json_object"},
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            flag = True
            for i in range(self.try_count):
                
                try:
                    print(self.url)
                    resp = requests.post(self.url, json = gpt_request_data, timeout= self.timeout)
                    res = resp.text
                    flag = True
                except Exception as err:
                    res = ''
                    logging.exception("single chat error: {}, req: {}, try_count: {}".format(str(err), query, i))
                    flag = False
                if flag == True:
                    break
            return res