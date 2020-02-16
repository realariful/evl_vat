# -*- coding: utf-8 -*-
{
    'name': "VAT Management",

    'summary': """VAT Management""",

    'description': """
        VAT Management Application
    """,

    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "http://www.ergo-ventures.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','hr','mrp'],

    # always loaded
    'data': [
                'wizards/evl_report.xml',
        'views/evl_vat_menus.xml',  

        
        'views/evl_hscode_views.xml', 

        'views/evl_vat_report_views.xml', 
        'security/groups.xml',
        'security/security.xml',
        'reports/report.xml',
        'reports/report_mushak_input_output.xml',
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/mrp_bom_view_extend.xml'
        
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}
