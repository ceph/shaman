import base64
import hmac

from hashlib import sha1
from pecan import request, abort, response, conf


def basic_auth():
    try:
        auth = request.headers.get('Authorization')
        assert auth
        decoded = base64.b64decode(auth.split(' ')[1]).decode()
        username, password = decoded.split(':')

        assert username == conf.api_user
        assert password == conf.api_key
    except:
        response.headers['WWW-Authenticate'] = 'Basic realm="Shaman :: API"'
        abort(401)

    return True


def github_basic_auth():
    x_hub_signature = request.headers.get('X-Hub-Signature')
    if not x_hub_signature:
        # if this isn't github try basic_auth
        return basic_auth()

    github_secret = conf.github_secret.encode()
    signature = "sha1={}".format(
        hmac.new(github_secret, request.body, sha1).hexdigest()
    )
    if not hmac.compare_digest(x_hub_signature, signature):
        response.headers['WWW-Authenticate'] = 'Basic realm="Shaman :: API"'
        abort(401)

    return True
