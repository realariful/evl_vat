# -*- coding: utf-8 -*-
from odoo import http

# class EvlEmployee(http.Controller):
#     @http.route('/evl_employee/evl_employee/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/evl_employee/evl_employee/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('evl_employee.listing', {
#             'root': '/evl_employee/evl_employee',
#             'objects': http.request.env['evl_employee.evl_employee'].search([]),
#         })

#     @http.route('/evl_employee/evl_employee/objects/<model("evl_employee.evl_employee"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('evl_employee.object', {
#             'object': obj
#         })