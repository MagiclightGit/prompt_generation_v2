import requests
import json
import logging

class TruboOpenaiGptClient(object):
    def __init__(self, 
                url = "http://0.0.0.0:7002/gpt-aigc-gen", 
                timeout = 20):
        self.url = url
        self.timeout = timeout
        self.try_count = 3
        
    @staticmethod
    def __call__(self, dialog: str, max_context=0):
        logging.info("__call__ function")
        return ""
    
    def ask_question(self, query):
        gpt_request_data = {
            "query": query
        }
        flag = True
        for i in range(self.try_count):
            try:
                resp = requests.post(self.url, data = gpt_request_data, timeout= self.timeout)
                res = resp.text
                flag = True
                #logging.info("req: {} \n \t\t res: {}".format(gpt_request_data, res))
            except Exception as err:
                res = ''
                flag = False
                logging.error("single chat error: {}, req: {}".format(str(err), query))
            if flag == True:
                break
        return res
