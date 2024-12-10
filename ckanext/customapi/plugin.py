import requests
import jwt
from datetime import datetime
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckan.common import config
from ckan.logic import get_action
from ckan.model import Package, User, meta
from flask import Blueprint, jsonify, request

from ckanext.customapi.utils import query_custom, query_solr, get_user_object, get_username, has_package_access

class CustomapiPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'customapi')
        toolkit.add_resource('assets', 'utils')
    
    # IActions
    def get_actions(self):
        return {
            'hello_api': hello_api_action
        }

    # IBlueprint
    def get_blueprint(self):
        # Inisialisasi engine SQLAlchemy
        session = meta.Session

        #Query API keys dari database menggunakan ORM SQLAlchemy
        # valid_api_keys = []
        # valid_api_keys = [user.apikey for user in session.query(User).filter(User.apikey.isnot(None)).all()]

        # Method untuk mendaftarkan Blueprint.
        blueprint_customapi = Blueprint('customapi', __name__,url_prefix='/api/1/custom')

        @blueprint_customapi.route('/welcome-api3', methods=['GET'])
        def welcome_api():
            """
            Route untuk /welcome_api
            """
            return jsonify({
                "message": "Welcome to the Virtual World!!",
                "success": True
            })

        @blueprint_customapi.route('/get-user-by-username', methods=['POST'])
        def get_user_by_username():
            """
            Route untuk /get-user-by-username
            """
            try:
                # Ambil parameter username dari JSON payload
                payload = request.get_json()
                if not payload or 'username' not in payload:
                    return jsonify({"success": False, "error": "Parameter 'username' is required"}), 400
                
                username = payload['username']

                # Query menggunakan parameterized query untuk keamanan
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

                return jsonify({
                    "data": data,
                    "success": True
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @blueprint_customapi.route('/get-capacity-by-username', methods=['POST'])
        def get_capacity_by_username():
            """
            Route untuk mendapatkan kapasitas berdasarkan username
            """
            try:
                # Ambil parameter username dari JSON payload
                payload = request.get_json()
                if not payload or 'username' not in payload:
                    return jsonify({"success": False, "error": "Parameter 'username' is required"}), 400

                username = payload['username']

                # Query menggunakan parameterized query untuk keamanan
                query = '''
                    SELECT 
                        u.name AS user_name, 
                        u.id AS user_id, 
                        g.name AS organization_name, 
                        m.capacity
                    FROM "member" m
                    JOIN "user" u ON m.table_id = u.id
                    JOIN "group" g ON m.group_id = g.id
                    WHERE 
                        g.type = 'organization'
                        AND m.state = 'active'
                        AND u.name = :username
                '''
                result = query_custom(query, {'username': username})

                # Konversi hasil query menjadi daftar dictionary
                data = [
                    {
                        "user_name": row[0],
                        "user_id": row[1],
                        "organization_name": row[2],
                        "capacity": row[3]
                    }
                    for row in result
                ]

                return jsonify({
                    "data": data,
                    "success": True
                })

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @blueprint_customapi.route('/get-dataset', methods=['POST'])
        def get_dataset():
            try:
                # Ambil payload dari request body
                payload = request.get_json()
                if not payload:
                    return jsonify({"success": False, "error": "Request body is required"}), 400

                token = request.headers.get("Authorization")
                username, email = get_username(token)

                # Ambil parameter dari payload JSON
                query = payload.get('q', '*:*')
                rows = int(payload.get('rows', 10))
                start = int(payload.get('start', 0))
                sort = payload.get('sort', 'prioritas_tahun desc')
                facet_limit = int(payload.get('facet.limit', 500))

                # Format query dengan `title` atau `notes`
                if query != '*:*':
                    query = f"(title:{query} OR notes:{query})"

                # Parameter untuk Solr
                params = {
                    'q': query,  # Query utama
                    'wt': 'json',
                    'rows': rows,
                    'start': start,
                    'sort': sort,
                    'facet': 'true',
                    'facet.field': ['organization', 'kategori', 'prioritas_tahun', 'tags', 'res_format'],
                    'facet.limit': facet_limit,
                    'include_private': True 
                }

                context = {'ignore_auth': True}

                # Jalankan package_search
                response = get_action('package_search')(context, params)

                return jsonify({"success": True, "email": email, "data": response})

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @blueprint_customapi.route('/get-dataset-by-name-id', methods=['POST'])
        def get_dataset_by_name_or_id():
            try:
                # Ambil parameter ID dan name dari payload JSON
                payload = request.get_json()

                # Cek apakah payload mengandung ID atau name
                request_id = payload.get('id')
                request_name = payload.get('name')
                token = request.headers.get("Authorization")
  
                if not request_id and not request_name:
                    return jsonify({"success": False, "error": "Either 'id' or 'name' parameter is required"}), 400

                if request_id:
                    id = request_id
                if request_name:
                    id = request_name
                preferred_username, email = get_username(token)
                username = email.split('@')[0]

                # Parameter query untuk package_show
                params = {'id': id}

                # Context dengan pengguna yang memiliki akses
                context = {
                    'user': username,
                    'ignore_auth': False
                }

                role_access = has_package_access(id, username)
                print(f'role_access-------------:{role_access}')

                # Jalankan package_show
                response = get_action('package_show')(context, params)

                # Kembalikan data dokumen
                return jsonify({"success": True, "data": response})

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @blueprint_customapi.route('/get-token', methods=['POST'])
        def get_token():
            jwt_token = request.headers.get("Authorization")

            if not jwt_token:
                return jsonify({"error": "JWT token tidak ditemukan"}), 400

            try:
                # Dekode JWT tanpa memvalidasi signature dan expiration
                decoded_token = jwt.decode(jwt_token, options={"verify_signature": False, "verify_exp": False})

                # Jika sukses, kembalikan decoded token
                return jsonify(decoded_token)

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token sudah kedaluwarsa"}), 401
            except jwt.InvalidTokenError as e:
                return jsonify({"error": f"Token tidak valid: {str(e)}"}), 400
                
        return blueprint_customapi
    
def hello_api_action(context, data_dict):
    """
    Endpoint sederhana
    curl -X POST http://localhost/api/3/action/hello_api
    """
    return {'message': 'Hello, API!', 'success': True}