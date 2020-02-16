from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockMoveLineRequisition(models.Model):
    _inherit = "stock.move.line"

    requisition_line_id = fields.Many2one('requisition.line', related='move_id.requisition_id', copy=False, store=True)