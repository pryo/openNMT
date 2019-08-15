
import requests
import json
if __name__ == '__main__':
    combine_url = 'http://146.148.103.174/caption_translate'

    # files = {'picture':open(input('image path: '),'rb'),'beam_size':input('beam size: ')}
    # files = {'picture': open(input('image path: '), 'rb')}
    # r = requests.post(local_url,params = {'beam_size':input('beam size: ')},
    #                   files=files,timeout=400)
    r= requests.post(combine_url, json=[{"id": 100, "src": "what is this."}])
    print(r.text)