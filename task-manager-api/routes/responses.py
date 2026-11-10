from flask import jsonify, request


def respond(result):
    payload, status = result
    return jsonify(payload), status


def json_body():
    return request.get_json(silent=True)
