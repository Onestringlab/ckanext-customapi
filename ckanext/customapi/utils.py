
import requests
from ckan.model import meta


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