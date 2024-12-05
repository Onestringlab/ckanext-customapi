from ckan.model import meta

def query_database(query, params=None):
    """
    Helper function untuk menjalankan query ke database CKAN.
    """
    # session = meta.Session
    # result = session.execute(query, params or {})
    # return result.fetchall()
    return query