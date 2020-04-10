#-*- coding: utf-8 -*-


from odoo import models, fields, api
import datetime

from odoo import api, fields, models, _
from odoo.tools.misc import get_lang

from datetime import datetime,timedelta

def last_day_of_month(any_day):
    import datetime
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)

def get_years():
    year_list = []
    crn_year = datetime.now().year
    for i in range(2019, crn_year+1):
        year_list.append((str(i), str(i)))
    return year_list


class EvlPayments(models.Model):
    _name = 'evl.payments'
    _description = 'Payments'
    _rec_name = 'name'

    name = fields.Char(string="Sequence", required=True, copy=False,readonly=True, index=True, default=lambda self: ('New'))
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    month = fields.Selection(
                        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                        string='Month', required=True)
    year = fields.Selection(get_years(), string='Year', dafault='10', required=True)
    date_submit = fields.Date('Date', required=True)  
    purpose = fields.Selection([('vat', 'VAT'), ('sd', 'SD'), ('surcharge', 'Surcharge'),
                                ('vatin', 'Interest for Unpaid VAT'), 
                                ('sdin', 'Interest for Unpaid SD'),
                                ('ed','Excise duty')], string='Purpose', required=True)
    
    challan = fields.Char('Challan', required=True)
    amount = fields.Monetary(currency_field='company_currency_id', required=True)
    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda x: x.env.company.currency_id)
    payment_method = fields.Selection([('cash', 'Cash'), ('cheque', 'Cheque'), ('bank', 'Bank'), ('card', 'Card'),], string='Payment Method', required=True)
    bank =  fields.Char('Bank', required=True)
    branch =  fields.Char('Branch', required=True)
    description =  fields.Char('Description')
    com_name = fields.Char('Name')
    address = fields.Char('Address')
    note = fields.Char('Note')

    acc_code = fields.Char('Account code')

    surcharge_type = fields.Selection(
                        [
                        ('none', 'None'),
                        ('pen', 'Penalty and Fine'),
                        ('dev', 'Development Surcharge'), 
                        ('info', 'Information Techonology Development Surcharge'), 
                        ('health', 'Health Protection Surcharge'), 
                        ('env', 'Environment Protecttion Surcharge'),
                        ],
                        string='Surcharge Type', required=True,
                        default='none'
                        )
   

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
           vals['name'] = self.env['ir.sequence'].next_by_code('evl.payments') or _('New')
        result = super(EvlPayments, self).create(vals)
        return result