import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.model import Package
from ckan.model.meta import Session
from flask import Blueprint, jsonify


class CustomapiPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    # plugins.implements(plugins.IBlueprint)

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

def hello_api_action(context, data_dict):
    """
    Endpoint sederhana
    """
    return {'message': 'Hello, API!', 'success': True}