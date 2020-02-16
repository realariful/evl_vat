# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EVLRequisition(models.Model):
    """
    This model is responsible for all requisition related data and workflows.

    """
    _name = 'requisition.master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1) 

    name = fields.Char(string='Requisition Reference', required=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('requisition.master'))
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('requisition.master'), index=True, readonly=True)
    requisition_line_ids = fields.One2many('requisition.line', 'requisition_id', string='Requisition Line', track_visibility='onchange')
    note = fields.Text(string="Note")
    purchase_requi_id = fields.Many2one('purchase.requisition', string='Purchase Agreement', copy=False, readonly=True)
    requisition_date = fields.Datetime('Date', copy=False, default=fields.Datetime.now, index=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', 'Requisitioner', default=lambda self: self._default_employee())
    requisition_type = fields.Selection([
        ('item', 'Item'),
        ('hr', 'Manpower'),
        ('service', 'Service'),
        ('vehicle', 'Vehicle'),
    ], default='item', string='Requisition Type')

    picking_id = fields.Many2one('stock.picking', string='Internal Transfer', readonly=True, copy=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('approve', 'Manager Approved'),
        ('head_approve', 'Head Approved'),
        ('hr_approve', 'Admin Approved'),
        ('issue', 'Issued'),
        ('purchase_ready', 'Purchase Ready'),
        ('partial_receive', 'Partially Received'),
        ('store_receive', 'Store Received'),
        ('receive', 'Received'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status', track_visibility='onchange', copy=False)
    show_issue = fields.Boolean(default=False, copy=False)
    show_purchase = fields.Boolean(default=False, copy=False)

    def action_confirm(self):
        for rec in self:
            if rec.state == 'draft':
                rec.write({'state': 'confirm'})

    def action_approve(self):
        for rec in self:
            if rec.state == 'confirm':
                rec.write({'state': 'approve'})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'confirm':
                rec.write({'state': 'cancel'})

    def action_draft(self):
        for rec in self:
            if rec.state == 'cancel':
                rec.write({'state': 'draft'})

    def action_head_approve(self):
        for rec in self:
            if rec.state == 'approve':
                rec.write({'state': 'head_approve'})

    def action_hr_approve(self):
        for rec in self:
            if rec.state == 'head_approve':
                rec.write({'state': 'hr_approve'})
                rec.admin_issue_or_purchase()

    def action_receive(self):
        for rec in self:
            if rec.state in ['issue', 'store_receive']:
                rec.write({'state': 'receive'})

    # @api.multi
    # def _track_subtype(self, init_values):
    #     self.ensure_one()
    #     if 'requisition_line_ids' in init_values:
    #         return 'mir_purchase.mt_purchase_requisition'

    #     return super(EVLRequisition, self)._track_subtype(init_values)

    def create_internal_transfer(self, line=False, prod_categ=False, src_loc=False):
        src_loc = self.env['stock.location'].search([('company_id', '=', self.company_id.id), 
                                ('usage', '=', 'internal')], order='id desc', limit=1)
        
        for line in self.requisition_line_ids:

            if line.product_id.product_tmpl_id.type == 'product':
                # destination_location = self.env.ref('')
                picking_type_internal = self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                        ('company_id', '=', self.company_id.id)], limit=1)

                pick_vals = {    
                    'scheduled_date'    :   self.requisition_date,
                    'company_id'        :   self.company_id.id,
                    'location_id'       :   src_loc.id,
                    'location_dest_id'  :   line.delivery_location.id,
                    'picking_type_id'   :   picking_type_internal.id,
                    'origin'            :   self.name
                    }

                picking_id = self.env['stock.picking'].create(pick_vals)

                move_vals = {  
                    'product_id'        :   line.product_id.id,
                    'product_uom_qty'   :   line.product_qty,
                    'product_uom'       :   line.product_uom_id.id,
                    'date'              :   self.requisition_date,
                    'name'              :   line.product_id.name,
                    'date_expected'     :   self.requisition_date,
                    'company_id'        :   self.company_id.id,
                    'location_id'       :   src_loc.id,
                    'location_dest_id'  :   line.delivery_location.id,
                    'picking_id'        :   picking_id.id,
                    'requisition_id'    :   line.id
                    }

                self.env['stock.move'].create(move_vals)
                picking_id.action_confirm()
                picking_id.action_assign()
                picking_id.move_ids_without_package.quantity_done = picking_id.move_ids_without_package.reserved_availability
                picking_id.button_validate()
                
                self.write({
                    'show_issue' : False,
                    'picking_id' : picking_id.id,
                    'state'      : 'issue' 
                    })

            elif line.product_id.product_tmpl_id.type == 'consu':

                destination_location = self.env.ref('evl_requisition.stock_location_issues')
                picking_type_internal = self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                        ('company_id', '=', self.company_id.id)], limit=1)

                vals = {    
                    'scheduled_date'    :   self.requisition_date,
                    'company_id'        :   self.company_id.id,
                    'location_id'       :   src_loc.id,
                    'location_dest_id'  :   destination_location.id,
                    'picking_type_id'   :   picking_type_internal.id,
                    'origin'            :   self.name
                    }

                picking_id = self.env['stock.picking'].create(vals)

                move_vals = {  
                    'product_id'        :   line.product_id.id,
                    'product_uom_qty'   :   line.product_qty,
                    'product_uom'       :   line.product_uom_id.id,
                    'date'              :   self.requisition_date,
                    'name'              :   line.product_id.name,
                    'date_expected'     :   self.requisition_date,
                    'company_id'        :   self.company_id.id,
                    'location_dest_id'  :   destination_location.id,
                    'location_id'       :   src_loc.id,
                    'picking_id'        :   picking_id.id,
                    'requisition_id'    :   line.id
                    }

                self.env['stock.move'].create(move_vals)
                picking_id.action_confirm()
                picking_id.action_assign()
                picking_id.move_ids_without_package.quantity_done = picking_id.move_ids_without_package.reserved_availability
                picking_id.button_validate()
                
                self.write({
                    'show_issue' : False,
                    'picking_id' : picking_id.id,
                    'state'      : 'issue' 
                    })

    def create_purchase_requisition(self):
        for line in self.requisition_line_ids:

            requi_vals = {    
                    'type_id'           :   2,
                    'company_id'        :   self.company_id.id,
                    'currency_id'       :   self.company_id.currency_id.id,
                    'origin'            :   self.name,
                    'state'             :   'draft',
                    'user_id'           :   self.env.user.id
                    }    
                
            requi_id = self.env['purchase.requisition'].create(requi_vals)

            line_vals = {  
                'product_id'            :   line.product_id.id,
                'qty_ordered'           :   line.product_qty,
                'product_uom_id'        :   line.product_uom_id.id,
                'company_id'            :   self.company_id.id,
                'requisition_id'        :   requi_id.id,
                'requisition_line_id'   :   line.id
                }
            
            requi_line_id = self.env['purchase.requisition.line'].create(line_vals)
            requi_id.action_in_progress()

            self.write({
                'show_purchase'              : False,
                'purchase_requi_id'          : requi_id.id,
                'state'                      : 'purchase_ready' 
                    })

    def admin_issue_or_purchase(self):
        for line in self.requisition_line_ids:
            
            if line.product_id.product_tmpl_id.type == 'product':
                admin_location = self.env['stock.location'].search([('company_id', '=', self.company_id.id), 
                        ('usage', '=', 'internal')], order='id desc', limit=1)
                
                if line.product_id.with_context(dict(self.env.context, location=admin_location.id)).qty_available > 0:
                    self.show_issue = True
                
                elif line.product_id.with_context(dict(self.env.context, location=admin_location.id)).qty_available <= 0:
                    self.show_purchase = True

            elif line.product_id.product_tmpl_id.type == 'consu':
                self.show_issue = True

    def unlink(self):
        for requi in self:
            if requi.state != 'draft':
                raise UserError(_('You can only delete a draft requisition'))

        super(EVLRequisition, self).unlink()


class EVLRequisitionLine(models.Model):
    _name = 'requisition.line'
    _description = 'Requisition Line'
    _order = 'id desc'

    @api.model
    def stock_location_by_company(self):
        company = self.env['res.company']._company_default_get('requisition.line')
        return [('company_id', '=', company.id), ('usage', '=', 'internal')]

    name = fields.Char(string='Line Reference', copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('requisition.line'), readonly=True, store=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    # domain="[('categ_id', 'child_of', ['Raw Materials', 'Spare Parts', 'Fuel and Lubricant', 'Service'])]"
    product_qty = fields.Float('Quantity', digits='Product Unit of Measure', default=0.0, required=True)
    receive_qty = fields.Float('Receive Qty', compute='_compute_qty_received', digits='Product Unit of Measure', default=0.0, readonly=True, store=True)
    purchase_qty = fields.Float('Purchase Qty', digits='Product Unit of Measure', default=0.0, readonly=True, store=True)
    product_uom_id = fields.Many2one('uom.uom', 'UoM', required=True)
    delivery_date = fields.Date(string='Delivery Date')
    delivery_location = fields.Many2one('stock.location', 'Stock Location', domain=lambda self: self.stock_location_by_company(), required=True)
    requisition_id = fields.Many2one('requisition.master', string='Requisition', index=True, ondelete='cascade')
    # purchase_requisition_line_ids = fields.One2many('purchase.requisition.line', 'master_requisition_id', string='Purchase Requisition Line')
    state = fields.Selection(related='requisition_id.state', string='Status', store=True)
    company_id = fields.Many2one('res.company', related='requisition_id.company_id', store=True)
    move_ids = fields.One2many('stock.move', 'requisition_id', string='Moves of Requisition', readonly=True, ondelete='set null', copy=False)

    def unlink(self):
        for requi_line in self:
            if requi_line.state != 'draft':
                raise UserError(_('You can only delete requisition lines in draft state'))

        super(EVLRequisitionLine, self).unlink()

    @api.depends('move_ids.state', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_received(self):
        for line in self:
            total = 0.0
            for move in line.move_ids:
                if move.state == 'done':
                    if move.location_dest_id.usage == "supplier":

                        if move.to_refund:
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom_id)

                    elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                        pass
                    else:
                        total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom_id)

            line.receive_qty = total

    # @api.onchange('status')
    # def _status_onchange(self):
    #     user_group = self.env['ir.config_parameter'].search(
    #         [('key', '=', 'purchase.status_update_config')]).value
    #     user_groups = user_group.split(',')
    #     for user in user_groups:
    #         if self.env.user.has_group(user.strip()) and self.status in ['approved', 'in_progress', 'confirmed', 'done', 'partial_done']:
    #             raise UserError("You are not allowed to change this status!!")
    #     if self.env.user.has_group('mir_purchase.group_mir_purchase_manager') and self._origin.fi_status != 'fi_approved':
    #         raise UserError("Factory Incharge does not approved this requisition!!")

    #     if not (self.env.user.has_group('inventory.group_factory_incharge') or self.env.user.has_group('base.group_erp_manager')) and self.status == 'fi_approved':
    #         raise UserError("Only Factory Incharge allowed to change this status!!")

    #     if self.env.user.has_group('inventory.group_factory_incharge') and self.status in ['approved', 'in_progress', 'confirmed', 'done', 'partial_done', 'cancel']:
    #         raise UserError("You are not allowed to change this status!!")

    @api.onchange('product_id')
    def _product_onchange(self):
        product = self.product_id
        self.product_uom_id = self.product_id.uom_id.id
        return {'domain': {'product_uom_id': [('category_id', '=', product.uom_id.category_id.id)]}}
    
    # @api.multi
    # def write(self, vals):
    #     status = vals.get('status', 'draft')
    #     if status == 'fi_approved':
    #         vals['fi_status'] = status
    #     elif status == 'draft':
    #         vals['fi_status'] = 'draft'
    #     return super(RequisitionLine, self).write(vals)

    # def requisition_status_update(self):
    #     stock_collection = []
    #     rounding_method = self._context.get('rounding_method', 'UP')
    #     picking = self.env['stock.picking'].search([('state', 'in', ('done', 'qc', 'sm'))])
    #     stock_moves = picking.mapped('move_lines')
    #     for stock_move in stock_moves:
    #         lc = stock_move.picking_id.foreign_purchase
    #         if stock_move.requisition_id.id and not lc:
    #             done_qty = stock_move.product_uom._compute_quantity(stock_move.product_qty, stock_move.requisition_id.product_uom_id, rounding_method=rounding_method)
    #             stock_collection.append({stock_move.requisition_id.id: done_qty})

    #     if not len(stock_collection):
    #         return

    #     completed_purchase = dict(reduce(add, map(Counter, stock_collection)))
    #     for requisition_id, qty in completed_purchase.items():
    #         stock_move = self.env['stock.move'].search([('state', '=', 'done'), ('requisition_id', '=', requisition_id)])
    #         requisition_line = self.browse(requisition_id)
    #         status = None

    #         done_quantity = 0.0
    #         for sm in stock_move:
    #             if not sm.picking_id.foreign_purchase:
    #                 done_quantity += sm.product_uom._compute_quantity(sm.product_uom_qty, requisition_line.product_uom_id, rounding_method=rounding_method)

    #         diff = float_compare(done_quantity, requisition_line.product_qty, precision_digits=2)
    #         if done_quantity > 0:
    #             if diff == -1:
    #                 status = 'partial_done'
    #             else:
    #                 status = 'done'
    #         if requisition_line.status in ('confirmed', 'partial_done', 'in_progress') and status is not None:
    #             requisition_line.write({
    #                 'status': status,
    #                 'receive_qty': done_quantity
    #             })


# class PurchaseRequisitionInherit(models.Model):
#     _inherit = "purchase.requisition"
#     _description = "Purchase Requisition"

#     @api.onchange('vendor_id')
#     def _create_purchase_requisition_line(self):
#         line = []
#         active_ids = self.env.context.get('active_ids')
#         master_purchase = self.env['requisition.line'].search([('id', 'in', active_ids)])
#         for requisition in master_purchase:
#             if requisition.status == 'approved':
#                 line.append((0, 0, {
#                     'product_id': requisition.product_id.id,
#                     'product_qty': requisition.product_qty,
#                     'delivery_location': requisition.delivery_location,
#                     'schedule_date': requisition.delivery_date,
#                     'product_uom_id': requisition.product_uom_id,
#                     'master_requisition_id': requisition.id,
#                 }))
#         self.line_ids = line

#     @api.model
#     def create(self, vals):
#         vals['picking_type_id'] = self.get_picking_type_id()
#         return super(PurchaseRequisitionInherit, self).create(vals)

#     @api.model
#     def get_picking_type_id(self):
#         company = self.env['res.company']._company_default_get('purchase.requisition')
#         pick_in = self.env['stock.picking.type'].search(
#             [('warehouse_id.company_id', 'child_of', company.id), ('code', '=', 'incoming')],
#             limit=1,
#         )
#         return pick_in.id if pick_in else None


# class PurchaseRequisitionLineInherit(models.Model):
#     _inherit = "purchase.requisition.line"
#     _description = "Purchase Requisition Line"

#     product_id = fields.Many2one('product.product', string='Product', required=True)
#     delivery_location = fields.Many2one('stock.location', 'Warehouse Location')
#     master_requisition_id = fields.Many2one('requisition.line', string='Master Requisition')

#     @api.model
#     def create(self, values):
#         master_requisition_id = values.get('master_requisition_id')
#         if master_requisition_id is not None:
#             master_requisition = self.env['mir.requisition.line'].browse(master_requisition_id)
#             master_requisition.write({
#                 'status': 'in_progress'
#             })
#         return super(PurchaseRequisitionLineInherit, self).create(values)

#     @api.multi
#     def write(self, values):
#         master_requisition_id = values.get('master_requisition_id')
#         if master_requisition_id is not None:
#             master_requisition = self.env['mir.requisition.line'].browse(master_requisition_id)
#             master_requisition.write({
#                 'status': 'in_progress'
#             })
#         return super(PurchaseRequisitionLineInherit, self).write(values)
