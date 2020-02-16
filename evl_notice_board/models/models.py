# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError
import json
import logging
import werkzeug
from datetime import datetime
from math import ceil
from odoo import fields, http, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo.http import request
from odoo.tools import ustr

import time
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import except_orm
from odoo import exceptions
from odoo.exceptions import AccessError, UserError, ValidationError

import datetime
import pdb
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError


class evl_notice_board(models.Model):
    _name = "evl.notice.board"
    _description = "Notice Board"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "title"

    name = fields.Char()

    title = fields.Char(string="title",)
    is_seen = fields.Boolean(string="Status", default=False)
    is_batch = fields.Boolean(default="False", store=True)

    description = fields.Text()

    

    state = fields.Selection(
        [("new", "New"), ("read", "Read"),],
        string="Seen State",
        default="new",
        track_visibility="onchange",
    )

    messege_state = fields.Selection(
        string="state",
        default="draft",
        selection=[("draft", "Draft"), ("posted", "Posted")],
    )

    is_related_model = fields.Boolean(string="related_model", default="False")

    employee_id = fields.Many2one(
        "hr.employee", required=True, string="Employee", index=True
    )

    gen_date = fields.Datetime(string="Post Date", default=fields.Datetime.now,)

    messege_id_id = fields.Many2one(
        string="Messege Id", comodel_name="mail.message", ondelete="restrict",
    )

    def notification_message_post(self, *,
                     message_body='', 
                     related_record=None,
                     message_recipient=False,
                     **kwargs):

        if related_record and message_recipient:
            

            for records in message_recipient:
                if records.user_id:

                    discuss_notification= related_record.sudo().message_post(
                            body = message_body,
                            partner_ids=records.user_id.partner_id.ids)



                custom_notification = self.env['evl.notice.board'].sudo().create({
                    'employee_id':records.id,
                    'res_model':related_record._name,
                    'res_model_id':related_record.id,
                    'res_model_name':related_record._description,
                    'title':related_record.name_get()[0][1],
                    'is_related_model': True,
                    'messege_state':'posted',
                    'state':'new',
                    'description':message_body
                    })
            return True
        
        else:
            False

                

    res_model = fields.Char(string="res_model",)

    res_model_id = fields.Integer(string="res_model_id",)

    res_model_name = fields.Char(string="res_model_name",)

    attachment_ids = fields.Many2many("ir.attachment", string="Attachment Files")

    description = fields.Html("Description")

    def action_seen(self):
        for records in self:
            records.sudo().write({'state':"read"})

    def related_model_view_form(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "name": "Related Model",
            "view_mode": "form",
            "res_id": self.res_model_id or False,
        }

    @api.depends("value")
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100

    batch = fields.Many2one(comodel_name="notice.batch", ondelete="restrict",)


class NoticeBatch(models.Model):
    _name = "notice.batch"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Notice Batch Circulate"

    _rec_name = "batch_name"

    batch_name = fields.Char()
    title = fields.Char(string="title",)

    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)


    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("posted", "Circulated"),
            ("cancel", "Cancel"),
        ],
        string="Status",
        default="draft",
        track_visibility="onchange",
    )

    employee_ids = fields.Many2many(comodel_name="hr.employee",)
    gen_date = fields.Datetime(string="Post Date", default=fields.Datetime.now,)

    lines = fields.One2many(comodel_name="evl.notice.board", inverse_name="batch",)
    description = fields.Html("Description")
    attachment_ids = fields.Many2many("ir.attachment", string="Attachment Files")

    def action_confirm(self):
        for records in self:
            records.write({"state": "confirm"})

    def action_post(self):

        for persons in self.employee_ids:

            if not persons.user_id.partner_id.ids:
                raise UserError(_('No Active User found for "%s".') % (persons.name))

            
            # notif_lines = self.lines.create(
            #     {
            #         "batch": self.id,
            #         "is_batch": True,
            #         "title": self.title,
            #         "employee_id": persons.id,
            #         "description": self.description,
            #         "is_related_model": False,
            #         "messege_state": "posted",
            #         "attachment_ids": [(6, 0, self.attachment_ids.mapped("id"))],
            #     })

            self.message_post(
                body=_("A Notice is generated "),
                partner_ids=persons.user_id.partner_id.ids,
            )

            
        self.write({"state": "posted"})

    @api.model
    def create(self, vals):
        res_id = super(NoticeBatch, self).create(vals)
        res_id.batch_name = "Notice for " + res_id.title

        return res_id

