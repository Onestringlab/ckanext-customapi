from ckan.model import meta

def query_custom(result = session.execute(query, params or {})):
    """
    Helper function untuk menjalankan query ke database CKAN.
    """
    session = meta.Session
    result = session.execute(query, params or {})
    return result.fetchall()
    return query