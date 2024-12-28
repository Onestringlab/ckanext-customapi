import jwt
import logging
import requests
from datetime import datetime
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckan.common import config
from ckan.logic import get_action
from flask import Blueprint, jsonify, request, make_response

from ckanext.customapi.utils import query_custom, get_username, has_package_access
from ckanext.customapi.utils import get_profile_by_username, get_username_capacity
from ckanext.customapi.utils import list_organizations

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
        log = logging.getLogger(__name__)

        # Method untuk mendaftarkan Blueprint.
        blueprint_customapi = Blueprint('customapi', __name__,url_prefix='/api/1/custom')

        @blueprint_customapi.route('/welcome-api3', methods=['GET'])
        def welcome_api():
            """
            Route untuk /welcome_api
            """
            response = make_response("Membuat cookie")
            response.set_cookie('hore', 'Kambing')
            message = "Welcome to the Virtual World 13!"
            log.info(f'message:{message}')
            return jsonify({
                "message": message,
                "success": True
            })

        @blueprint_customapi.route('/get-user-by-username', methods=['POST'])
        def get_user_by_username():
            """
            Route untuk /get-user-by-username
            """
            try:
                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]
                    data = get_profile_by_username(username)

                    return jsonify({
                        "data": data,
                        "success": True,
                        "username": username
                    })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @blueprint_customapi.route('/get-capacity-by-username', methods=['POST'])
        def get_capacity_by_username():
            """
            Route untuk mendapatkan kapasitas berdasarkan username
            """
            try:
                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]
                    data = get_username_capacity(username)

                    return jsonify({
                        "data": data,
                        "success": True
                    })

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @blueprint_customapi.route('/get-dataset', methods=['POST'])
        def get_dataset():
            try:
                payload = request.get_json()
                if not payload:
                    return jsonify({"success": False, "error": "Request body is required"}), 400

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]

                query = payload.get('q', '').strip()
                rows = int(payload.get('rows', 10))
                start = int(payload.get('start', 0))
                sort = payload.get('sort', '')
                facet_limit = int(payload.get('facet_limit', 500))
                include_private = payload.get('include_private', True)
                include_private = bool(include_private) if isinstance(include_private, bool) else str(include_private).lower() == 'true'
                organization = payload.get('organization', '').strip()
                kategori = payload.get('kategori', '').strip()
                prioritas_tahun = payload.get('prioritas_tahun', '').strip()
                tags = payload.get('tags', '').strip()
                res_format = payload.get('res_format', '').strip()
                fq = payload.get('fq', '').strip()

                if len(query) == 0:
                    query = '*:*'
                elif query != '*:*': 
                    query = f"(title:{query} OR notes:{query})"
                
                if organization:
                    query += f" AND organization:{organization}"
                if kategori:
                    query += f" AND kategori:{kategori}"
                if prioritas_tahun:
                    query += f" AND prioritas_tahun:{prioritas_tahun}"
                if tags:
                    query += f" AND tags:{tags}"
                if res_format:
                    query += f" AND res_format:{res_format}"
                if fq:
                    query += f" AND {fq}"

                params = {
                    'q': query,
                    'wt': 'json',
                    'rows': rows,
                    'start': start,
                    'sort': sort,
                    'facet': 'true',
                    'facet.field': ['organization', 'kategori', 'prioritas_tahun', 'tags', 'res_format'],
                    'facet.limit': facet_limit,
                    'include_private': include_private
                }

                context = {'user': username,'ignore_auth': True}

                response = get_action('package_search')(context, params)

                return jsonify({"success": True, "email": email, "data": response})

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @blueprint_customapi.route('/get-dataset-by-name-id', methods=['POST'])
        def get_dataset_by_name_or_id():
            try:
                payload = request.get_json()
                request_id = payload.get('id')
                request_name = payload.get('name')

                if not request_id and not request_name:
                    return jsonify({"success": False, "error": "Either 'id' or 'name' parameter is required"}), 400

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]

                if request_id:
                    dataset_id = request_id
                if request_name:
                    dataset_id = request_name

                params = {'id': dataset_id}

                has_access = has_package_access(username, dataset_id)

                context = {'ignore_auth': True}

                response = get_action('package_show')(context, params)

                return jsonify({"success": True, "email": email, "has_access": has_access, "data": response})

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
                
        @blueprint_customapi.route('/get-count-datasets', methods=['POST'])
        def get_count_datasets():
            try:
                params = {
                    'q': '*:*',
                    'wt': 'json',
                    'rows': 0,
                    'include_private': True
                }

                context = {'ignore_auth': True}
                result = toolkit.get_action('package_search')(context, params)
                
                return jsonify({"success": True, "data": result})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/get-data-organizations', methods=['POST'])
        def get_data_organizations():
            try:
                data = list_organizations()
                return jsonify({"success": True, "data": data})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400


        return blueprint_customapi
    
def hello_api_action(context, data_dict):
    """
    Endpoint sederhana
    curl -X POST http://localhost/api/3/action/hello_api
    """
    return {'message': 'Hello, API!', 'success': True}