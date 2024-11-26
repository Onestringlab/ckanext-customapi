import requests
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.model import Package
from ckan.model.meta import Session
from flask import Blueprint, jsonify, request

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
        """
        Method untuk mendaftarkan Blueprint.
        """
        blueprint_customapi = Blueprint('customapi', __name__,url_prefix='/api/1/custom')

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
                solr_url = "http://solr:8983/solr/ckan/select"

                # Query dan parameter untuk Solr
                # params = {
                #     'q': '(title:Pendidikan AND notes:Pendidikan)',  # Query utama
                #     'facet': 'true',  # Aktifkan faceting
                #     'facet.field': ['organization', 'kategori'],  # Field untuk faceting
                #     'facet.limit': 500,  # Batas faceting
                #     'rows': 1,  # Jumlah hasil
                #     'start': 0,  # Offset
                #     'sort': 'prioritas_tahun desc',  # Sorting
                #     'wt': 'json',  # Format hasil
                # }

                # Parameter query
                query = request.args.get('q', '*:*')
                rows = int(request.args.get('rows', 10))
                start = int(request.args.get('start', 0))
                sort = request.args.get('sort', 'prioritas_tahun desc')
                # include_private = request.args.get('include_private', 'true').lower() == 'true'
                facet_limit = int(request.args.get('facet.limit', 500))

                # facet_fields = eval(request.args.get(
                #     'facet.field',
                #     '["organization", "kategori", "tags"]'
                # ))

                params = {
                    'q': '(title:Pendidikan AND notes:Pendidikan)',  # Query utama
                    'wt': 'json',
                    'rows': rows,
                    'start': start,
                    'sort': sort,
                    'facet': 'true',
                    'facet.field': ['organization','kategori'],  # Field untuk faceting
                    'facet.limit': facet_limit,
                    'fq': 'private:true'
                }

                # Kirim query ke Solr
                response = requests.get(solr_url, params=params)
                response.raise_for_status()

                # Debug URL
                print("Query URL:", response.url)

                return jsonify(response.json())

            except requests.exceptions.RequestException as e:
                return jsonify({"success": False, "error": str(e)}), 500

                
        return blueprint_customapi
    
def hello_api_action(context, data_dict):
    """
    Endpoint sederhana
    curl -X POST http://localhost/api/3/action/hello_api
    """
    return {'message': 'Hello, API!', 'success': True}