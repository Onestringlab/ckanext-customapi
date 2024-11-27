import requests
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckan.common import config
from ckan.model import Package, User, meta
from flask import Blueprint, jsonify, request

# from sqlalchemy import create_engine, text

class CustomapiPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'customapi')
    
    # IActions
    def get_actions(self):
        return {
            'hello_api': hello_api_action
        }

    # IBlueprint
    def get_blueprint(self):
        # Ambil URL database dari konfigurasi CKAN
        DATABASE_URI = config.get('sqlalchemy.url')
        
        # Inisialisasi engine SQLAlchemy
        # engine = create_engine(DATABASE_URI)

        # Inisialisasi engine SQLAlchemy
        session = meta.Session

        """
        Method untuk mendaftarkan Blueprint.
        """
        blueprint_customapi = Blueprint('customapi', __name__,url_prefix='/api/1/custom')
        solr_url = "http://solr:8983/solr/ckan/select"

        @blueprint_customapi.route('/welcome-api', methods=['GET'])
        def welcome_api():
            """
            Route untuk /welcome_api
            """
            return jsonify({
                "message": "Welcome to API!",
                "success": True
            })

        @blueprint_customapi.route('/query-solr', methods=['GET'])
        def query_solr():
            try:
                # Parameter query
                query = request.args.get('q', '*:*')
                rows = int(request.args.get('rows', 10))
                start = int(request.args.get('start', 0))
                sort = request.args.get('sort', 'prioritas_tahun desc')
                # include_private = request.args.get('include_private', 'true').lower() == 'true'
                facet_limit = int(request.args.get('facet.limit', 500))

                # Format query dengan `title` dan `notes`
                if query != '*:*':
                    query = f"(title:{query} AND notes:{query})"

                params = {
                    'q': query,  # Query utama
                    'wt': 'json',
                    'rows': rows,
                    'start': start,
                    'sort': sort,
                    'facet': 'true',
                    'facet.field': ['organization','kategori','prioritas_tahun','tags','res_format'],  # Field untuk faceting
                    'facet.limit': facet_limit,
                    # 'include_private':true
                }

                # Kirim query ke Solr
                response = requests.get(solr_url, params=params)
                response.raise_for_status()

                # Debug URL
                print("Query URL:", response.url)

                return jsonify(response.json())

            except requests.exceptions.RequestException as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @blueprint_customapi.route('/get-detail-by-name-id', methods=['GET'])
        def get_detail_by_id_or_name():
            try:
                # Validasi API Key
                api_key = request.headers.get("Authorization")
                if not api_key:
                    return jsonify({"success": False, "error": "Unauthorized: Missing API Key"}), 401

                #Query API keys dari database menggunakan ORM
                valid_api_keys = []
                valid_api_keys = [user.apikey for user in session.query(User).filter(User.apikey.isnot(None)).all()]
                
                # valid_api_keys = []
                # with engine.connect() as connection:
                #     query = text("SELECT apikey FROM \"user\" WHERE apikey IS NOT NULL")
                #     result = connection.execute(query)
                #     valid_api_keys = [row['apikey'] for row in result]
                
                # Periksa apakah API Key yang diberikan valid
                if api_key not in valid_api_keys:
                    return jsonify({"success": False, "error": "Unauthorized: Invalid API Key"}), 401


                # Ambil parameter ID dan name dari request
                record_id = request.args.get('id')
                record_name = request.args.get('name')

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
                response = requests.get(solr_url, params=params)
                response.raise_for_status()

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
                
        return blueprint_customapi
    
def hello_api_action(context, data_dict):
    """
    Endpoint sederhana
    curl -X POST http://localhost/api/3/action/hello_api
    """
    return {'message': 'Hello, API!', 'success': True}