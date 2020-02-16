# -*- coding: utf-8 -*-
# from odoo import http


# class EvlNoticeBoard(http.Controller):
#     @http.route('/evl_notice_board/evl_notice_board/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/evl_notice_board/evl_notice_board/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('evl_notice_board.listing', {
#             'root': '/evl_notice_board/evl_notice_board',
#             'objects': http.request.env['evl_notice_board.evl_notice_board'].search([]),
#         })

#     @http.route('/evl_notice_board/evl_notice_board/objects/<model("evl_notice_board.evl_notice_board"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('evl_notice_board.object', {
#             'object': obj
#         })
