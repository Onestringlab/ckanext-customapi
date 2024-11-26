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

        @blueprint_customapi.route('/welcome_api', methods=['GET'])
        def welcome_api():
            """
            Route untuk /welcome_api
            """
            return jsonify({
                "message": "Welcome to API!",
                "success": True
            })
        """
        http://localhost:5000/query-solr?q=climate&rows=5&start=10&sort=title asc
        http://localhost:5000/api/1/custom/query-solr?q=(title:Pendidikan%20AND%20notes:Pendidikan)&facet.field=[%22organization%22,%22kategori%22,%22prioritas_tahun%22,%22tags%22,%22res_format%22]&facet.limit=500&start=0&rows=20&sort=prioritas_tahun%20desc&include_private=true
        http://localhost:8983/solr/ckan/select?q=*:*&facet=true&facet.field=organization&rows=0&wt=json
        """
        @blueprint.route('/query-solr', methods=['GET'])
        def query_solr():
            """
            Query Solr dengan parameter dan format faceting yang benar.
            """
            try:
                solr_url = "http://solr:8983/solr/ckan/select"

                # Ambil parameter query dari URL
                query = request.args.get('q', '*:*')  # Default query semua data
                rows = int(request.args.get('rows', 10))  # Default jumlah hasil
                start = int(request.args.get('start', 0))  # Default offset
                sort = request.args.get('sort', 'prioritas_tahun desc')  # Default sorting
                include_private = request.args.get('include_private', 'true').lower() == 'true'

                # Facet fields
                facet_fields = request.args.get(
                    'facet.field',
                    '["organization", "kategori", "prioritas_tahun", "tags", "res_format"]'
                )
                facet_fields = eval(facet_fields)  # Convert string list to Python list
                facet_limit = int(request.args.get('facet.limit', 500))

                # Parameter untuk Solr
                params = {
                    'q': query,
                    'wt': 'json',
                    'rows': rows,
                    'start': start,
                    'sort': sort,
                    'facet': 'true',
                    'facet.limit': facet_limit,
                    'fq': 'private:true' if include_private else '-private:true'
                }

                # Tambahkan setiap facet.field secara terpisah
                for field in facet_fields:
                    params.setdefault('facet.field', []).append(field)

                # Kirimkan query ke Solr
                response = requests.get(solr_url, params=params)
                response.raise_for_status()

                # Kembalikan hasil mentah dari Solr
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