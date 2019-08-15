import requests
import json
if __name__ == '__main__':
    local_url = ' http://0.0.0.0:5000/translate'
    google_url = 'http://104.198.205.153:80/translate'

    # files = {'picture':open(input('image path: '),'rb'),'beam_size':input('beam size: ')}
    # files = {'picture': open(input('image path: '), 'rb')}
    # r = requests.post(local_url,params = {'beam_size':input('beam size: ')},
    #                   files=files,timeout=400)
    r= requests.post(google_url, json=[{"id": 100, "src": "what is this."}])
    print(r.text)