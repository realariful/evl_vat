from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class StockReturnPickingRequisition(models.TransientModel):
    _inherit = "stock.return.picking"
    _description = 'Return Picking'

    def _prepare_move_default_values(self, return_line, new_picking):

        vals = super(StockReturnPickingRequisition, self)._prepare_move_default_values(return_line, new_picking)
        vals['requisition_id'] = return_line.move_id.requisition_id.id

        return vals