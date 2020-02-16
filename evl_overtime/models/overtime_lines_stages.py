# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class OverTimeStage(models.Model):
  
    _name = "overtime.stage"
    _description = "Loan Stages"
    _rec_name = 'name'
  


    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")

    is_final_stage = fields.Boolean('Is Final Stage?')

    requirements = fields.Text('Requirements', help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name.")

  