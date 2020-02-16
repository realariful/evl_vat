# -*- coding: utf-8 -*-
{
    'name': "Requisition Management",

    'summary': """
       Requisition Management.""",

    'description': """
        This module contains requisition related customization with specific workflow.
    """,

    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "",
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase', 'hr', 'uom', 'stock', 'purchase_stock', 'purchase_requisition', 'purchase_requisition_stock'],

    # always loaded
    'data': [
        'security/requisition_security.xml',
        'security/ir.model.access.csv',
        'views/evl_requisition_views.xml',
        'views/evl_requisition_menus.xml',
        'views/evl_requisition_sequences.xml',
        'data/evl_requisition_data.xml',
        'views/inherit_stock_moves_views.xml',
        'views/inherit_purchase_requi_views.xml',
        'views/inherit_purchase_order_views.xml',
    
    ],
}