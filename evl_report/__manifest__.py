# -*- coding: utf-8 -*-
{
    'name': "Report Management",

    'summary': """Report Management""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "http://www.ergo-ventures.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','hr'],

    # always loaded
    'data': [
        'wizards/evl_report.xml',
        'security/ir.model.access.csv',
        'views/evl_training_views.xml',
        'security/groups.xml',
        'security/security.xml',
        'reports/report.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
