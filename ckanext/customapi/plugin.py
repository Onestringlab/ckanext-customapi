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
    def query_solr():
        try:
            solr_url = "http://localhost:8983/solr/ckan/select"

            query = request.args.get('q', '*:*')
            rows = int(request.args.get('rows', 10))
            start = int(request.args.get('start', 0))
            sort = request.args.get('sort', 'prioritas_tahun desc')
            include_private = request.args.get('include_private', 'true').lower() == 'true'

            facet_fields = eval(request.args.get(
                'facet.field',
                '["organization", "kategori", "tags"]'
            ))
            facet_limit = int(request.args.get('facet.limit', 500))

            params = {
                'q': query,
                'wt': 'json',
                'rows': rows,
                'start': start,
                'sort': sort,
                'facet': 'true',
                'facet.limit': facet_limit,
                'fq': 'private:true' if include_private else '*:*',
            }

            for field in facet_fields:
                params.setdefault('facet.field', []).append(field)

            # Debugging
            print("Query Parameters:", params)

            response = requests.get(solr_url, params=params)
            response.raise_for_status()

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