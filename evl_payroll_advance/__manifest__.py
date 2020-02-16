
{
    'name': 'Advance Salary',
    'version': '',
    'summary': 'Advance Salary In HR',
    'description': """
        .
        """,
    'category': '',
    'author': "Ergo Ventures Pvt. Ltd.",
    'website': "https://www.ergo-ventures.com/",
    'depends': [
        'hr','om_hr_payroll', 'account', 'hr_contract',
    ],
    'data': [
        'views/hr_payroll_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/salary_structure.xml',
        'views/salary_advance.xml',
        'views/hr_payroll_advance_batch.xml',
        'views/bulk_custom_compute.xml',
        'security/security_payroll_models.xml',
        
    ],
    'demo': [],
    
}

