import logging
from copy import deepcopy

# import pinyin
import boto3


# def translate_fromCh2Pinyin(chn_text):
#     """
#     description: 中文to pinyin，每个字拼音首字母大写，中间无空格
#     return {*}
#     """
#     pinyin_text = pinyin.get(chn_text, format="strip", delimiter=" ")
#     # 每个字拼音首字母大写，中间无空格
#     words = pinyin_text.split(" ")
#     for idx in range(len(words)):
#         word = words[idx]
#         words[idx] = word[0].upper() + word[1:]
#     pinyin_final_text = "".join(words)
#     return pinyin_final_text
# '''
# def translate_fromCh2Eng_raw(chn_text):
#     translate_cn_req_data={
#         'query_cn': chn_text
#     }
#     invalid_word= {'无': 'None', '未知': 'Unknow'}
#     if chn_text not in invalid_word:
#         try:
#             url = 'http://0.0.0.0:7002/translate_ch2en'
#             resp = requests.post(url, data = translate_cn_req_data, timeout= 60)
#             en_text = resp.text
#         except Exception as err:
#             en_text = ''
#             logging.error("translate_fromCh2Eng_raw error: {}, req: {}".format(str(err), chn_text))
#     else:
#         en_text = invalid_word[chn_text]
#     return en_text
#
# def translate_fromEng2Ch_raw(eng_text):
#     translate_en_req_data={
#         'query_en': eng_text
#     }
#     try:
#         url = 'http://0.0.0.0:7002/translate_en2ch'
#         resp = requests.post(url, data = translate_en_req_data, timeout= 60)
#         chn_text = resp.text
#     except Exception as err:
#         chn_text = ''
#         logging.error("translate_fromEng2Ch_raw error: {}, req: {}".format(str(err), eng_text))
#     return chn_text
# '''


def translate_fromCh2Eng_raw(chn_text):
    source_language = "zh"
    target_language = "en"
    translate = boto3.client(service_name='translate', region_name='us-east-1', use_ssl=True)
    try:
        res = translate.translate_text(Text=chn_text, SourceLanguageCode=source_language, TargetLanguageCode=target_language)
        translate_text = res.get('TranslatedText')
        logging.info("ch2eng query: {}, res: {}".format(chn_text, translate_text))
        return translate_text
    except Exception as err:
        logging.error("translate ch2eng failed, query: {}, err: {}".format(chn_text, err))
        return ""

def translate_fromEng2Ch_raw(eng_text):
    source_language = 'en'
    target_language = 'zh'
    translate = boto3.client(service_name='translate', region_name='us-east-1', use_ssl=True)
    try:
        res = translate.translate_text(Text=eng_text, SourceLanguageCode=source_language, TargetLanguageCode=target_language)
        translate_text = res.get('TranslatedText')
        logging.info("eng2ch query: {}, res: {}".format(eng_text, translate_text))
        return translate_text
    except Exception as err:
        logging.error("translate eng2ch failed, query: {}, err: {}".format(eng_text, err))
        return ""

def translate_fromCh2Eng(chn_text, roles_pairs=[]):
    """
    description: 基于角色的翻译，先把中文角色名变成拼音，然后翻译。
    return {*}
    """
    chn_text = deepcopy(chn_text)
    for role_chn, role_pinyin in roles_pairs:
        chn_text = chn_text.replace(role_chn, role_pinyin)

    eng_text = translate_fromCh2Eng_raw(chn_text=chn_text)
    return eng_text

if __name__ == "__main__":
    print(translate_fromCh2Eng_raw("Qing1Nian2 推开自己背后的窗户"))
    print(translate_fromCh2Eng_raw("[青年]"))
