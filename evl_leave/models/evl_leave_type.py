# -*- coding: utf-8 -*-

import datetime
import logging

from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools.float_utils import float_round

_logger = logging.getLogger(__name__)


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    validation_type = fields.Selection([
        ('no_validation', 'No Validation'),
        ('hr', 'Time Off Officer'),
        ('manager', 'Team Leader'),
        ('both', 'Team Leader and Time Off Officer'),
        ('triple', 'Team Leader,Time Off Officer and HR Officer')], default='hr', string='Validation')
