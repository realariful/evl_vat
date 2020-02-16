
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

class TestModel(models.Model):
    _name = "evl.test"  
    _description = "sad"

    patient_id = fields.Many2one('hr.employee', string="employee")
    date_meeting = fields.Date(string="Date Meeting")

   
    @api.model
    def print_doc(self):
        print(self.reead()[0])
        return self.env.ref('evl_report.action_lost_reason_apply').report_action(self)
