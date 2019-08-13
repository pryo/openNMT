
import torch
import torch.nn.functional as F
import numpy as np
import json
import logging

from flask import Flask, request,render_template,jsonify
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
app = Flask(__name__)
#models
conf = conf.local.param()
checkpoint = None
decoder = None
encoder = None
word_map = None
rev_word_map  = None
@app.before_first_request
def _load_model():

    global checkpoint
    global decoder
    global encoder
    global device
    global word_map
    global rev_word_map
    checkpoint = torch.load(conf.checkpoint)
    decoder = checkpoint['decoder']
    decoder = decoder.to(device)
    decoder.eval()
    encoder = checkpoint['encoder']
    encoder = encoder.to(device)
    encoder.eval()
    with open(conf.wordmap, 'r') as j:
        word_map = json.load(j)
    rev_word_map = {v: k for k, v in word_map.items()}
    #word_map = json.load(conf.wordmap)
@app.route('/predict',methods=['POST'])
def predict():
    beam = None
    try:
        img_obj = request.files['picture']
    except:
        logging.exception('Error with image upload')
    try:
        beam_arg = request.args['beam_size']
        #beam = request.files['beam_size']
        assert 0<int(beam_arg)<10
        beam = int(beam_arg)
    except:
        logging.exception('Invalid beam input')
        beam = 5
    seq,alphas = caption.caption_image_beam_search(encoder,decoder,img_obj,word_map,beam_size=beam)
    # seq is a list of numbers
    words = [rev_word_map[ind] for ind in seq]
    # words is a list of string

    return jsonify(words)


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