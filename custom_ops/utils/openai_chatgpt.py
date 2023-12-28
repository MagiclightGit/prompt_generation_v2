import logging
import requests


class TruboOpenaiGptClient(object):
    def __init__(self, url=None, timeout=20):
        self.url = url or "http://a902c36a7f8f74f7598f245345559af3-159765183.us-east-1.elb.amazonaws.com:7010/gpt-aigc-gen"
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
