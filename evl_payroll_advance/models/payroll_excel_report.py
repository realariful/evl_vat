import babel
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from io import StringIO
from io import BytesIO
import base64
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class PaySlipReport(models.Model):
    _inherit = "hr.payslip"

    gross = fields.Float(compute="compute_columns")

    # >>>>>>>>>>>>>># alw
    basic_salary = fields.Float(compute="compute_columns")
    house_rent = fields.Float(compute="compute_columns")
    medical= fields.Float(compute="compute_columns")
    conveyance= fields.Float(compute="compute_columns")
    residual_others= fields.Float(compute="compute_columns")

    total_earnings= fields.Float(compute="compute_columns")

    # >>>>>>>>>>>>>># ded

    absent= fields.Float(compute="compute_columns") 
    penalty = fields.Float(compute="compute_columns")   
    advance_it = fields.Float(compute="compute_columns") 
    others= fields.Float(compute="compute_columns") 
    advance_salary= fields.Float(compute="compute_columns")
    total_deductions= fields.Float(compute="compute_columns")
    # >>>>>>>>>>>>>># net payment
    
    net_payment= fields.Float(compute="compute_columns") 

    @api.depends('details_by_salary_rule_category')
    def compute_columns(self):
        for payslip in self:
            payslip.update(dict(payslip.details_by_salary_rule_category.mapped(lambda line: (line.name.lower().replace(' ','_'), line.total))))
 
    