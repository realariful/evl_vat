# -*- coding: utf-8 -*-
from odoo import http

# class EvlTransfer(http.Controller):
#     @http.route('/evl_transfer/evl_transfer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/evl_transfer/evl_transfer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('evl_transfer.listing', {
#             'root': '/evl_transfer/evl_transfer',
#             'objects': http.request.env['evl_transfer.evl_transfer'].search([]),
#         })

#     @http.route('/evl_transfer/evl_transfer/objects/<model("evl_transfer.evl_transfer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('evl_transfer.object', {
#             'object': obj
#         })