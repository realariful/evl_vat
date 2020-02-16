from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, time


class PurchaseRequisitionLineRequisition(models.Model):
    _inherit = "purchase.requisition.line"

    requisition_line_id = fields.Many2one('requisition.line', string='Requisition Line Ref', copy=False, readonly=True)

    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, requisition_line_id=False, taxes_ids=False):
        print('========= My _prepare_purchase_order_line ==============')
        self.ensure_one()
        requisition = self.requisition_id
        if requisition.schedule_date:
            date_planned = datetime.combine(requisition.schedule_date, time.min)
        else:
            date_planned = datetime.now()
        return {
            'name': name,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_po_id.id,
            'product_qty': product_qty,
            'price_unit': price_unit,
            'requisition_line_id': requisition_line_id,
            'taxes_id': [(6, 0, taxes_ids)],
            'date_planned': date_planned,
            'account_analytic_id': self.account_analytic_id.id,
            'analytic_tag_ids': self.analytic_tag_ids.ids,
        }