# -*- coding: utf-8 -*-
{
    'name': "Appraisal",

    'summary': """
        Custom Workflow For Appraisal""",

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
    'depends': ['base','hr', 'calendar', 'survey'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
        'security/appraisal_access_rule.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}