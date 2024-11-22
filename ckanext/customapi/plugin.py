import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.model import Package
from ckan.model.meta import Session
from flask import Blueprint, jsonify


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
            solr_url = "http://192.168.1.6:8983/solr/ckan/select"
            query = request.args.get('q', '*:*')  # Query default: semua data
            params = {
                'q': query,
                'wt': 'json',  # Format hasil JSON
                'rows': 10     # Batas hasil
            }
            response = requests.get(solr_url, params=params)
            return jsonify(response.json())
                
        return blueprint_customapi
    
    def create_blueprint():
        app.register_blueprint(blueprint_customapi, url_prefix="/api/custom")


def hello_api_action(context, data_dict):
    """
    Endpoint sederhana
    """
    return {'message': 'Hello, API!', 'success': True}