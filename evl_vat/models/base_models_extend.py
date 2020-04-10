# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import copy 
from itertools import groupby

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    taxes_id = fields.Many2many('account.tax', compute="_compute_taxes_id", 
                                inverse='_inverse_taxes_id',string='Taxes Id', 
                                domain=['|', ('active', '=', False), ('active', '=', True)],                                
                                #context={'purchase_type': purchase_type }
                                )
    purchase_type =  fields.Selection(
                        [('local', 'Local'),
                        ('foreign', 'Foreign'),], string='Purchase Type', store=True,
                        compute='_compute_purchase_type')
    purchase_price = fields.Float(string="Purchase Price", required=True, digits='Product Price')  
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    purchase_subtype = fields.Selection(
                        [   ('zero', 'Zeo VAT'),
                            ('exempt', 'Exempted VAT'),
                            ('standard', 'Standard VAT'),
                            ('not_standard', 'Non-Standard VAT'),
                            ('specific', 'Specific VAT'),
                             ('not_reyat', 'Non Reyat'),
                             ('not_reyat_ser', 'Non Reyat Products or Services'),                            
                        ] ,default='standard',string='Purchase Sub Type', store=True,)
    supplier_cat = fields.Selection(
                        [   ('none', 'None'),
                            ('turnover', 'Turnover Company'),
                            ('unregistered', 'Unregistered Company'),                            
                        ] ,default='none',string='Supplier Category', store=True,)
    
    @api.onchange('purchase_price','purchase_type','product_id','order_id.fiscal_position_id')
    def _compute_price_unit(self):
       
        if self.product_id:
            self.purchase_subtype = self.product_id.hscode.vat_category
            if self.purchase_subtype == 'not_reyat' and self.purchase_type == 'local':
                if self.partner_id.vat == False:
                    self.supplier_cat = 'unregistered'
                else:
                    self.supplier_cat = 'turnover'
        

        for rec in self:
            if rec.order_id.fiscal_position_id.name == 'Local Purchase':
                rec.price_unit = rec.purchase_price
            if rec.order_id.fiscal_position_id.name == 'Foreign Purchase':
                # import pdb; pdb.set_trace()
                rec.vat_cd =   rec.purchase_price * rec.product_id.hscode.vat_cd/100
                rec.vat_rd =   rec.purchase_price * rec.product_id.hscode.vat_rd/100
                rec.vat_sd =  (rec.purchase_price + rec.vat_cd + rec.vat_rd) * rec.product_id.hscode.vat_sd/100
                rec.price_unit = rec.purchase_price  + rec.vat_sd
                # pur_order = self.env['purchase.order'].search([('id','=',rec.order_id.id)])
                # pur_order.po_vat_cd += rec.vat_cd 
                #-----------New lines added

            # po = self.env['purchase.order'].search([('name','=',self.order_id.name)])
            # if len(po) > 0:
            #     po_id = po.id
            #     po.po_vat_cd = po.po_vat_rd = po.po_vat_sd = po.po_vat_atv = po.po_vat_ait = po.po_vat_vat = 0.0
                
            #     for line in self.env['purchase.order.line'].search([('order_id','=',po_id)]): 
            #         if po.fiscal_position_id.name[0:7].lower() == 'foreign':
            #             line.purchase_price =     rec.purchase_price   
            #             line.vat_cd = line.purchase_price * line.product_id.hscode.vat_cd/100
            #             line.vat_rd = line.purchase_price * line.product_id.hscode.vat_rd/100
            #             line.vat_sd = (line.purchase_price + line.vat_cd + line.vat_rd) * line.product_id.hscode.vat_sd/100
                        
            #             line.vat_vat =  (line.purchase_price + line.vat_cd + line.vat_rd+ line.vat_sd) * line.product_id.hscode.vat.amount/100 
                        
            #             po.po_vat_cd += line.vat_cd
            #             po.po_vat_rd += line.vat_rd               
            #             po.po_vat_sd += line.vat_sd
            #             po.po_vat_atv += line.vat_atv
            #             po.po_vat_ait += line.vat_ait
            #             po.po_vat_vat += line.vat_vat
                # print("------------------DATAS---------------------")
                # print(po.po_vat_cd , po.po_vat_rd , po.po_vat_sd , po.po_vat_atv , po.po_vat_ait , po.po_vat_vat)
    

    vat_cd = fields.Monetary(string="CD")    
    vat_sd = fields.Monetary(string="SD")
    vat_rd = fields.Monetary(string="RD")
    vat_vat = fields.Monetary(string="VAT")
    vat_ait = fields.Monetary(string="AIT")
    vat_atv = fields.Monetary(string="ATV")
    vat_at = fields.Monetary(string="AT")
    vat_tti = fields.Monetary(string="TTI")
    vat_exd = fields.Monetary(string="EXD")
    vat_rebate = fields.Monetary(string="Rebate")



    line_status = fields.Boolean(string="Compute Status", default=False)

    @api.model  
    @api.depends('purchase_type','product_id','order_id.fiscal_position_id')
    def _compute_taxes_id(self):        
        for rec in self:
            if rec.order_id.fiscal_position_id:
                if rec.order_id.fiscal_position_id.name[0:7].lower() == 'foreign':
                    print("foreign")
                    # rec.taxes_id += rec.product_id.hscode.vat_cd
                    # rec.taxes_id += rec.product_id.hscode.vat_rd
                    # rec.taxes_id += rec.product_id.hscode.vat_sd        
                    rec.taxes_id += rec.product_id.hscode.vat
                    # rec.taxes_id += rec.product_id.hscode.ait
                    # rec.taxes_id += rec.product_id.hscode.vat_atv

                    rec.vat_cd = rec.purchase_price * rec.product_id.hscode.vat_cd/100
                    rec.vat_rd = rec.purchase_price * rec.product_id.hscode.vat_rd/100
                    rec.vat_sd = (rec.purchase_price + rec.vat_cd + rec.vat_rd) * rec.product_id.hscode.vat_sd/100
                    rec.vat_vat = (rec.purchase_price + rec.vat_sd ) * rec.product_id.hscode.vat.amount/100
                    rec.vat_ait = rec.purchase_price * rec.product_id.hscode.ait/100
                    rec.vat_exd = rec.product_id.hscode.vat_exd
                    # for tax in rec.taxes_id:
                    #     if tax.name.split(" ")[0] == 'VAT':
                    #         vat_base = 0
                    #         vat_base = rec.purchase_price 
                    #         vat_base += rec.vat_cd if tax.vat_cd == True else 0
                    #         vat_base += rec.vat_rd if tax.vat_rd == True else 0
                    #         vat_base += rec.vat_sd if tax.vat_sd == True else 0
                    #         rec.vat_vat =  vat_base * rec.product_id.hscode.vat.amount/100 
                    #     if tax.name.split(" ")[0] == 'SD':
                    #         vat_base = 0
                    #         vat_base = rec.purchase_price 
                    #         vat_base += rec.vat_cd if tax.vat_cd == True else 0
                    #         vat_base += rec.vat_rd if tax.vat_rd == True else 0
                    #         rec.vat_sd =  vat_base * rec.product_id.hscode.vat.amount/100 
                    #     if tax.name.split(" ")[0] == 'AT' or tax.name.split(" ")[0] == 'ATV':
                    #         vat_base = 0
                    #         vat_base = rec.purchase_price 
                    #         vat_base += rec.vat_cd if tax.vat_cd == True else 0
                    #         vat_base += rec.vat_rd if tax.vat_rd == True else 0
                    #         vat_base += rec.vat_sd if tax.vat_sd == True else 0
                    #         rec.vat_at =  vat_base * rec.product_id.hscode.vat.amount/100 
                    #         rec.vat_atv =  vat_base * rec.product_id.hscode.vat.amount/100                  



                    #rec.vat_vat =  (rec.price_unit + rec.vat_cd+ rec.vat_rd + rec.vat_sd) * rec.product_id.hscode.vat.amount/100           
                    
                    #rec.vat_at =  (rec.price_unit + rec.vat_cd+ rec.vat_rd + rec.vat_sd) * rec.product_id.hscode.vat_at/100
                    #rec.vat_atv = (rec.price_unit + rec.vat_cd+ rec.vat_rd + rec.vat_sd) * rec.product_id.hscode.vat_atv.amount/100
                    #rec.vat_tti = rec.vat_cd + rec.vat_rd + rec.vat_sd + rec.vat_vat + rec.vat_ait + rec.vat_atv 
                    
                elif  rec.order_id.fiscal_position_id.name[0:5].lower() == 'local':
                    print("local")
                    # rec.taxes_id += self.env['account.tax'].search([('name','=','CD 0%')])
                    # rec.taxes_id += self.env['account.tax'].search([('name','=','RD 0%')])
                    # rec.taxes_id += self.env['account.tax'].search([('name','=','SD 0%')])              
                    rec.taxes_id += rec.product_id.hscode.vat
                    # rec.taxes_id += self.env['account.tax'].search([('name','=','AIT 0%')])
                    # rec.taxes_id += self.env['account.tax'].search([('name','=','ATV 0%')])
                    rec.vat_cd = rec.vat_rd = rec.vat_sd = rec.vat_at =  rec.vat_atv = rec.vat_exd = rec.vat_ait = 0.0
                    rec.vat_vat =  (rec.purchase_price + rec.vat_cd+ rec.vat_rd + rec.vat_sd) * rec.product_id.hscode.vat.amount/100                        
                    rec.vat_tti = rec.vat_cd + rec.vat_rd + rec.vat_sd + rec.vat_vat + rec.vat_ait + rec.vat_at 
                else:
                    rec.taxes_id += rec.product_id.hscode.vat

            else:
                rec.taxes_id += rec.product_id.hscode.vat
    @api.model  
    def _inverse_taxes_id(self):        
        for rec in self:
            pass

    @api.model  
    def _compute_purchase_type(self):
        for rec in self:        
            rec.purchase_type = rec.order_id.purchase_type




    @api.model
    def create(self, values):  
        po = self.env['purchase.order'].search([('id','=',values['order_id'])])
        values['date_planned'] = po.date_order
        values['purchase_type'] = po.purchase_type        
        result = super(PurchaseOrderLine, self).create(values)
        # result.sudo().write({'purchase_type': result.order_id.purchase_type})
        return result
    



#-------------------Not need can be removed---------------------------

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for rec in self:
            for line in rec:
                
                vals = line._prepare_compute_all_values()
                taxes = line.taxes_id.compute_all(
                    vals['price_unit'],
                    vals['currency_id'],
                    vals['product_qty'],
                    vals['product'],
                    vals['partner'],
                    vals['purchase_type'])
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
            

    def _prepare_compute_all_values(self):
        for rec in self:
            rec.ensure_one()
            return {
                'price_unit': rec.price_unit,
                'currency_id': rec.order_id.currency_id,
                'product_qty': rec.product_qty,
                'product': rec.product_id,
                'partner': rec.order_id.partner_id,
                'purchase_type':rec.order_id.purchase_type,
            }


    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a purchase order line.

        :param qty: float quantity to bill
        """
        self.ensure_one()
        return {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.product_qty,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'date': self.date_planned,
        }

#------------------------------------------------------

class ResPartnerExtend(models.Model):
    _inherit = 'res.partner'

    supplier_type = fields.Selection(
        [('local', 'Local'),
         ('foreign', 'Foreign'),
         ('both', 'Both'),
        ], string='Type', 
        help="Select Local for Local Supplier.\n Or Select Foreign for foriegn supplier.")


class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    hscode = fields.Many2one('evl.hscode', string="HS Code")
                
class PurchaseOrderExtend(models.Model):
    _inherit = 'purchase.order'

    partner_ref = fields.Char("Bill Of Entry") 
    purchase_type =  fields.Selection(
                        [('local', 'Local'),
                        ('foreign', 'Foreign'),], string='Purchase Type', 
                        default='local', 
                        help="Select Local for Local Purchase.\n Or Select Foreign for foriegn Purchase.")
    po_vat_cd = fields.Monetary(string="CD")    
    po_vat_sd = fields.Monetary(string="SD")   
    po_vat_rd = fields.Monetary(string="RD") 
    po_vat_vat = fields.Monetary(string="VAT") 
    po_vat_ait = fields.Monetary(string="AIT") 
    po_vat_atv = fields.Monetary(string="ATV") #,compute="compute_vats"
    compute_status = fields.Boolean(string="Compute Status", default="True")


    @api.model
    def create(self, values):  
        rec = super(PurchaseOrderExtend, self).create(values)
        fis_id = self.env['account.fiscal.position'].sudo().search([('id','=',values['fiscal_position_id'])])
        if fis_id.name == 'Local Purchase':
            rec.sudo().write({'purchase_type' : 'local'})
            rec.po_vat_cd = rec.po_vat_rd = rec.po_vat_sd = rec.po_vat_atv = rec.po_vat_ait = rec.po_vat_vat = 0.0
            for line in rec.order_line:
                line.purchase_type = rec.purchase_type

                rec.po_vat_cd += line.vat_cd
                rec.po_vat_rd += line.vat_rd               
                rec.po_vat_sd += line.vat_sd
                rec.po_vat_atv += line.vat_atv
                rec.po_vat_ait += line.vat_ait
                rec.po_vat_vat += line.vat_vat

        if fis_id.name == 'Foreign Purchase':
            rec.sudo().write({'purchase_type' : 'foreign'}) 
            for line in rec.order_line:
                line.purchase_type = rec.purchase_type
        return rec
    
    @api.model 
    @api.onchange('purchase_type')
    def _onchange_field(self):
        for rec in self:
            if rec.order_line:
                for line in rec.order_line:
                    line.purchase_type = rec.purchase_type
        
    @api.model    
    @api.onchange('fiscal_position_id')
    def _onchange_field(self):
        for rec in self:
            if rec.fiscal_position_id.name == 'Local Purchase':
                rec.sudo().write({'purchase_type' : 'local'})
            if rec.fiscal_position_id.name == 'Foreign Purchase':
                rec.sudo().write({'purchase_type' : 'foreign'})        

    @api.model    
    @api.depends('order_line.product_id','order_line.purchase_price','order_line.purchase_price')
    def compute_vats(self):
        for rec in self:
            if rec.fiscal_position_id.name == 'Foreign Purchase':
                rec.po_vat_cd = rec.po_vat_rd = rec.po_vat_sd = rec.po_vat_atv = rec.po_vat_ait = rec.po_vat_vat = 0.0
                if len(rec.order_line) > 0:
                    for line in rec.order_line :
                        rec.po_vat_cd += line.vat_cd
                        rec.po_vat_rd += line.vat_rd               
                        rec.po_vat_sd += line.vat_sd
                        rec.po_vat_atv += line.vat_atv
                        rec.po_vat_ait += line.vat_ait
                        rec.po_vat_vat += line.vat_vat
    


    # #-------------------Po to PO Receive
    @api.model
    def button_approve(self, force=False):        
        result = super(PurchaseOrderExtend, self).button_approve(force=force)
        if result != None:
            self.date_approve = self.date_order
        self._create_picking()
        return result

    @api.model
    def button_confirm(self,values):
        recs =  self.env['purchase.order'].search([('id','=',values[0])])

        #Button Confirm
        for order in recs:            
            quotation_date = order.date_order
            if order.state not in ['draft', 'sent']:
                continue
            
            order._add_supplier_to_product()#No date relation            
            order.button_approve()#date_approve changed with button approve function
            
            picking = order.action_view_picking()#Getting nothing
           
            picking = self.env['stock.picking'].search([('id','=',picking['res_id'])])          

            warehouse = self.env['stock.warehouse'].search([('lot_stock_id','=',picking.location_dest_id.id)])            
            
            # order.date_order = quotation_date

            
            if warehouse.is_receipt_set_to_done and picking:  
                picking.action_assign()#No change in date
                picking.action_confirm()#No change in date

                for mv in picking.move_ids_without_package:
                    mv.quantity_done = mv.product_uom_qty
                # print("Hitting stock valuation")
                status = picking.button_validate()  
                # print(status);import pdb; pdb.set_trace()
                # picking.write({'date_done': order.date_order}) if status == True else ''    
                
                # import pdb; pdb.set_trace()
                picking.date_done = picking.date = picking.schedule_date = quotation_date

            



            if warehouse.create_invoice and not order.invoice_ids:
                inv = order._create_invoices() 
                inv.date =  inv.invoice_date = inv.invoice_date_due = order.date_order.date() #get_local_date(self,quotation_date)                        
                
            if warehouse.validate_invoice:
                inv.action_post()
                order.invoice_ids = inv
                order.invoice_status = 'invoiced'
                # order.date_approve = quotation_date


            # #CHaging the value in stock.valuattion.layer
            # for mv in picking.move_ids_without_package:
            #     svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',mv.id)])
            #     if svl:
            #         # import pdb; pdb.set_trace()
            #         svl.create_date = quotation_date
            #         svl.write_date = quotation_date
        return True

    def _prepare_invoice(self):
        self.ensure_one()
        journal = self.env['account.move'].with_context(force_company=self.company_id.id, default_type='in_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': '',
            'type': 'in_invoice',
            'narration': '',
            'currency_id': self.currency_id.id,
            'campaign_id': '',
            'medium_id': '',
            'source_id': '',
            'invoice_user_id': self.user_id and self.user_id.id,
            # 'team_id': '',
            'partner_id': self.partner_id.id,
            # 'partner_shipping_id': False,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'invoice_origin': '',
            'bill_origin': self.id,
            # 'invoice_payment_term_id': self.payment_term_id.id,
            # 'invoice_payment_ref': self.reference,
            # 'transaction_ids': '',#[(6, 0, self.transaction_ids.ids)]
            'invoice_line_ids': [],
        }
        return invoice_vals




    #Sales Invoice
    def _create_invoices(self, grouped=False, final=False):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # 1) Create invoices.
        invoice_vals_list = []
        for order in self:
            pending_section = None

            # Invoice values.
            # import pdb; pdb.set_trace()
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_received, precision_digits=precision):
                    continue
                if line.qty_received > 0 or (line.qty_received < 0 and final):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None
                    
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('partner_id'), x.get('currency_id'))):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    # payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs),
                    'invoice_origin': ', '.join(origins),
                    # 'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Manage 'final' parameter: transform out_invoice to out_refund if negative.
        in_invoice_vals_list = []
        refund_invoice_vals_list = []
        if final:
            for invoice_vals in invoice_vals_list:
                if sum(l[2]['quantity'] * l[2]['price_unit'] for l in invoice_vals['invoice_line_ids']) < 0:
                    for l in invoice_vals['invoice_line_ids']:
                        l[2]['quantity'] = -l[2]['quantity']
                    invoice_vals['type'] = 'in_refund'
                    refund_invoice_vals_list.append(invoice_vals)
                else:
                    in_invoice_vals_list.append(invoice_vals)
        else:
            in_invoice_vals_list = invoice_vals_list

        if invoice_vals['type'] in self.env['account.move'].get_outbound_types():
            invoice_bank_id = self.partner_id.bank_ids[:1]
        else:
            invoice_bank_id = self.company_id.partner_id.bank_ids[:1]

        invoice_vals['invoice_partner_bank_id'] = invoice_bank_id

        # Create invoices.
        moves = self.env['account.move'].with_context(default_type='in_invoice').create(in_invoice_vals_list)
        moves += self.env['account.move'].with_context(default_type='in_refund').create(refund_invoice_vals_list)
        # for move in moves:
        #     move.message_post_with_view('mail.message_origin_link',
        #         values={'self': move, 'origin': move.line_ids.mapped('order_line.order_id')},
        #         subtype_id=self.env.ref('mail.mt_note').id
        #     )

        if len(moves) > 0:
            self.invoice_count += 1
            # self.invoice_status ='invoiced'

        return moves





class AccountTaxInherit(models.Model):
    _inherit = 'account.tax'

    vat_cd = fields.Boolean(string="CD")    
    vat_sd = fields.Boolean(string="SD")    
    vat_rd = fields.Boolean(string="RD")
    # vat_vat = fields.Monetary(string="VAT")
    # vat_ait = fields.Monetary(string="AIT")
    # vat_atv = fields.Monetary(string="ATV")

    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False, handle_price_include=True):
        if not self:
            company = self.env.company
        else:
            company = self[0].company_id

        # 1) Flatten the taxes.
        taxes = self.flatten_taxes_hierarchy()

        # 2) Avoid mixing taxes having price_include=False && include_base_amount=True
        # with taxes having price_include=True. This use case is not supported as the
        # computation of the total_excluded would be impossible.
        base_excluded_flag = False  # price_include=False && include_base_amount=True
        included_flag = False  # price_include=True
        for tax in taxes:
            if tax.price_include:
                included_flag = True
            elif tax.include_base_amount:
                base_excluded_flag = True
            if base_excluded_flag and included_flag:
                raise UserError(_('Unable to mix any taxes being price included with taxes affecting the base amount but not included in price.'))

        # 3) Deal with the rounding methods
        if not currency:
            currency = company.currency_id
        prec = currency.decimal_places

        round_tax = False if company.tax_calculation_rounding_method == 'round_globally' else True
        round_total = True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])
            round_total = bool(self.env.context['round'])
        if not round_tax:
            prec += 5

        # 4) Iterate the taxes in the reversed sequence order to retrieve the initial base of the computation.
        #     tax  |  base  |  amount  |
        # /\ ----------------------------
        # || tax_1 |  XXXX  |          | <- we are looking for that, it's the total_excluded
        # || tax_2 |   ..   |          |
        # || tax_3 |   ..   |          |
        # ||  ...  |   ..   |    ..    |
        #    ----------------------------
        def recompute_base(base_amount, fixed_amount, percent_amount, division_amount):
            return (base_amount - fixed_amount) / (1.0 + percent_amount / 100.0) * (100 - division_amount) / 100

        base = round(price_unit * quantity, prec)
        # For the computation of move lines, we could have a negative base value.
        # In this case, compute all with positive values and negate them at the end.
        sign = 1
        if base < 0:
            base = -base
            sign = -1

        # Store the totals to reach when using price_include taxes (only the last price included in row)
        total_included_checkpoints = {}
        i = len(taxes) - 1
        store_included_tax_total = True
        # Keep track of the accumulated included fixed/percent amount.
        incl_fixed_amount = incl_percent_amount = incl_division_amount = 0
        # Store the tax amounts we compute while searching for the total_excluded
        cached_tax_amounts = {}
        if handle_price_include:
            for tax in reversed(taxes):
                tax_repartition_lines = (
                    is_refund
                    and tax.refund_repartition_line_ids
                    or tax.invoice_repartition_line_ids
                ).filtered(lambda x: x.repartition_type == "tax")
                sum_repartition_factor = sum(tax_repartition_lines.mapped("factor"))

                if tax.include_base_amount:
                    base = recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount)
                    incl_fixed_amount = incl_percent_amount = incl_division_amount = 0
                    store_included_tax_total = True
                if tax.price_include or self._context.get('force_price_include'):
                    if tax.amount_type == 'percent':
                        incl_percent_amount += tax.amount * sum_repartition_factor
                    elif tax.amount_type == 'division':
                        incl_division_amount += tax.amount * sum_repartition_factor
                    elif tax.amount_type == 'fixed':
                        incl_fixed_amount += quantity * tax.amount * sum_repartition_factor
                    else:
                        # tax.amount_type == other (python)
                        tax_amount = tax._compute_amount(base, price_unit, quantity, product, partner) * sum_repartition_factor
                        incl_fixed_amount += tax_amount
                        # Avoid unecessary re-computation
                        cached_tax_amounts[i] = tax_amount
                    if store_included_tax_total:
                        total_included_checkpoints[i] = base
                        store_included_tax_total = False
                i -= 1

        total_excluded = recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount)

        # 5) Iterate the taxes in the sequence order to compute missing tax amounts.
        # Start the computation of accumulated amounts at the total_excluded value.
        base = total_included = total_void = total_excluded

        taxes_vals = []
        i = 0
        cumulated_tax_included_amount = 0

        base_new = {}
        for tax in taxes:          
       
            tax_repartition_lines = (is_refund and tax.refund_repartition_line_ids or tax.invoice_repartition_line_ids).filtered(lambda x: x.repartition_type == 'tax')
            sum_repartition_factor = sum(tax_repartition_lines.mapped('factor'))

            
            #compute the tax_amount
            if (self._context.get('force_price_include') or tax.price_include) and total_included_checkpoints.get(i):
                # We know the total to reach for that tax, so we make a substraction to avoid any rounding issues
                tax_amount = total_included_checkpoints[i] - (base + cumulated_tax_included_amount)
                cumulated_tax_included_amount = 0
            else:



                tax_amount = tax.with_context(force_price_include=False)._compute_amount(
                    base, sign * price_unit, quantity, product, partner)



            # Round the tax_amount multiplied by the computed repartition lines factor.
            tax_amount = round(tax_amount, prec)
            factorized_tax_amount = round(tax_amount * sum_repartition_factor, prec)
            # import pdb; pdb.set_trace()

            if tax.price_include and not total_included_checkpoints.get(i):
                cumulated_tax_included_amount += factorized_tax_amount

            # If the tax affects the base of subsequent taxes, its tax move lines must
            # receive the base tags and tag_ids of these taxes, so that the tax report computes
            # the right total
            subsequent_taxes = self.env['account.tax']
            subsequent_tags = self.env['account.account.tag']
            if tax.include_base_amount:
                subsequent_taxes = taxes[i+1:]
                subsequent_tags = subsequent_taxes.get_tax_tags(is_refund, 'base')

            # Compute the tax line amounts by multiplying each factor with the tax amount.
            # Then, spread the tax rounding to ensure the consistency of each line independently with the factorized
            # amount. E.g:
            #- 0.04 = 0.02 as total_rounding_error to dispatch
            # in lines as 2 x 0.01.
            repartition_line_amounts = [round(tax_amount * line.factor, prec) for line in tax_repartition_lines]
            total_rounding_error = round(factorized_tax_amount - sum(repartition_line_amounts), prec)
            nber_rounding_steps = int(abs(total_rounding_error / currency.rounding))
            rounding_error = round(nber_rounding_steps and total_rounding_error / nber_rounding_steps or 0.0, prec)

            for repartition_line, line_amount in zip(tax_repartition_lines, repartition_line_amounts):

                if nber_rounding_steps:
                    line_amount += rounding_error
                    nber_rounding_steps -= 1

                taxes_vals.append({
                    'id': tax.id,
                    'name': partner and tax.with_context(lang=partner.lang).name or tax.name,
                    'amount': sign * line_amount,
            # Suppose a tax having 4 x 50% repartition line applied on a tax amount of 0.03 with 2 decimal places.
            # The factorized_tax_amount will be 0.06 (200% x 0.03). However, each line taken independently will compute
            # 50% * 0.03 = 0.01 with rounding. It means there is 0.06 
                    'base': round(sign * base, prec),
                    'sequence': tax.sequence,
                    'account_id': tax.cash_basis_transition_account_id.id if tax.tax_exigibility == 'on_payment' else repartition_line.account_id.id,
                    'analytic': tax.analytic,
                    'price_include': tax.price_include or self._context.get('force_price_include'),
                    'tax_exigibility': tax.tax_exigibility,
                    'tax_repartition_line_id': repartition_line.id,
                    'tag_ids': (repartition_line.tag_ids + subsequent_tags).ids,
                    'tax_ids': subsequent_taxes.ids,
                })

                if not repartition_line.account_id:
                    total_void += line_amount

            # Affect subsequent taxes
            if tax.include_base_amount:
                base += factorized_tax_amount

            total_included += factorized_tax_amount
            i += 1

        return {
            'base_tags': taxes.mapped(is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids').filtered(lambda x: x.repartition_type == 'base').mapped('tag_ids').ids,
            'taxes': taxes_vals,
            'total_excluded': sign * (currency.round(total_excluded) if round_total else total_excluded),
            'total_included': sign * (currency.round(total_included) if round_total else total_included),
            'total_void': sign * (currency.round(total_void) if round_total else total_void),
        }


    # def _compute_amount(self):
    #     for line in self:
    #         vals = line._prepare_compute_all_values()
    #         #print(vals)
    #         #{'price_unit': 100.0, 'currency_id': res.currency(55,), 'product_qty': 1.0, 
    #         # product': product.product(6,), 'partner': res.partner(26,)}

    #         #print(line)
    #         #purchase.order.line(<NewId ref='virtual_1305'>,)

    #         # import pdb; pdb.set_trace()

    #         taxes = line.taxes_id.compute_all(
    #             vals['price_unit'],
    #             vals['currency_id'],
    #             vals['product_qty'],
    #             vals['product'],
    #             vals['partner'])


    #         taxes = {'base_tags': [], 'taxes': [
    #             {'id': '<NewId origin=17>', 'name': 'RD 5%', 
    #         'amount': 3.0, 'base': 100.0, 'sequence': 1, 'account_id': False, 
    #         'analytic': False, 'price_include': None, 'tax_exigibility': 'on_invoice',
    #          'tax_repartition_line_id': '<NewId origin=66>', 'tag_ids': [], 
    #          'tax_ids': []}, 
    #             {'id': '<NewId origin=10>', 'name': 'CD 15%', 
    #             'amount': 35.0, 'base': 100.0, 'sequence': 1, 'account_id': False, 
    #             'analytic': False, 'price_include': None, 'tax_exigibility': 
    #             'on_invoice', 'tax_repartition_line_id': '<NewId origin=38>', 
    #             'tag_ids': [], 'tax_ids': []}], 'total_excluded': 100.0, 
    #             'total_included': 120.0, 'total_void': 120.0}
    #         line.update({
    #             'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
    #             'price_total': taxes['total_included'],
    #             'price_subtotal': taxes['total_excluded'],
    #         })



class Picking(models.Model):
    _inherit = "stock.picking"


    @api.model
    def create(self, vals):
        
        defaults = self.default_get(['name', 'picking_type_id'])
        picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
            vals['name'] = picking_type.sequence_id.next_by_id()

        moves = vals.get('move_lines', []) + vals.get('move_ids_without_package', [])

        if moves and vals.get('location_id') and vals.get('location_dest_id'):
            for move in moves:
                if len(move) == 3 and move[0] == 0:
                    move[2]['location_id'] = vals['location_id']
                    move[2]['location_dest_id'] = vals['location_dest_id']
                    picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id'])
                    if 'picking_type_id' not in move[2] or move[2]['picking_type_id'] != picking_type.id:
                        move[2]['picking_type_id'] = picking_type.id
                        move[2]['company_id'] = picking_type.company_id.id
        
        #Changes do not work
        po = self.env['purchase.order'].search([('name','=',vals['origin'])])
        vals['date'] = po.date_order
        res = super(Picking, self).create(vals)
        print("BASE MODEL CREATE PICKING")
        # import pdb; pdb.set_trace()
        
        res._autoconfirm_picking()
        return res

#     def button_validate(self):
#         self.ensure_one()
#         if not self.move_lines and not self.move_line_ids:
#             raise UserError(_('Please add some items to move.'))

#         # If no lots when needed, raise error
#         picking_type = self.picking_type_id
#         precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
#         no_quantities_done = all(float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in self.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
#         no_reserved_quantities = all(float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line in self.move_line_ids)
#         if no_reserved_quantities and no_quantities_done:
#             raise UserError(_('You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities.'))

#         if picking_type.use_create_lots or picking_type.use_existing_lots:
#             lines_to_check = self.move_line_ids
#             if not no_quantities_done:
#                 lines_to_check = lines_to_check.filtered(
#                     lambda line: float_compare(line.qty_done, 0,
#                                                precision_rounding=line.product_uom_id.rounding)
#                 )

#             for line in lines_to_check:
#                 product = line.product_id
#                 if product and product.tracking != 'none':
#                     if not line.lot_name and not line.lot_id:
#                         raise UserError(_('You need to supply a Lot/Serial number for product %s.') % product.display_name)

#         if no_quantities_done:
#             view = self.env.ref('stock.view_immediate_transfer')
            #wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})

      

            # # #-----------------
            # # po = self.env['purchase.order'].sudo().search([('name','=',self.origin),
            # #             ('company_id','=',self.company_id.id)])

            # # invoice = self.env['account.move'].create({            
            # #         'type': 'in_invoice',
            # #         'purchase_id': po.id,
            # #         'partner_id': self.partner_id.id,
            # #         })

            # # print(invoice)
            # #invoice.purchase_order_change()

            # # #--------------------------------
            # po = self.env['purchase.order'].sudo().search([('name','=',self.origin),
            #             ('company_id','=',self.company_id.id)])   

            # inv = po.action_view_invoice()

            # print(po)

            # print("INV")
            # print(inv)
            # print(inv['res_id'])#151

            # acc = self.env['account.move'].search([('id','=',inv['res_id'])])
            # # po_invoice = {
            # #     'partner_id': self.partner_id.id,
            # #     # 'journal_id': self.partner_id.property_account_payable_id.id,
            # #     'state': 'draft',
            # #     'type': 'in_invoice',
            # #     'date': self.date,
            # #     'purchase_id': self.id,   
            # #     'amount_untaxed':po.amount_untaxed,
            # #     'amount_tax': po.amount_tax,
            # #     'amount_total': po.amount_total,
            # #     'fiscal_position_id': po.fiscal_position_id.id,
            # #     'invoice_date': self.date,              
            # # }          



            # # inv = self.env['account.move'].sudo().create(po_invoice)

            # acc.action_post()
            # # if inv:
            # #     inv.sudo().write({
            # #         'state': 'posted',
            # #     })


            # # #Works but button not showug
            # # #--------------------------------------
        #     return {
        #         'name': _('Immediate Transfer?'),
        #         'type': 'ir.actions.act_window',
        #         'view_mode': 'form',
        #         'res_model': 'stock.immediate.transfer',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'res_id': wiz.id,
        #         'context': self.env.context,
        #     }

        # if self._get_overprocessed_stock_moves() and not self._context.get('skip_overprocessed_check'):
        #     view = self.env.ref('stock.view_overprocessed_transfer')
        #     wiz = self.env['stock.overprocessed.transfer'].create({'picking_id': self.id})


        #     return {
        #         'type': 'ir.actions.act_window',
        #         'view_mode': 'form',
        #         'res_model': 'stock.overprocessed.transfer',
        #         'views': [(view.id, 'form')],
        #         'view_id': view.id,
        #         'target': 'new',
        #         'res_id': wiz.id,
        #         'context': self.env.context,
        #     }

        # # Check backorder should check for other barcodes
        # if self._check_backorder():
        #     return self.action_generate_backorder_wizard()
        # self.action_done()

        #------------------Create an invoice


        # print("-------------------")
        # print("------------")

        # # picking_ids = self.env['stock.picking'].search([('origin', '=', self.name)])
        # # for picking in picking_ids:
        # #     picking.action_confirm()
        # #     picking.button_validate()
        # #     self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking.id)]}).process()
        # po_invoice = {
        #     'partner_id': self.partner_id.id,
        #     'account_id': self.partner_id.property_account_payable_id.id,
        #     'state': 'draft',
        #     'type': 'in_invoice',
        #     'date_invoice': self.date_order,
        #     'purchase_id': self.id,
        #     }

        # inv = self.env['account.invoice'].create(po_invoice)
        # inv.purchase_order_change()
        # inv.action_invoice_open()
        # print(inv)
        # print("-----------")

        #_--------------------------------
        #return

            



#----------------Working------------Need to update XML

class ResCompanyExtend(models.Model):
    _inherit = "res.company"

    owner_type =   fields.Selection(
                        [('pro', 'Proprietorship'),
                        ('partner', 'Partnership'),
                        ('pvt', 'Private Limited'),
                        ('plc', 'Public Limited'),
                        ('plc', 'Public Limited'),
                        ('int', 'International Organization'),
                        ('dip', 'Diplomatic Mission'),
                        ('gov', 'Government'),
                        ('ngo', 'NGO'),
                        ('edu', 'Educational Institute'),
                        ('others', 'Other'),
                        ], string='Type of Ownership', store=True, default='pro',
                        )

    
    withholding = fields.Boolean(string= 'Withholding Entity', default=False, store=True)

    economic_activity =   fields.Selection(
                        [
                        ('man', 'Manufacturing'),
                        ('ser', 'Services'),
                        ('imp', 'Imports'),
                        ('exp', 'Exports'),
                        ('other', 'Other'),
     
             ], string='Economic Activity', store=True,
                        )

    man_areas = fields.Selection(
                        [
                            ('none','None'),
                            ('agr', 'Agriculture/Forestry/Fisheries'),
                            ('edi', 'Edible Oil'),
                            ('fab', 'Food & Beverage'),
                            ('tob', 'Tobacco'),
                            ('ores', 'Ores & Minerals'),
                            ('che', 'Chemical Products'),
                            ('pls', 'Plastic & Rubber'),
                            ('leather', 'Leather Products'),
                            ('wood', 'Wood, Wooden Products & Furniture Institute'),
                            ('paper', 'Paper & Paper Products'),
                            ('textile', 'Textile & Apparels'),
                            ('glass', 'Glass, Ceramic & Stone Articles'),
                            ('jewelry', 'Jewelry'),
                            ('iron', 'Iron, Steel & Other Metal Products'),
                            ('machinery', 'Machinery & Equipment'),
                            ('electrical', 'Electrical & Electronics'),
                            ('automobiles', 'Autmobiles'),
                            ('cycle', 'Cycle & Motorcycles'),
                            ('watercraft', 'Watercraft'),
                            ('aviation', 'Aviation'),
                            ('optical', 'Optical Instruments(e.g. spectacles, camera)'),
                            ('others', 'Other'),
                        ], string='Type of Manufacturing', store=True, default='none',
                        )


    ser_areas = fields.Selection(
                        [
                            ('none','None'),
                            ('con', 'Construction'),
                            ('trading', 'Trading including e-Commerce'),
                            ('real', 'Real Estate'),
                            ('transport', 'Transport'),
                            ('electrical', 'Electrical/Gas?Water Supply'),
                            ('financial', 'Financial Institution'),
                            ('pls', 'Plastic & Rubber'),
                            ('hotel', 'Hotel & Guest Houses'),
                            ('restaurants', 'Restaurants'),
                            ('rental', 'Rental'),
                            ('research', 'Research & Leasing Service'),
                            ('healthcare', 'Healthcare'),
                            ('education', 'Education & Training'),
                            ('telecom', 'Telecommunication & Internet'),
                            ('software', 'Software & ITES'),
                            ('sports', 'Sports & entertainment'),
                            ('event', 'Event Management & Catering'),
                            ('workshop', 'Workshop & Engineering'),
                            ('tour', 'Tour Operator & Travel Agent'),
                            ('advertising', 'Advertising & Promotion'),
                            ('customs', 'Customs Brokerage & freight Forwarding & Promotion'),
                            ('radio', 'Radio & TV Operations'),
                            ('consultancy','Consultancy'),                            
                            ('others', 'Other'),
                        ], string='Service Areas', store=True, default='none',
                        )
    
    last_turn = fields.Monetary('Taxable turnover in past 12 months period (if applicable)',default=False)
    pro_turn = fields.Monetary('Projected turnover in next 12 months period', default=False)

  
class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    bill_origin = fields.Many2one(
        string='PO Reference',
        comodel_name='purchase.order',
        ondelete='restrict', )

    # @api.model
    # def create(self, values):
    #     sale_order = False
    #     for key,value in values.items():
    #         if values[key] == 'out_invoice':
    #             sale_order = True
    #     if sale_order == False:           
    #         val = copy.deepcopy(values)
    #     # print("Before-->",val)
    #     record = super(AccountMoveInherit, self).create(values)
    #     # 
    #     # print("After-->",val)
    #     if record.type == 'in_invoice':    
    #         if val['invoice_line_ids']:
    #             value  = val['invoice_line_ids']
    #             pur_ref = value[0][2]['name'].split(":")[0]
    #         if value:
    #                 pur_or = self.env['purchase.order'].sudo().search([('name','=',pur_ref)])
    #                 record.sudo().write({'bill_origin' : pur_or})
    #         else:
    #             for key,value in values.items():
    #                 if key == 'invoice_line_ids':
    #                     pur_ref = value[0][2]['name'].split(":")[0]
    #                     pur_or = self.env['purchase.order'].sudo().search([('name','=',pur_ref)])
    #                     record.sudo().write({'bill_origin' : pur_or})
    #     return record



class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    origin = fields.Char(string="Challan No", required=True)

    def button_mark_done(self):
        self.ensure_one()
        self._check_company()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self._check_lots()
        self.post_inventory()
        (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        
        return self.write({'date_finished': self.date_planned_finished})
        #return self.write({'date_finished': fields.Datetime.now()})

    # def open_produce_product(self):
    #     self.ensure_one()
    #     if self.bom_id.type == 'phantom':
    #         raise UserError(_('You cannot produce a MO with a bom kit product.'))
    #     action = self.env.ref('mrp.act_mrp_product_produce').read()[0]
    #     print(self.button_mark_done())       
        
    #     return action