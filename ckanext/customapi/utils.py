import jwt
import requests

from flask import jsonify
from ckan.model import meta, User
from ckan.logic import get_action

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
    solr_url = "http://solr:8983/solr/ckan/select"
    response = requests.get(solr_url, params=params)
    response.raise_for_status()
    return response

def get_user_object(username):
    user = User.get(username)
    if user and user.is_active():
        return user
    return None

def get_username(jwt_token):
    try:
        # Dekode JWT tanpa memvalidasi signature dan expiration
        decoded_token = jwt.decode(jwt_token, options={"verify_signature": False})

        # Extract the preferred_username
        email = decoded_token.get("email")
        preferred_username = decoded_token.get("preferred_username")

        # Jika sukses, kembalikan decoded token
        return preferred_username,email

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token sudah kedaluwarsa"}), 401
    except jwt.InvalidTokenError as e:
        return jsonify({"error": f"Token tidak valid: {str(e)}"}), 400

def get_profile_by_username(username):
    query = '''
                SELECT id, name, apikey, fullname, email, reset_key, sysadmin, 
                    activity_streams_email_notifications, state, plugin_extras, image_url 
                FROM public.user 
                WHERE name = :username
            '''
    result = query_custom(query, {'username': username})

    # Konversi hasil query menjadi daftar dictionary
    data = [
        {
            "id": row[0],
            "name": row[1],
            "apikey": row[2],
            "fullname": row[3],
            "email": row[4],
            "reset_key": row[5],
            "sysadmin": row[6],
            "activity_streams_email_notifications": row[7],
            "state": row[8],
            "plugin_extras": row[9],
            "image_url": row[10]
        }
        for row in result
    ]
    return data

def has_package_access(id, username):
    params = {'id': id}
    context = {
        'user': username
    }
    try:
        # response = get_action('package_show')(context, params)
        return context
    except Exception as e:
        return context
