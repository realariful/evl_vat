# -*- coding: utf-8 -*-
{
    'name': "evl_transfer",

    'summary': """
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "https://www.ergo-ventures.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['calendar', 'resource','base','hr'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/groups.xml',
        'security/transfer_access_rule.xml',
        'security/ir.model.access.csv',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}