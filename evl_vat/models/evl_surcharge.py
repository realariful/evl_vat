#-*- coding: utf-8 -*-


from odoo import models, fields, api
import datetime

from odoo import api, fields, models, _
from odoo.tools.misc import get_lang

from datetime import datetime,timedelta

# Outside the model
def get_years():
    
    year_list = []
    for i in range(2015, 2099):
        year_list.append((str(i), str(i)))
    return year_list


class EvlPayments(models.Model):
    _name = 'evl.surcharge'
    _description = 'Surcharge Voucher'
    _rec_name = 'name'

    name = fields.Char(string="Name", required=True, copy=False,readonly=True, index=True, default=lambda self: ('New'))
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    month = fields.Selection(
                        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                        string='Ledger Month', required=True)
    year = fields.Selection(get_years(), string='Ledger Year', dafault='10', required=True)

    date_submit = fields.Date('Date', required=True)  
    amount = fields.Monetary(currency_field='company_currency_id', required=True)
    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
    description =  fields.Char('Description')

    surcharge_type = fields.Selection(
                        [
                        ('pen', 'Penalty and Fine'),
                        ('dev', 'Development Surcharge'), 
                        ('info', 'Information Techonology Development Surcharge'), 
                        ('health', 'Health Protection Surcharge'), 
                        ('env', 'Environment Protecttion Surcharge'),
                        ]
                        ,string='Surcharge Type', required=True)

    debit_account_id = fields.Many2one('account.account', string='Debit account', domain=[('deprecated', '=', False)])
    credit_account_id = fields.Many2one('account.account', string='Credit account', domain=[('deprecated', '=', False)])

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
           vals['name'] = self.env['ir.sequence'].next_by_code('evl.surcharge') or _('New')
        result = super(EvlPayments, self).create(vals)
        return result