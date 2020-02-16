# -*- coding: utf-8 -*-
{ 
    'name': "Training Management",

    'summary': """Ergo Ventures Pvt. Ltd.""",

    'description': """
        Ergo Ventures Pvt. Ltd.
    """,

    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "http://www.ergo-ventures.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml', 
        'views/evl_training_views.xml',        
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
