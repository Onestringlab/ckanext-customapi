import jwt
import logging
import requests
from datetime import datetime
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckan.common import config
from ckan.logic import get_action
from ckan.plugins import toolkit as tk
from flask import Blueprint, jsonify, request, make_response

from ckanext.customapi.utils import query_custom, get_username, has_package_access
from ckanext.customapi.utils import get_profile_by_username, get_username_capacity
from ckanext.customapi.utils import list_organizations, get_profile_by_id, get_organizations_query
from ckanext.customapi.utils import get_count_dataset_organization, get_sysadmin, get_organizations_query_count

solr_url = tk.config.get('ckanext.customapi.solr_url', environ.get('CKANEXT__CUSTOMAPI__SOLR_URL'))

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

        @blueprint_customapi.route('/welcome-api', methods=['GET'])
        def welcome_api():
            """
            Route untuk /welcome_api
            """
            message = "Welcome to the Virtual World 20.1!"
            log.info(f'message:{message}')

            # Buat respons JSON
            response = jsonify({
                "message": message,
                "success": True
            })

            return response

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
        
        @blueprint_customapi.route('/get-user-by-id', methods=['POST'])
        def get_user_by_id():
            """
            Route untuk /get-user-by-id
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

                payload = request.get_json()
                user_id = payload.get('id', '').strip()
                data = get_profile_by_id(user_id)

                return jsonify({
                    "data": data,
                    "success": True,
                    "username": username,
                    "email": email
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

                context = {'ignore_auth': True}

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
                response.update({"sysadmin": get_sysadmin()})
                response.update({"creator_profile": get_profile_by_id(response["creator_user_id"])})

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

        @blueprint_customapi.route('/get-stream-dataset', methods=['POST'])
        def get_stream_dataset():
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

                context = {'ignore_auth': True}

                response = get_action('package_activity_list')(context, params)
                for activity in response:
                    user_id = activity.get("user_id")
                    if user_id:
                        user_profile = get_profile_by_id(user_id)
                        activity["user_profile"] = user_profile 

                return jsonify({"success": True, "email": email, "data": response})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/get-stream-organizations', methods=['POST'])
        def get_stream_organizations():
            try:
                payload = request.get_json()
                request_id = payload.get('id')
                request_name = payload.get('name')
                limit = int(payload.get('limit', 10))
                offset = int(payload.get('offset', 0))

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
                    organisasi_id = request_id
                if request_name:
                    organisasi_id = request_name

                params = {'id': organisasi_id, 'limit': limit,'offset': offset}


                context = {'ignore_auth': True}

                response = get_action('organization_activity_list')(context, params)
                for activity in response:
                    user_id = activity["user_id"]
                    if user_id:
                        user_profile = get_profile_by_id(user_id)
                        activity["user_profile"] = user_profile 

                return jsonify({"success": True, "email": email, "data": response})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/get-organizations', methods=['POST'])
        def get_organization():
            try:
                payload = request.get_json()
                q = payload.get('q')
                limit = int(payload.get('limit', 10))
                offset = int(payload.get('offset', 0))
                sort = payload.get('sort', 'asd')

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]
                
                organizations = get_organizations_query_count(q,sort)
                total_item = organizations["total"]
                response = get_organizations_query(q,sort,limit,offset)

                return jsonify({"success": True, "email": email, "data": response, "total_item": total_item, "offset": offset})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/get-organization-show', methods=['POST'])
        def get_organization_show():
            try:
                payload = request.get_json()
                org_id = payload.get('org_id')
                org_name = payload.get('org_name')

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]

                if org_id:
                    org_id = org_id
                if org_name:
                    org_id = org_name

                params = {'id': org_id}

                context = {'ignore_auth': True}
                dataset_organization = get_count_dataset_organization(org_id)
    
                response = get_action('organization_show')(context, params)
                response.update({"dataset_organization": dataset_organization})               

                return jsonify({"success": True, "email": email, "data": response})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

    @blueprint_customapi.route('/get-similar-datasets', methods=['POST'])
    def get_similar_datasets():
        ##
        return solr_url

    return blueprint_customapi
        
        # @blueprint_customapi.route('/get-organizations-list', methods=['POST'])
        # def get_organizations_list():
        #     try:
        #         payload = request.get_json()
        #         limit = int(payload.get('limit', 10))
        #         offset = int(payload.get('offset', 0))
        #         sort = payload.get('sort', '')
        #         include_extras = payload.get('include_extras', True)
        #         include_extras = bool(include_extras) if isinstance(include_extras, bool) else str(include_extras).lower() == 'true'
        #         all_fields = payload.get('all_fields', True)
        #         all_fields = bool(all_fields) if isinstance(all_fields, bool) else str(all_fields).lower() == 'true'

        #         params = {
        #             'wt': 'json',
        #             'limit': limit,
        #             'offset': offset,
        #             'sort': sort,
        #             'include_extras': include_extras,
        #             "all_fields": all_fields
        #         }

        #         email = "anonymous@somedomain.com"
        #         username = "anonymous"
        #         token = request.headers.get("Authorization")
        #         if token:
        #             if not token.startswith("Bearer "):
        #                 return jsonify({"error": "Invalid authorization format"}), 400
        #             token_value = token.split(" ", 1)[1]
        #             _, email = get_username(token_value)
        #             username = email.split('@')[0]

        #         context = {'ignore_auth': True}

        #         response = get_action('organization_list')(context, params)

        #         return jsonify({"success": True, "email": email, "data": response})
        #     except Exception as e:
        #         return jsonify({"error": f"{str(e)}"}), 400

       
    
def hello_api_action(context, data_dict):
    """
    Endpoint sederhana
    curl -X POST http://localhost/api/3/action/hello_api
    """
    return {'message': 'Hello, API!', 'success': True}