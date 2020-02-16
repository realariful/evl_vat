# -*- coding: utf-8 -*-
{
    'name': "Leave Management",

    'summary': """Leave Management Module""",

    'description': """
        Leave Management Module.
    """,

    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "http://www.ergo-ventures.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_holidays'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/security.xml',        
        'security/ir.model.access.csv',
        'views/change_timeoff.xml',
        'views/hr_views_extend.xml',
        'views/hr_views_allocation_extend.xml',
        'views/hr_leave_extend.xml',       
        'views/hr_leave_views_extend.xml',
        'views/evl_leave_type.xml',
        'wizard/hr_holidays_summary_employees_views.extend.xml',
       
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
