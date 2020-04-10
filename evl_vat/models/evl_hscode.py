# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _


class HsCode(models.Model):
    _name = 'evl.hscode'
    _description = 'EVL HS Code for Bangladesh'
    _rec_name = 'hscode'

    name = fields.Char(string="Sequence", required=True, copy=False,readonly=True, index=True, default=lambda self: ('New'))
    hscode = fields.Char(string="HS Code", required=True, default=None)
    description = fields.Char(string="Description", required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

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
        
    
    vat_cd = fields.Float(string="CD", required=True)
    vat_sd = fields.Float(string="SD", required=True)
    vat_rd = fields.Float(string="RD", required=True)
    vat = fields.Many2one(string="VAT", comodel_name='account.tax', domain="[('name','like','VAT')]")
    ait = fields.Float(string="AIT", required=True)
    vat_atv = fields.Float(string="ATV", required=True)
    vat_at = fields.Float(string="AT")
    vat_tti = fields.Float(string="TTI")
    vat_exd = fields.Float(string="EXD")
    status = fields.Boolean(string='Status',default=True)

    # vat_cd = fields.Many2one(string="CD", comodel_name='account.tax', domain="[('name','like','CD')]")
    # vat_sd = fields.Many2one(string="SD", comodel_name='account.tax', domain="[('name','like','SD')]")
    # vat_rd = fields.Many2one(string="RD", comodel_name='account.tax', domain="[('name','like','RD')]")
    # vat = fields.Many2one(string="VAT", comodel_name='account.tax', domain="[('name','like','VAT')]")
    # ait = fields.Many2one(string="AIT", comodel_name='account.tax', domain="[('name','like','AIT')]")
    # vat_atv = fields.Many2one(string="ATV", comodel_name='account.tax', domain="[('name','like','ATV')]")
    # vat_at = fields.Float(string="AT")
    # vat_tti = fields.Float(string="TTI")
    # vat_exd = fields.Float(string="EXD")
    # status = fields.Boolean(string='Status',default=True)

    vat_category = fields.Selection(
                            [
                                ('zero', 'Zero VAT (শুন্যহার বিশিষ্ট পণ্য/সেবা)'),
                                ('exempt', 'Exempted VAT (অব্যাহতিপ্রাপ্ত পণ্য/সেবা)'),
                                ('standard', 'Standard VAT (আদর্শ হারের পণ্য/সেবা)'),
                                ('not_standard', 'Others VAT not standard (আদর্শ হার ব্যতীত অন্যান্য হারের পণ্য/সেবা)'),
                                ('specific', 'Specific VAT (সুনির্দিষ্ট কর ভিত্তিক পন্য/সেবা)'),

                                ('not_reyat', 'Reyat not applicable (Local Purchase) from Turnover Company or Unregistered Company'), #Trunover Company or Unregistered Company-(Local Purchase)'),
                                ('not_reyat_ser', 'Reyat not applicable excluding zero vat,specific vat, standard vat (রেয়াতযোগ্য নয় এরূপ পণ্য/সেবা (যে সকল করদাতা শুধুমাত্র অব্যাহতিপ্রাপ্ত/সুনির্দিষ্ট কর/আদর্শ হার ব্যতীত অন্যান্য হারের পণ্য/সেবা সরবরাহ করেন))'),
                            ], 
                            
                            string='Vat Category', store=True,
                            default='standard')
    
    # zero_vat = fields.Boolean(string='Zero VAT (শুন্যহার বিশিষ্ট পণ্য/সেবা)',default=False)#Local and Foreign
    # exempted_vat = fields.Boolean(string='Exempted VAT (অব্যাহতিপ্রাপ্ত পণ্য/সেবা)',default=False) #Local and Foreign
    # standard_vat = fields.Boolean(string='Standard VAT (আদর্শ হারের পণ্য/সেবা)',default=False)#Local and Foreign
    # others_not_standard = fields.Boolean(string='Others VAT not standard (আদর্শ হার ব্যতীত অন্যান্য হারের পণ্য/সেবা)',default=False)#Local and Foreign
    # specific_vat = fields.Boolean(string='Specific VAT (সুনির্দিষ্ট কর ভিত্তিক পন্য/সেবা)',default=False) #Local and Foreign
    # reyat_not =  fields.Boolean(string='Reyat not applicable (Local Purchase) from Turnover Company or Unregistered Company', default=False) #Trunover Company or Unregistered Company-(Local Purchase)
    # reyat_not_others =  fields.Boolean(string='Reyat not applicable excluding zero vat,specific vat, standard vat (রেয়াতযোগ্য নয় এরূপ পণ্য/সেবা (যে সকল করদাতা শুধুমাত্র অব্যাহতিপ্রাপ্ত/সুনির্দিষ্ট কর/আদর্শ হার ব্যতীত অন্যান্য হারের পণ্য/সেবা সরবরাহ করেন))',default=False) #Local and Foreign Purchase



    

    hscode_line = fields.Many2one(
        string='HSCode Line',
        comodel_name='product.template',
    )
    
    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
           vals['name'] = self.env['ir.sequence'].next_by_code('evl.hscode') or _('New')
        result = super(HsCode, self).create(vals)
        return result

