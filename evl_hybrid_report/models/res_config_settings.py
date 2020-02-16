# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    
    date_to = fields.Date(
        string='Date To',
    )

    def action_gen_report(self):

        pass
    

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(date_to=self.env['ir.config_parameter'].sudo().get_param('evl_hybrid.date_to'))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('evl_hybrid.date_to', self.date_to)