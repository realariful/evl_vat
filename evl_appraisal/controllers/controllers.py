# -*- coding: utf-8 -*-
from odoo import http

# class EvlAppraisal(http.Controller):
#     @http.route('/evl_appraisal/evl_appraisal/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/evl_appraisal/evl_appraisal/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('evl_appraisal.listing', {
#             'root': '/evl_appraisal/evl_appraisal',
#             'objects': http.request.env['evl_appraisal.evl_appraisal'].search([]),
#         })

#     @http.route('/evl_appraisal/evl_appraisal/objects/<model("evl_appraisal.evl_appraisal"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('evl_appraisal.object', {
#             'object': obj
#         })