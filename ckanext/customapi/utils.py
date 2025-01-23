import jwt
import datetime
import requests

from flask import jsonify
from sqlalchemy import or_
from ckan.logic import get_action
from ckan.model import Package, User, Group, Member, meta

def query_custom(query, params=None):
    """
    Helper function untuk menjalankan query ke database CKAN.

    :param query: Query SQL yang akan dijalankan.
    :param params: Parameter untuk query (dictionary).
    :return: Hasil query dalam bentuk list of rows.
    """
    session = meta.Session
    try:
        # Eksekusi query dengan parameter
        result = session.execute(query, params or {})
        session.commit()
        return result.fetchall()
    except Exception as e:
        # Tangani error dengan logging atau raise exception
        session.rollback()
        raise Exception(f"Error executing query: {e}")
    finally:
        # Pastikan session tidak bocor
        session.close()

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

def get_sysadmin():
    session = meta.Session
    sysadmin_users = session.query(User).filter(User.sysadmin == True, User.email != None).all()
    result = []
    for user in sysadmin_users:
        result.append({
            "id": user.id,
            "username": user.name,
            "email": user.email,
            "fullname": user.fullname,
            "created": user.created.isoformat() if user.created else None,
            "state": user.state,
            "sysadmin": user.sysadmin,
        })
    return result

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
                LIMIT 1
            '''
    result = query_custom(query, {'username': username})
    row = result[0]

    # Konversi hasil query menjadi daftar dictionary
    data = {
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
    return data

def get_profile_by_id(user_id):
    query = '''
                SELECT id, about, name, activity_streams_email_notifications, 
                    apikey, created, fullname, email, sysadmin, state, image_url 
                FROM public.user 
                WHERE id = :user_id
                LIMIT 1
            '''
    result = query_custom(query, {'user_id': user_id})
    row = result[0]

    # Konversi hasil query menjadi daftar dictionary
    data ={
            "id": row[0],
            "about": row[1],
            "name": row[2],
            "activity_streams_email_notifications": row[3],
            "apikey": row[4],
            "created": row[5],
            "fullname": row[6],
            "email": row[7],
            "sysadmin": row[8],
            "state": row[9],
            "image_url": row[10]
        }
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
    
    if user:
        # Jika pengguna adalah sysadmin, beri akses
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
                capacities = get_username_capacity(user.name, group.id)
                if capacities:
                    capacity = capacities[0].get('capacity', None)
                    if capacity in ['admin', 'editor', 'member']:
                        package_access = True

    if len(has_package_collaborator(dataset_id, user_id)) > 0:
        package_access = True
    
    return package_access

def has_stream_access(user_id, ord_id):
    # Mendapatkan pengguna berdasarkan user_id
    user = User.get(user_id)
    dataset = Package.get(dataset_id)
    stream_access = False

    if not user:
        stream_access = False
    
    if not dataset:
        raise ValueError(f"Dataset dengan ID {dataset_id} tidak ditemukan.")
    
    # Jika pengguna adalah sysadmin, beri akses
    if user:
        if user.sysadmin:
            stream_access = True
    
        # Jika pengguna adalah creator dari dataset, beri akses
        if user.id == dataset.creator_user_id:
            stream_access = True
    
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
                        stream_access = True

    return stream_access

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

    total_org = total_kl + total_pv + total_kk

    return {
        "total_org": total_org,
        "total_kl": total_kl,
        "data_kl": data_kl,
        "total_pv": total_pv,
        "data_pv": data_pv,
        "total_kk": total_kk,
        "data_kk": data_kk
    }

def get_organizations_query(q, sort,limit=10, offset=0):

    valid_sorts = ["asc", "desc"]
    if sort.lower() not in valid_sorts:
        sort = "asc" 

    query = f'''
                SELECT g.id, 
                    g.name, 
                    g.title, 
                    g.image_url,
                    g.description,
                    MAX(CASE WHEN ge.key = 'department_type' THEN ge.value ELSE NULL END) AS department_type,
                    MAX(CASE WHEN ge.key = 'notes' THEN ge.value ELSE NULL END) AS notes,
                    MAX(CASE WHEN ge.key = 'department_id' THEN ge.value ELSE NULL END) AS department_id
                FROM public.group g
                LEFT JOIN public.group_extra ge ON g.id = ge.group_id
                WHERE g.is_organization = true
                    AND g.state = 'active'
                    AND g.approval_status = 'approved'
                    AND g.title ILIKE :q
                GROUP BY g.id, g.name, g.title, g.image_url
                ORDER BY g.title {sort}
                LIMIT :limit
                OFFSET :offset
            '''
    # Parameter untuk query
    params = {
        'q': f"%{q}%",
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
            "description": row[4],
            "department_type": row[5],
            "notes": row[6],
            "department_id": row[7],
            "dataset_count": get_count_dataset_organization(row[1])
        }
        for row in result
    ]
    return data

def get_organizations_query_count(q, sort):

    valid_sorts = ["asc", "desc"]
    if sort.lower() not in valid_sorts:
        sort = "asc" 

    query = f'''
                SELECT COUNT(*)
                FROM public.group g
                WHERE g.is_organization = TRUE
                AND g.state = 'active'
                AND g.approval_status = 'approved'
                AND g.title ILIKE :q
            '''
    # Parameter untuk query
    params = {
        'q': f"%{q}%"
    }
    result = query_custom(query, params)
    
    row = result[0]
    data = {"total": row[0]}

    return data

def get_count_dataset_organization(owr_org):
    query = '*:*'
    query += f" AND organization:{owr_org}"
    
    params = {
            'q': query,
            'wt': 'json',
            'rows': 0,
            'start': 0,
            'include_private': True,
            'facet.limit': 0
    }
    
    context = {'ignore_auth': True}

    response = get_action('package_search')(context, params)

    return response['count']

def package_collaborator_org_list(dataset_id):
    query = f'''
                SELECT pm.user_id, u.name AS username, 
                pm.capacity,
                pm.package_id, 
                pm.modified
                FROM package_member pm
                JOIN "user" u ON pm.user_id = u.id
                WHERE pm.package_id = :dataset_id
            '''
    # Parameter untuk query
    params = {
        'dataset_id': dataset_id
    }

    result = query_custom(query, params)

    data = [
        {
            "user_id": row[0],
            "name": row[1],
            "capacity": row[2],
            "package_id": row[3],
            "modified": row[4]
        }
        for row in result
    ]

    return data

def has_package_collaborator(package_name, username):
    query = f'''
                SELECT pm.user_id, 
                    u.name AS username, 
                    pm.capacity, 
                    pm.package_id, 
                    pm.modified
                FROM package_member pm
                JOIN "user" u ON pm.user_id = u.id
                JOIN "package" p ON p.id = pm.package_id
                WHERE p.name = :package_name
                AND u.name = :username
            '''
    # Parameter untuk query
    params = {
        'package_name': package_name, 'username': username
    }

    result = query_custom(query, params)
    data = [
        {
            "user_id": row[0],
            "name": row[1],
            "capacity": row[2],
            "package_id": row[3],
            "modified": row[4]
        }
        for row in result
    ]
    return data


def add_package_collaborator(package_id, user_id, capacity):
    """
    Menambahkan kolaborator ke dataset.

    :param package_id: ID dataset tempat kolaborator akan ditambahkan.
    :param user_id: ID pengguna yang akan ditambahkan sebagai kolaborator.
    :param capacity: Peran kolaborator (misalnya, 'editor', 'member').
    :return: Dictionary yang merepresentasikan kolaborator baru.
    """

    # Validasi input
    allowed_capacities = ['editor', 'member']
    if capacity not in allowed_capacities:
        raise ValueError(f"Invalid capacity. Must be one of {', '.join(allowed_capacities)}")

    # Query untuk menambahkan kolaborator
    query = '''
        INSERT INTO package_member (user_id, capacity, package_id, modified)
        VALUES (:user_id, :capacity, :package_id, :modified)
        RETURNING user_id, capacity, package_id, modified
    '''

    # Parameter untuk query
    params = {
        'user_id': user_id,
        'capacity': capacity,
        'package_id': package_id,
        'modified': datetime.datetime.utcnow()
    }

    # Eksekusi query dan ambil hasil
    result = query_custom(query, params)

    # Format hasil menjadi dictionary
    if result:
        row = result[0]
        return {
            "user_id": row[0],
            "capacity": row[1],
            "package_id": row[2]
        }
    else:
        raise Exception("Failed to add collaborator.")


def delete_package_collaborator(package_id, user_id):
    """
    Menghapus kolaborator dari dataset.

    :param package_id: ID dataset tempat kolaborator akan dihapus.
    :param user_id: ID pengguna yang akan dihapus sebagai kolaborator.
    :return: Pesan sukses atau error.
    """

    # Query untuk menghapus kolaborator
    query = '''
        DELETE FROM package_member
        WHERE package_id = :package_id AND user_id = :user_id
        RETURNING user_id, package_id
    '''

    # Parameter untuk query
    params = {
        'package_id': package_id,
        'user_id': user_id
    }

    # Eksekusi query dan ambil hasil
    result = query_custom(query, params)

    # Periksa apakah data berhasil dihapus
    if result:
        row = result[0]
        return {
            "message": "Collaborator deleted successfully.",
            "user_id": row[0],
            "package_id": row[1]
        }
    else:
        raise Exception(f"No collaborator found with package_id {package_id} and user_id {user_id}.")

def update_package_collaborator(package_id, user_id, capacity):
    """
    Memperbarui kolaborator pada dataset.

    :param package_id: ID dataset tempat kolaborator akan diperbarui.
    :param user_id: ID pengguna yang kolaborasinya akan diperbarui.
    :param capacity: Peran baru kolaborator (misalnya, 'editor', 'member').
    :return: Dictionary yang merepresentasikan kolaborator yang diperbarui.
    """

    # Validasi input
    allowed_capacities = ['editor', 'member']
    if capacity not in allowed_capacities:
        raise ValueError(f"Invalid capacity. Must be one of {', '.join(allowed_capacities)}")

    # Query untuk memperbarui kolaborator
    query = '''
        UPDATE package_member
        SET capacity = :capacity, modified = :modified
        WHERE package_id = :package_id AND user_id = :user_id
        RETURNING user_id, capacity, package_id, modified
    '''

    # Parameter untuk query
    params = {
        'user_id': user_id,
        'capacity': capacity,
        'package_id': package_id,
        'modified': datetime.datetime.utcnow()
    }

    # Eksekusi query dan ambil hasil
    result = query_custom(query, params)

    # Format hasil menjadi dictionary
    if result:
        row = result[0]
        return {
            "user_id": row[0],
            "capacity": row[1],
            "package_id": row[2],
            "modified": row[3].isoformat()  # Konversi datetime ke format ISO 8601
        }
    else:
        raise Exception(f"No collaborator found with package_id {package_id} and user_id {user_id}.")

def search_username(username):
    """
    Mencari pengguna berdasarkan username menggunakan LIKE.

    :param username: String pencarian untuk username (partial match).
    :return: List dictionary pengguna yang ditemukan.
    """

    # Query SQL untuk pencarian username
    query = '''
        SELECT id, name, fullname, email, created, sysadmin
        FROM "user"
        WHERE
        state = 'active' 
        AND name ILIKE :username
        ORDER BY name asc
        limit 10
    '''

    # Parameter untuk query (LIKE dengan wildcard)
    params = {
        'username': f'%{username}%'
    }

    # Eksekusi query
    result = query_custom(query, params)

    # Format hasil menjadi list of dictionaries
    users = [
        {
            "id": row[0],
            "name": row[1],
            "fullname": row[2],
            "email": row[3],
            "created": row[4],
            "sysadmin": row[5]
        }
        for row in result
    ]

    return users

