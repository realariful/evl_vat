# -*- coding: utf-8 -*-
{
    'name': "Hybrid report",

    'summary': """
        Attendance Report connected with leave,global leaves and holiday""",

    'description': """
        Hybrid Attendace Report
    """,

    'author': "Ergo Ventures Pvt. Ltd",
    'website': "https://www.ergo-ventures.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['evl_movement','base','hr','hr_attendance'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/attendance_report_views.xml',
        'views/views.xml',
        'views/cron_actions.xml',
        'views/res_config_settings_views.xml'
        # 'views/attendance_report_config.xml',
        # 'views/global_leave_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}