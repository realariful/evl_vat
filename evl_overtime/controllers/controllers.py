# -*- coding: utf-8 -*-
# from odoo import http


# class EvlOvertime(http.Controller):
#     @http.route('/evl_overtime/evl_overtime/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/evl_overtime/evl_overtime/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('evl_overtime.listing', {
#             'root': '/evl_overtime/evl_overtime',
#             'objects': http.request.env['evl_overtime.evl_overtime'].search([]),
#         })

#     @http.route('/evl_overtime/evl_overtime/objects/<model("evl_overtime.evl_overtime"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('evl_overtime.object', {
#             'object': obj
#         })
