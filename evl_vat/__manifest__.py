# -*- coding: utf-8 -*-
{
    'name': "VAT Management",
    'summary': """VAT Management""",
    'description': """VAT Management Application""",
    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "http://www.ergo-ventures.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','product','hr','mrp','account','purchase','sale','l10n_generic_coa','sale_management','om_account_accountant'],

    'external_dependencies': {
        'python': ['bangla','inflect'],
    },
    
    'data': [
        'data/postgres_log.xml',

        'views/mrp_bom_view_extend.xml',
	    'reports/report_mushak_treasury.xml',               
        'reports/report_mushak_input_output.xml',
        'reports/report_mushak_purchase.xml',
        'reports/report_mushak_sale_book.xml' ,
        'reports/report_mushak_purchase_sale_book.xml',
        'reports/report_mushak_tax_book.xml',
        'reports/report_mushak_credit_note.xml',
        'reports/report_mushak_debit_note.xml',
        'reports/report_mushak_transfer_book.xml',
        'reports/report_mushak_contract.xml',
        'reports/report_mushak_twolakhs.xml',
        'reports/report_mushak_nine_one.xml',
        'reports/report_mushak_nine_two.xml',

        'wizards/evl_report.xml',
        'views/evl_vat_menus.xml', 
        'views/sale_order_extend.xml'  ,
        'views/res_company_extend.xml',   
        'data/account_tax.xml',
       
        'views/evl_payments.xml',        
        'wizards/tax_adjustments.xml',
        'views/evl_hscode_views.xml', 
        'views/evl_surcharge.xml',
        'views/evl_vdssale.xml',
        'views/evl_vdspayments.xml',
        'security/groups.xml',
        
        'reports/report.xml',   
        'data/ir_sequence_data.xml',
        'data/cement_data.xml',
        'security/ir.model.access.csv',
        
        'views/res_partner_view_form_extend.xml',
        'views/product_template_extend.xml',
        'views/purchase_order_extend.xml',
        'views/view_tax_form_extend.xml',  
	    'views/stock_warehouse.xml',   

        'views/dashboard_views.xml',

        'views/audit_log_view.xml',
        'views/audit_rule_view.xml', 
        'views/audit_log.xml',

        'security/security.xml',


        
             
        
        

        
    ],

    'qweb': ["static/src/xml/hrms_dashboard.xml",
                # "static/src/xml/audit_trail.xml"
            ],
    'images': ["static/description/banner.gif"],
    'license': "AGPL-3",
}
