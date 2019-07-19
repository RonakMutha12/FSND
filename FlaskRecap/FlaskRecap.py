from flask import Flask, request, jsonify, abort

app = Flask(__name__)

greetings = {
            'en': 'hello', 
            'es': 'Hola', 
            'ar': 'مرحبا',
            'ru': 'Привет',
            'fi': 'Hei',
            'he': 'שלום',
            'ja': 'こんにちは'
            }

@app.route('/greeting', methods=['GET'])
def greeting_all():
    return jsonify({'greetings': greetings})

@app.route('/greeting/<lang>', methods=['GET'])
def greeting_one(lang):
    print(lang)
    if(lang not in greetings):
        abort(404)
    return jsonify({'greeting': greetings[lang
    ]})

@app.route('/greeting', methods=['POST'])
def greeting_add():
    info = request.get_json()
    if('lang' not in info or 'greeting' not in info):
        abort(422)
    greetings[info['lang']] = info['greeting']
    return jsonify({'greetings':greetings})

@app.route('/headers', methods=['GET'])
def headers():
    if request.headers.get("Authorization") is None:
        abort(401)
    auth_headers = request.headers.get("Authorization")
    headers_parts = auth_headers.split(" ")
    if len(headers_parts) != 2:
        abort(401)
    if headers_parts[0] != 'Bearer':
        abort(401)
    return headers_parts[1]