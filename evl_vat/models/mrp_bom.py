
import logging
import math

from collections import namedtuple

from datetime import datetime, time
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _

class MrpBomInherit(models.Model):
    _inherit = 'mrp.bom'

    bill_of_cost = fields.One2many('mrp.bom.costs','cost_id', string="Bill of Cost")
    # services = fields.One2many('mrp.bom.services','service_id', string="Services")


# class MrpBomServices(models.Model):
#     _name = 'mrp.bom.services'
#     _description = 'EVL MRP BOM Services'
#     _rec_name = 'id'

#     product_id = fields.Many2one('product.product',string="Service Name", required=True,domain="[('type','=','service')]")
#     cost = fields.Float('Cost', required=True)
#     service_id = fields.Many2one('mrp.bom', string="Service Id")



class MrpBomCosts(models.Model):
    _name = 'mrp.bom.costs'
    _description = 'EVL MRP BOM Costs'
    _rec_name = 'id'

    name = fields.Char(string="Cost Name", required=True)
    cost = fields.Float('Cost', required=True)
    cost_id = fields.Many2one('mrp.bom', string="Cost Id")


class MrpBomLineExtend(models.Model):
    _inherit = 'mrp.bom.line'

    waste_qty = fields.Float(
        'Waste (Qty)', default=1.0,
        digits='Product Unit of Measure')

    waste_per = fields.Float('Waste (%)', default=0.0, compute="_waste_percent")

    standard_price = fields.Float('Price', default=0.0)
    # @api.depends('product_id')
    # def _product_price(self):
    #     for rec in self:
    #         rec.standard_price = rec.product_id.standard_price

    @api.depends('waste_qty','product_qty')
    def _waste_percent(self):
        for rec in self:
            if rec.waste_qty > rec.product_qty:
                raise ValidationError("Waste Quantity must be smaller than Product Quantity")
            else:
                if rec.waste_qty == 0.0 and rec.product_qty == 0.0:
                    rec.waste_per = 0.0
                else:
                    rec.waste_per = round((rec.waste_qty/rec.product_qty)*100)