# -*- coding: utf-8 -*-
{
    'name': "Attendance Management (Main Server)",

    'summary': """
        Ergo Ventures Pvt. Ltd.""",

    'description': """
        Ergo Ventures Pvt. Ltd.

    """,
    'author': "Ergo Ventures Pvt. Ltd",
    'website': "https://www.ergo-ventures.com/",
    'category': 'Uncategorized',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_attendance'],

    # always loaded
    'data': [
        'views/groups.xml',
        'views/views.xml',
        'views/actions.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],

    # 'qweb': ['static/one.xml'],

}
