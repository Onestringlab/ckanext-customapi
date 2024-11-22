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
        blueprint_customapi = Blueprint('customapi', __name__)

        @blueprint_customapi.route('/welcome_api', methods=['GET'])
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
                query = request.args.get('q', '*:*')  # Query default: semua data
                # Tambahkan bidang default jika query tanpa spesifikasi
                if ':' not in query:
                    query = f'title:{query}' # OR notes:{query}'
                params = {
                    'q': query,
                    'wt': 'json',  # Format hasil JSON
                    'rows': 10     # Batas hasil
                }
                response = requests.get(solr_url, params=params)
                response.raise_for_status()
                return jsonify(response.json())
            except requests.exceptions.RequestException as e:
                return jsonify({"error": str(e)}), 500
                
        return blueprint_customapi
    
def hello_api_action(context, data_dict):
    """
    Endpoint sederhana
    """
    return {'message': 'Hello, API!', 'success': True}