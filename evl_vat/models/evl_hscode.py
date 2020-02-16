# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
# from datetime import date, datetime
# from dateutil.relativedelta import relativedelta
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class HsCode(models.Model):
    _name = 'evl.hscode'
    _description = 'EVL HS Code for Bangladesh'
    _rec_name = 'hscode'

    name = fields.Char(string="Sequence", required=True, copy=False,readonly=True, index=True, default=lambda self: ('New'))
    hscode = fields.Char(string="HS Code", required=True, default=None)
    description = fields.Char(string="Description", required=True)

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'BD')], limit=1)
        return country

    country = fields.Many2one(
        string='Country',
        comodel_name='res.country',
        ondelete='restrict',        
        default=_get_default_country
        )
        
    
    vat_cd = fields.Float(string="CD")
    vat_sd = fields.Float(string="SD")
    vat = fields.Float(string="VAT")
    ait = fields.Float(string="AIT")
    vat_rd = fields.Float(string="RD")
    vat_at = fields.Float(string="AT")
    vat_tti = fields.Float(string="TTI")
    vat_exd = fields.Float(string="EXD")
    vat_atv = fields.Float(string="ATV")
    status = fields.Boolean(
        string='Status',default=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
           vals['name'] = self.env['ir.sequence'].next_by_code('evl.hscode') or _('New')
        result = super(HsCode, self).create(vals)
        return result
