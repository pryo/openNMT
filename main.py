
from onmt.translate import TranslationServer, ServerModelError
import Caption.caption as caption
import logging
import json
from flask import Flask, request,render_template,jsonify
import torch
STATUS_OK = "ok"
STATUS_ERROR = "error"

#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
app = Flask(__name__)
#models
translation_server = None

checkpoint = None
decoder = None
encoder = None
word_map = None
rev_word_map  = None

@app.before_first_request
def _load_model():
    global translation_server
    translation_server = TranslationServer()
    translation_server.start('./available_models/conf.json')
    global checkpoint
    global decoder
    global encoder
    global device
    global word_map
    global rev_word_map
    checkpoint = torch.load('acailable_models/BEST_checkpoint_coco_5_cap_per_img_5_min_word_freq.pth.tar')
    decoder = checkpoint['decoder']
    decoder = decoder.to(device)
    decoder.eval()
    encoder = checkpoint['encoder']
    encoder = encoder.to(device)
    encoder.eval()
    with open('available_models/WORDMAP_coco_5_cap_per_img_5_min_word_freq.json', 'r') as j:
        word_map = json.load(j)
    rev_word_map = {v: k for k, v in word_map.items()}

def prefix_route(route_function, prefix='', mask='{0}{1}'):
    def newroute(route, *args, **kwargs):
        return route_function(mask.format(prefix, route), *args, **kwargs)
    return newroute


def caption():
    # beam = None
    try:
        img_obj = request.files['picture']
    except:
        #report(traceback.format_exc())
        logging.exception('Error with image upload')
        return 'Error with image upload',500
    try:
        beam_arg = request.args['beam_size']
        #beam = request.files['beam_size']
        assert 0<int(beam_arg)<10
        beam = int(beam_arg)
    except:
        #report(traceback.format_exc())
        logging.exception('Invalid beam input')
        beam = 5

    try:
        translate_api = request.args['translate_api']
    except:
        #report(traceback.format_exc())
        logging.exception('no translator api specified, using the one in the conf file')
    seq,alphas = caption.caption_image_beam_search(encoder,decoder,img_obj,word_map,beam_size=beam)
    # seq is a list of numbers
    try:
        words = [rev_word_map[ind] for ind in seq]
    except:
        #report(traceback.format_exc())
        return 'can not get word from seq',500
    # words is a list of string
    try:
        r =translate(words,translate_api)
    except:
        #report(traceback.format_exc())
        return 'translate failed',500
    if r.status_code==500:
        return 'translation server give 500',500
    return r

@app.route('/models', methods=['GET'])
def get_models():
    out = translation_server.list_models()
    return jsonify(out)

@app.route('/health', methods=['GET'])
def health():
    out = {}
    out['status'] = STATUS_OK
    return jsonify(out)
    #return 200

@app.route('/clone_model/<int:model_id>', methods=['POST'])
def clone_model(model_id):
    out = {}
    data = request.get_json(force=True)
    timeout = -1
    if 'timeout' in data:
        timeout = data['timeout']
        del data['timeout']

    opt = data.get('opt', None)
    try:
        model_id, load_time = translation_server.clone_model(
            model_id, opt, timeout)
    except ServerModelError as e:
        out['status'] = STATUS_ERROR
        out['error'] = str(e)
    else:
        out['status'] = STATUS_OK
        out['model_id'] = model_id
        out['load_time'] = load_time

    return jsonify(out)

@app.route('/unload_model/<int:model_id>', methods=['GET'])
def unload_model(model_id):
    out = {"model_id": model_id}

    try:
        translation_server.unload_model(model_id)
        out['status'] = STATUS_OK
    except Exception as e:
        out['status'] = STATUS_ERROR
        out['error'] = str(e)

    return jsonify(out)
@app.route('/caption_translate', methods=['POST'])
def caption_translate():
    try:
        img_obj = request.files['picture']
    except:
        #report(traceback.format_exc())
        logging.exception('Error with image upload')
        return 'Error with image upload',500
    try:
        beam_arg = request.args['beam_size']
        #beam = request.files['beam_size']
        assert 0<int(beam_arg)<10
        beam = int(beam_arg)
    except:
        #report(traceback.format_exc())
        logging.exception('Invalid beam input')
        beam = 5
    seq, alphas = caption.caption_image_beam_search(encoder, decoder, img_obj, word_map, beam_size=beam)
    try:
        words = [rev_word_map[ind] for ind in seq]
    except:
        #report(traceback.format_exc())
        return 'can not get word from seq',500
    string = ' '.join(words)
    out = {}
    inputs = [{"id": 100, "src": string}]
    try:
        translation, scores, n_best, times = translation_server.run(inputs)
        assert len(translation) == len(inputs)
        assert len(scores) == len(inputs)

        out = [[{"src": inputs[i]['src'], "tgt": translation[i],
                 "n_best": n_best,
                 "pred_score": scores[i]}
                for i in range(len(translation))]]
    except ServerModelError as e:
        out['error'] = str(e)
        out['status'] = STATUS_ERROR

    return jsonify(out)
@app.route('/translate', methods=['POST'])
def translate():
    inputs = request.get_json(force=True)
    # print(type(inputs))
    # print(inputs)
    out = {}
    try:
        translation, scores, n_best, times = translation_server.run(inputs)
        assert len(translation) == len(inputs)
        assert len(scores) == len(inputs)

        out = [[{"src": inputs[i]['src'], "tgt": translation[i],
                 "n_best": n_best,
                 "pred_score": scores[i]}
                for i in range(len(translation))]]
    except ServerModelError as e:
        out['error'] = str(e)
        out['status'] = STATUS_ERROR

    return jsonify(out)

@app.route('/to_cpu/<int:model_id>', methods=['GET'])
def to_cpu(model_id):
    out = {'model_id': model_id}
    translation_server.models[model_id].to_cpu()

    out['status'] = STATUS_OK
    return jsonify(out)

@app.route('/to_gpu/<int:model_id>', methods=['GET'])
def to_gpu(model_id):
    out = {'model_id': model_id}
    translation_server.models[model_id].to_gpu()

    out['status'] = STATUS_OK
    return jsonify(out)

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500
if __name__ == '__main__':
    #_load_model()
    app.run(host='127.0.0.1', port=5000, debug=True)