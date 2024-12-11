import jwt
import requests

from flask import jsonify
from ckan.model import meta, User
# from ckan.logic import get_action
from ckan.auth import get_action
from ckan.model import Package, User, Organization, Member

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

def get_username_capacity(username, organization_name=None):
    # Query menggunakan parameterized query untuk keamanan
    query = '''
        SELECT 
            u.name AS user_name, 
            u.id AS user_id, 
            g.title AS organization_title,
            g.name AS organization_name, 
            m.capacity
        FROM "member" m
        JOIN "user" u ON m.table_id = u.id
        JOIN "group" g ON m.group_id = g.id
        WHERE 
            m.state = 'active' 
            AND g.type = 'organization'
            AND u.name = :username
    '''

    if organization_name:
        query += ' AND organization_name = :organization_name'
        result = query_custom(query, {'username': username,'organization_name': organization_name})
    
    result = query_custom(query, {'username': username})

    # Konversi hasil query menjadi daftar dictionary
    data = [
        {
            "user_name": row[0],
            "user_id": row[1],
            "organization_title": row[2],
            "organization_name": row[3],
            "capacity": row[4]
        }
        for row in result
    ]

    return data

def has_package_access(user_id, dataset_id):
    """
    Fungsi untuk memeriksa hak akses pengguna terhadap dataset.
    
    Args:
        user_id (str): ID pengguna yang ingin diperiksa aksesnya.
        dataset_id (str): ID dataset yang akan diperiksa.
    
    Returns:
        bool: True jika akses diberikan, False jika akses ditolak.
    """
    # Mendapatkan pengguna berdasarkan user_id
    user = User.get(user_id)

    if not user:
        raise ValueError(f"User dengan ID {user_id} tidak ditemukan.")
    
    # Ambil dataset berdasarkan ID
    dataset = Package.get(dataset_id)

    if not dataset:
        raise ValueError(f"Dataset dengan ID {dataset_id} tidak ditemukan.")
    
    # Jika dataset bersifat public, beri akses
    if dataset.is_public():
        return True
    
    # Jika pengguna adalah sysadmin, beri akses
    if user.sysadmin:
        return True
    
    # Jika pengguna adalah creator dari dataset, beri akses
    if user.id == dataset.creator_user_id:
        return True
    
    # Jika dataset private, cek kapasitas user di organisasi terkait
    if not dataset.is_public():
        # Ambil organisasi dari dataset
        organization_id = dataset.owner_org
        if organization_id:
            # Ambil organisasi
            organization = Organization.get(organization_id)
            
            # Cek apakah pengguna adalah admin, editor, atau member dari organisasi
            member = Member.get(user.id, organization.id)
            if member:
                if member.capacity in ['admin', 'editor', 'member']:
                    return True

    # Jika tidak ada kondisi yang terpenuhi, akses ditolak
    return False
