# -*- coding: utf-8 -*-
# from odoo import http


# class EvlTraining(http.Controller):
#     @http.route('/evl_training/evl_training/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/evl_training/evl_training/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('evl_training.listing', {
#             'root': '/evl_training/evl_training',
#             'objects': http.request.env['evl_training.evl_training'].search([]),
#         })

#     @http.route('/evl_training/evl_training/objects/<model("evl_training.evl_training"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('evl_training.object', {
#             'object': obj
#         })
