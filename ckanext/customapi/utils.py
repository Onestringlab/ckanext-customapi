import requests
from ckan.model import meta, User

solr_url = "http://solr:8983/solr/ckan/select"

def query_custom(query, params=None):
    """
    Helper function untuk menjalankan query ke database CKAN.
    """
    session = meta.Session
    result = session.execute(query, params or {})
    return result.fetchall()

def query_solr(params):
    """
    Helper function untuk menjalankan query solr.
    """
    response = requests.get(solr_url, params=params)
    response.raise_for_status()
    return response

def get_user_object(username):
    user = User.get(username)
    if user and user.is_active():
        return user
    return None

def get_username(jwt_token, secret_key=None, public_key=None, algorithm="HS256"):
    try:
        key = secret_key if algorithm.startswith("HS") else public_key

        if not key:
            raise ValueError("Secret key or public key must be provided for decoding the token")

        # Decode the JWT token
        decoded_token = jwt.decode(jwt_token, key, algorithms=[algorithm])

        # Extract the preferred_username
        preferred_username = decoded_token.get("preferred_username")

        if not preferred_username:
            raise ValueError("preferred_username is not found in the token payload")

        return preferred_username

    except ExpiredSignatureError:
        raise ValueError("The token has expired")
    except InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
