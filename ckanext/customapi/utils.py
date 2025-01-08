import jwt
import requests

from flask import jsonify
from sqlalchemy import or_
from ckan.logic import get_action
from ckan.model import Package, User, Group, Member, meta

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

def get_profile_by_id(user_id):
    query = '''
                SELECT id, name, apikey, fullname, email, reset_key, sysadmin, 
                    activity_streams_email_notifications, state, plugin_extras, image_url 
                FROM public.user 
                WHERE id = :user_id
            '''
    result = query_custom(query, {'user_id': user_id})

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

def get_username_capacity(username, group_id=None):
    # Query menggunakan parameterized query untuk keamanan
    query = '''
        SELECT 
            u.name AS user_name, 
            u.id AS user_id,
            g.id as  organization_id,
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

    result = query_custom(query, {'username': username})

    if group_id:
        query += ' AND g.id = :group_id'
        result = query_custom(query, {'username': username,'group_id': group_id})

    # Konversi hasil query menjadi daftar dictionary
    data = [
        {
            "user_name": row[0],
            "user_id": row[1],
            "organization_id" : row[2],
            "organization_title": row[3],
            "organization_name": row[4],
            "capacity": row[5]
        }
        for row in result
    ]

    return data

def has_package_access(user_id, dataset_id):
    # Mendapatkan pengguna berdasarkan user_id
    user = User.get(user_id)
    dataset = Package.get(dataset_id)
    package_access = False

    if not user:
        package_access = False
    
    if not dataset:
        raise ValueError(f"Dataset dengan ID {dataset_id} tidak ditemukan.")
    
    # Jika dataset bersifat public, beri akses
    if not dataset.private:
        package_access = True
    
    # Jika pengguna adalah sysadmin, beri akses
    if user:
        if user.sysadmin:
            package_access = True
    
    # Jika pengguna adalah creator dari dataset, beri akses
        if user.id == dataset.creator_user_id:
            package_access = True
    
        # Jika dataset private, cek kapasitas user di organisasi terkait
        if dataset.private:
            # Ambil grup dari dataset
            groups = dataset.get_groups()
            for group in groups:
                # Ambil grup terkait dengan dataset
                print(user.id, user.name ,group.id, group.name)
                capacities = get_username_capacity(user.name, group.id)
                print(capacities)
                if capacities:
                    capacity = capacities[0].get('capacity', None)
                    if capacity in ['admin', 'editor', 'member']:
                        package_access = True

    # Jika tidak ada kondisi yang terpenuhi, akses ditolak
    return package_access

def list_organizations():
    session = meta.Session

    # kementerian lembaga
    filters_kl = [
        Group.title.like('Arsip%'),
        Group.title.like('Badan%'),
        Group.title.like('Dewan%'),
        Group.title.like('Kementerian%'),
        Group.title.like('Kepolisian%'),
        Group.title.like('Komisi%'),
        Group.title.like('Lembaga%'),
        Group.title.like('Mahkamah%'),
        Group.title.like('Majelis%'),
        Group.title.like('Ombudsman%'),
        Group.title.like('Perpustakaan%'),
        Group.title.like('Pusat%')
    ]

    result_kl = (
        session.query(
            Group.id,
            Group.name,
            Group.title,
            Group.image_url
        )
        .filter(Group.is_organization == True)
        .filter(or_(*filters_kl))
        .order_by(Group.title.asc())
    )

    data_kl = [
            {
                "id": row.id,
                "name": row.name,
                "title": row.title,
                "image_url": row.image_url
            }
            for row in result_kl
        ]
    total_kl = result_kl.count()

    # provinsi
    result_pv = (
        session.query(
            Group.id,
            Group.name,
            Group.title,
            Group.image_url
        )
        .filter(Group.is_organization == True)
        .filter(Group.title.like('Provinsi%'))
        .order_by(Group.title.asc())
    )

    data_pv = [
            {
                "id": row.id,
                "name": row.name,
                "title": row.title,
                "image_url": row.image_url
            }
            for row in result_kl
        ]
    total_pv = result_pv.count()

    # kabupaten kota
    filters_kk = [
        Group.title.like('Kota%'),
        Group.title.like('Kabupaten%')
    ]

    result_kk = (
        session.query(
            Group.id,
            Group.name,
            Group.title,
            Group.image_url
        )
        .filter(Group.is_organization == True)
        .filter(or_(*filters_kk))
        .order_by(Group.title.asc())
    )

    data_kk = [
            {
                "id": row.id,
                "name": row.name,
                "title": row.title,
                "image_url": row.image_url
            }
            for row in result_kk
        ]
    total_kk = result_kk.count()

    return {
        "total_kl": total_kl,
        "data_kl": data_kl,
        "total_pv": total_pv,
        "data_pv": data_pv,
        "total_kk": total_kk,
        "data_kk": data_kk
    }

def get_organizations(q, sort,limit=10, offset=0):
    query = '''
                SELECT g.id, 
                    g.name, 
                    g.title, 
                    g.image_url, 
                    COUNT(p.id) AS dataset_count
                FROM public.group g
                LEFT JOIN public.package p ON g.id = p.owner_org
                WHERE g.is_organization = true
                AND g.approval_status = 'approved'
                AND g.title LIKE :q
                GROUP BY g.id, g.name, g.title, g.image_url
                ORDER BY g.title :sort
                LIMIT :limit
                OFFSET :offset
            '''
    # Parameter untuk query
    params = {
        'q': f"%{q}%",
        'sort' : sort,
        'limit': limit,
        'offset': offset,
    }
    result = query_custom(query, params)

    # Konversi hasil query menjadi daftar dictionary
    data = [
        {
            "id": row[0],
            "name": row[1],
            "title": row[2],
            "image": row[3],
            "dataset_count":[4]
        }
        for row in result
    ]
    return data