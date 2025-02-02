import jwt
import logging
import requests
from datetime import datetime
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from os import environ
from ckan.common import config
from ckan.logic import get_action
from ckan.plugins import toolkit as tk
from flask import Blueprint, jsonify, request, make_response

from ckanext.customapi.utils import get_profile_by_username, get_username_capacity
from ckanext.customapi.utils import list_organizations, get_profile_by_id, get_organizations_query
from ckanext.customapi.utils import query_custom, get_username, has_package_access,has_stream_access
from ckanext.customapi.utils import get_count_dataset_organization, get_sysadmin, get_organizations_query_count

from ckanext.customapi.utils import package_collaborator_org_list, add_package_collaborator
from ckanext.customapi.utils import update_package_collaborator, delete_package_collaborator,search_username
from ckanext.customapi.utils import has_package_admin, has_package_stream

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
            message = "Welcome to the Virtual World 31.1!"
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
        
        @blueprint_customapi.route('/get-search-username', methods=['POST'])
        def get_search_username():
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
                username = payload.get('username', '').strip()
                data = search_username(username)

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
                has_admin = has_package_admin(username, dataset_id)
                has_stream = has_package_stream(username, dataset_id)

                context = {'ignore_auth': True}

                response = get_action('package_show')(context, params)
                response.update({"sysadmin": get_sysadmin()})
                response.update({"creator_profile": get_profile_by_id(response["creator_user_id"])})

                return jsonify({"success": True, "email": email, "has_access": has_access, 
                                    "data": response, "has_admin": has_admin,'has_stream': has_stream})

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

                has_stream = get_username_capacity(username, response['id'])
                has_admin = get_username_capacity(username, response['id'], True)
                is_stream = bool(has_stream)
                is_admin = bool(has_admin)
                
                return jsonify({"success": True, "email": email, "data": response, "has_stream": is_stream, "has_admin": is_admin})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/get-similar-datasets', methods=['POST'])
        def get_similar_datasets():
            solr_url = tk.config.get('ckanext.customapi.solr_url', environ.get('CKANEXT__CUSTOMAPI__SOLR_URL'))
            payload = request.get_json()
            dataset_id = payload.get('dataset_id')
            mlt_fl = payload.get('mlt_fl','title')
            mlt_match_include = payload.get('mlt_match_include', "false")
            mlt_mintf = int(payload.get('mlt_mintf',1))
            rows = int(payload.get('rows', 3))

            params = {
                "mlt.fl": mlt_fl,
                "mlt.match.include": mlt_match_include,
                "mlt.mintf": mlt_mintf,
                "q": f"id:{dataset_id}",
                "rows": rows
            }
            
            solr_url = solr_url + '/solr/ckan/mlt'

            email = "anonymous@somedomain.com"
            username = "anonymous"
            token = request.headers.get("Authorization")
            if token:
                if not token.startswith("Bearer "):
                    return jsonify({"error": "Invalid authorization format"}), 400
                token_value = token.split(" ", 1)[1]
                _, email = get_username(token_value)
                username = email.split('@')[0]

            try:
                # Mengirim permintaan ke Solr
                response = requests.get(solr_url, params=params)
                response.raise_for_status()

                # Parsing data dari respon JSON
                data = response.json()
                docs = data.get("response", {}).get("docs", [])
                datasets = [
                    {
                        "id": doc.get("id"),
                        "name": doc.get("name"),
                        "title": doc.get("title"),
                        "url": doc.get("url"),
                        "notes": doc.get("notes"),
                        "license_id": doc.get("license_id"),
                        "metadata_created": doc.get("metadata_created"),
                        "metadata_modified": doc.get("metadata_modified"),
                        "state": doc.get("state"),
                        "organization": doc.get("organization")
                    }
                    for doc in docs
                ]
                return jsonify({"success": True, "datasets": datasets})

            except requests.RequestException as e:
                print(f"Error fetching similar datasets: {e}")
                return jsonify({"success": False})


        #------------------------------------------------ collaborator ------------------------------------------------#
        @blueprint_customapi.route('/get-package-collaborator-org-list', methods=['POST'])
        def get_package_collaborator_org_list():
            try:
                payload = request.get_json()
                package_id = payload.get('package_id','')

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]

                context = {'user': username, 'ignore_auth': True}   
                data = package_collaborator_org_list(package_id)

                return jsonify({"Success": True, "data": data, "package_id": package_id})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/set-add-package-collaborator', methods=['POST'])
        def set_add_package_collaborator():
            try:
                payload = request.get_json()
                package_id = payload.get('package_id')
                user_id = payload.get('user_id')
                capacity = payload.get('capacity','member')

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]

                data = add_package_collaborator(package_id, user_id, capacity)

                return jsonify({"Success": True, "data": data})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400
        
        @blueprint_customapi.route('/set-update-package-collaborator', methods=['POST'])
        def set_update_package_collaborator():
            try:
                payload = request.get_json()
                package_id = payload.get('package_id')
                user_id = payload.get('user_id')
                capacity = payload.get('capacity','member')

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]

                data = update_package_collaborator(package_id, user_id, capacity)

                return jsonify({"Success": True, "data": data})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/set-delete-package-collaborator', methods=['POST'])
        def set_delete_package_collaborator():
            try:
                payload = request.get_json()
                package_id = payload.get('package_id')
                user_id = payload.get('user_id')

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]

                data = delete_package_collaborator(package_id, user_id)

                return jsonify({"Success": True, "data": data})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        #------------------------------------ organization member ------------------------------------#
        @blueprint_customapi.route('/get-member-list', methods=['POST'])
        def get_member_list():
            try:
                payload = request.get_json()
                id = payload.get('id','')
                object_type = payload.get('object_type','user')

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]

                context = {'user': username, 'ignore_auth': True}
                params = {'id': id, 'object_type':object_type}   
                members = get_action('member_list')(context, params)

                enriched_data = []
                for member in members:
                    user_id, object_type, capacity = member
                    user_profile = get_profile_by_id(user_id)
                    if user_profile:
                        enriched_data.append({
                            "id": user_profile["id"],
                            "name": user_profile["name"],
                            "fullname": user_profile["fullname"],
                            "email": user_profile["email"],
                            "created": user_profile["created"],
                            "state": user_profile["state"],
                            "capacity": capacity
                        })

                return jsonify({"Success": True, "data": enriched_data})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/set-add-member', methods=['POST'])
        def set_add_member():
            try:
                payload = request.get_json()
                id = payload.get('id','')
                user_id = payload.get('user_id','')
                capacity = payload.get('capacity','member')
                object_type = 'user'

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]
                
                context = {'user': username, 'ignore_auth': True}
                params = {'id': id, 'object': user_id, 'object_type':object_type, 'capacity': capacity}   
                response = get_action('member_create')(context, params)

                return jsonify({"Success": True, "data": params})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/set-update-member', methods=['POST'])
        def set_update_member():
            try:
                payload = request.get_json()
                id = payload.get('id','')
                user_id = payload.get('user_id','')
                capacity = payload.get('capacity','member')
                object_type = 'user'

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]
                
                context = {'user': username, 'ignore_auth': True}
                params = {'id': id, 'object': user_id, 'object_type':object_type, 'capacity': capacity}   
                response = get_action('member_create')(context, params)

                return jsonify({"Success": True, "data": params})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

        @blueprint_customapi.route('/set-delete-member', methods=['POST'])
        def set_delete_member():
            try:
                payload = request.get_json()
                id = payload.get('id','')
                user_id = payload.get('user_id','')
                object_type = 'user'

                email = "anonymous@somedomain.com"
                username = "anonymous"
                token = request.headers.get("Authorization")
                if token:
                    if not token.startswith("Bearer "):
                        return jsonify({"error": "Invalid authorization format"}), 400
                    token_value = token.split(" ", 1)[1]
                    _, email = get_username(token_value)
                    username = email.split('@')[0]
                
                context = {'user': username, 'ignore_auth': True}
                params = {'id': id, 'object': user_id, 'object_type':object_type}   
                response = get_action('member_delete')(context, params)

                return jsonify({"Success": True, "data": params})
            except Exception as e:
                return jsonify({"error": f"{str(e)}"}), 400

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