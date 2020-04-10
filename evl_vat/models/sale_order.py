# -*- coding: utf-8 -*-
from odoo import api, fields, models,exceptions, _
from pytz import timezone, UTC
from datetime import datetime,timedelta
import pytz
from odoo.exceptions import UserError



def get_local_date(self, utctime):
    user_tz = self.env.user.tz or pytz.utc
    if str(user_tz) == 'UTC':
        raise UserError(_("Please setup timezone for you."))
    else:
        local = pytz.timezone(user_tz)
        local_date = utctime.astimezone(local).date()
        return local_date

class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    sale_type =  fields.Selection(
                        [('local', 'Local'),
                        ('foreign', 'Foreign'),], string='Sale Type(Local/Foreign)', store=True,
                        compute='compute_sale_type', )  
    sale_type2 =  fields.Selection(
                        [('direct', 'Direct Sale'),
                        ('indirect', 'Indirect Sale'),], string='Sale Type',default='direct')
    sale_epz = fields.Boolean(string='Via EPZ',default=False)
    epz_name = fields.Char(string='EPZ Name')
    challan = fields.Char(string='Challan No',store=True)
    date_order = fields.Datetime(string='Order Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")  
    

    # compute_status = fields.Boolean(string="Compute Status", default="True")

    # @api.model 
    # @api.depends('fiscal_position_id','sale_epz') 
    # def compute_sale_type2(self):
    #     for rec in self:
    #         if rec.fiscal_position_id.name == 'Foreign Sale':
    #             if rec.sale_epz == True:
    #                 rec.sale_type2 = 'indirect'
    #             else:
    #                 rec.sale_type2 = 'direct'


    @api.model
    @api.depends('fiscal_position_id') 
    def compute_sale_type(self):
        for rec in self:
            if rec.fiscal_position_id.name == 'Foreign Sale':
                rec.sale_type = 'foreign'
                for line in rec.order_line:
                    line.tax_id = None
            else:
                rec.sale_type = 'local'

    @api.model
    def action_confirm(self, values):
        recs = self.env['sale.order'].search([('id','=',values[0])])

        # for rec in recs:
        quotation_date = recs.date_order
        imediate_obj = self.env['stock.immediate.transfer']
        res = super(SaleOrderExtend,recs).action_confirm()
        # rec.action_confirm()
        recs.date_order = quotation_date

        # import pdb; pdb.set_trace()
        for order in recs:
            order.date_order = quotation_date
            warehouse = order.warehouse_id
            if warehouse.is_delivery_set_to_done and order.picking_ids: 
                for picking in order.picking_ids:
                    picking.action_assign()
                    picking.action_confirm()
                    for mv in picking.move_ids_without_package:
                        mv.quantity_done = mv.product_uom_qty
                    picking.button_validate()
                    picking.date_done = picking.date = picking.schedule_date = quotation_date
                    # picking.action_done()
                    # imediate_rec = imediate_obj.create({'pick_ids': [(4, order.picking_ids.id)]})
                    # imediate_rec.process()
            
            if warehouse.create_invoice and not order.invoice_ids:
                # import pdb; pdb.set_trace()
                inv = order._create_invoices() 
                inv.date = inv.invoice_date = inv.invoice_date_due = get_local_date(order,quotation_date)

            if warehouse.validate_invoice and order.invoice_ids:
                for invoice in order.invoice_ids:
                    invoice.action_post()

            return res 

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sale_subtype = fields.Selection(
                        [   ('zero', 'Zero VAT'),
                            ('exempt', 'Exempted VAT'),
                            ('standard', 'Standard VAT'),
                            ('high', 'Highest Retail VAT'),
                            ('specific', 'Specific VAT'),
                            ('not_reyat', 'Non Reyat'),
                            ('retail', 'Retail or Wholesale'),           

                        ] , default='standard', string='Sale Sub Type', store=True,)
    sale_type =  fields.Selection(
                        [('local', 'Local'),
                        ('foreign', 'Foreign'),], string='Sale Type', store=True,
                        compute='compute_sale_type')
  
    sale_type2 =  fields.Selection(
                        [('direct', 'Direct Sale'),
                        ('indirect', 'Indirect Sale'),], string='Sale Type2', 
                        compute="compute_sale_type", 
                        )
    taxes_id = fields.Many2many('account.tax', compute="_compute_taxes_id", 
                                inverse='_inverse_taxes_id',string='Taxes Id', 
                                domain=['|', ('active', '=', False), ('active', '=', True)],                                
                                #context={'purchase_type': purchase_type }
                                )

    customer_cat = fields.Selection(
                        [   ('none', 'None'),
                            ('turnover', 'Turnover Company'),
                            ('unregistered', 'Unregistered Company'),                            
                        ] ,default='none',string='Supplier Category', store=True,)


    vat_sd = fields.Monetary("VAT Sd")
    @api.model 
    
    # @api.onchange('product_id')
    # def compute_tax_type(self):
    #     for rec in self:
    #         if rec.order_id.fiscal_position_id.name == 'Foreign Sale':
    #             rec.tax_id = None
    @api.depends('product_id') 
    def compute_sale_type(self):
        for rec in self:
            if rec.order_id.fiscal_position_id.name == 'Foreign Sale':
                rec.sale_type = 'foreign'
                if rec.order_id.sale_epz == True:
                    rec.sale_type2 = 'indirect'
                    rec.sudo().write({'sale_subtype': 'zero'})
                if rec.order_id.sale_epz == False:                    
                    rec.sale_type2 = 'direct'
                    rec.sudo().write({'sale_subtype': 'zero'})
                    # import pdb; pdb.set_trace()
            else:
                rec.sale_type = 'local'
                if rec.order_id.fiscal_position_id.name == 'Local Sale':
                    if rec.product_id.hscode.vat_category in ('zero','exempt','standard','specific'):
                        rec.sale_subtype = rec.product_id.hscode.vat_category
                    else:
                        rec.product_id.hscode.vat_category = 'high'

    # @api.model 
    # @api.depends('product_id') 
    # def compute_sale_type2(self):
    #     for rec in self:
    #         if rec.order_id.fiscal_position_id.name == 'Foreign Sale':
    #             if rec.sale_epz == True:
    #                 rec.sale_type2 = 'indirect'
    #                 rec.sudo().write({'sale_subtype': 'zero'})
    #             if rec.sale_epz == False:
                    
    #                 rec.sale_type2 = 'direct'
    #                 rec.sudo().write({'sale_subtype': 'zero'})
    #                 import pdb; pdb.set_trace()
    
    # @api.model 
    # @api.depends('product_id') 
    # def compute_sale_subtype(self):
    #     for rec in self:  



    
    # @api.onchange('purchase_price','sale_type','product_id','order_id.fiscal_position_id')
    # def _compute_price_unit(self):
    #     if self.product_id:
    #         self.purchase_subtype = self.product_id.hscode.vat_category
    #         if self.purchase_subtype == 'not_reyat' and self.sale_type == 'local':
    #             if self.partner_id.vat == False:
    #                 self.supplier_cat = 'unregistered'
    #             else:
    #                 self.supplier_cat = 'turnover'
 
