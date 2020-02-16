
{
    'name': 'Loan Management',
    'version': '',
    'summary': '',
    'description': """
        
        """,
    'category': '',
    'author': "",
    'company': '',
    'maintainer': '',
    'website': "",
    'depends': [
        'base', 'evl_employee','om_hr_payroll', 'hr','evl_payroll_advance', 'account',
    ],
    'data': [
        'security/security.xml',
        'views/hr_loan_seq.xml',
        'data/salary_rule_loan.xml',
        'views/hr_loan.xml',
        'views/hr_payroll.xml',
        'security/acces_rule_and_groups.xml',
        'security/ir.model.access.csv',

    ],
    'demo': [],
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
