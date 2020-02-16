# -*- coding: utf-8 -*-
{
    'name': "Expenses Management",

    'summary': """
       Expenses Management.""",

    'description': """
        This module Expenses customization with specific workflow.
    """,

    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "",
    'category': 'Account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account', 'hr'],

    # always loaded
    'data': [
        'security/expenses_security.xml',
        'security/ir.model.access.csv',
        'views/expenses_type_views.xml',
        'views/account_expenses_views.xml',
        'views/expense_bank_payments_sequence.xml',
        'views/expense_bank_payments_views.xml',
        'views/expenses_menus.xml',
        'views/account_move_form_views.xml',
        'views/expenses_bulk_actions.xml',
    
    ],
}