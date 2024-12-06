import requests
import jwt
from datetime import datetime
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckan.common import config
from ckan.logic import get_action
from ckan.model import Package, User, meta
from flask import Blueprint, jsonify, request

from ckanext.customapi.utils import query_custom, query_solr

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
        # session = meta.Session

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
                "message": "Welcome to API 3!!",
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
                    'facet.field': ['organization', 'kategori', 'prioritas_tahun', 'tags', 'res_format'],  # Field untuk faceting
                    'facet.limit': facet_limit,
                }

                # Kirim query ke Solr
                context = {}
                response = get_action('package_search')(context, params)

                return jsonify(response)

            except Exception as e:  # Tangani exception secara umum
                return jsonify({"success": False, "error": str(e)}), 500

        @blueprint_customapi.route('/get-dataset-by-name-id', methods=['POST'])
        def get_dataset_by_id_or_name():
            try:
                # Ambil parameter ID dan name dari payload JSON
                payload = request.get_json()

                # Cek apakah payload mengandung ID atau name
                record_id = payload.get('id')
                record_name = payload.get('name')

                if not record_id and not record_name:
                    return jsonify({"success": False, "error": "Either 'id' or 'name' parameter is required"}), 400

                # Buat query berdasarkan ID atau name
                query_parts = []
                if record_id:
                    query_parts.append(f"id:{record_id}")
                if record_name:
                    # Gunakan kutipan untuk memastikan query mendukung string dengan spasi
                    query_parts.append(f'name:"{record_name}"')

                # Gabungkan query dengan OR
                query = " OR ".join(query_parts)

                # Parameter query untuk Solr
                params = {
                    'q': query,  # Query utama
                    'wt': 'json',  # Format respons JSON
                    'rows': 1  # Batasi hasil hanya satu
                }

                # Kirim query ke Solr
                response = query_solr(params)

                # Parse respons dari Solr
                solr_response = response.json()
                docs = solr_response.get('response', {}).get('docs', [])

                # Cek apakah data ditemukan
                if not docs:
                    return jsonify({"success": False, "message": "No record found for the given ID or name"}), 404

                # Kembalikan data dokumen
                return jsonify({"success": True, "data": docs[0]})

            except requests.exceptions.RequestException as e:
                return jsonify({"success": False, "error": str(e)}), 500
        
        @blueprint_customapi.route('/get-token', methods=['POST'])
        def get_token():
            payload = request.get_json()  # Mengambil JSON body dari request
            jwt_token = payload.get('jwt_token')  # Mengambil JWT dari key 'jwt_token'

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