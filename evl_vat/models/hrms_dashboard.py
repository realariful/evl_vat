# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
# import pandas as pd
from pytz import utc
from odoo import models, fields, api, _
from odoo.http import request
from odoo.tools import float_utils

ROUNDING_FACTOR = 16

def last_day_of_month(any_day):
    import datetime
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)

def get_years():
    year_list = []
    for i in range(2020, 2099):
        year_list.append((str(i), str(i)))
    return year_list

class Purchase(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def get_purchase_details(self):
        last_day_of_month(datetime.today())
        uid = request.session.uid
        today = datetime.strftime(datetime.today(), '%Y-%m-%d')
        query = """
        select name, date_order
        from purchase_order
        WHERE invoice_status ='invoiced' AND state='purchase' 
                ORDER BY id desc LIMIT 1"""
        cr = self._cr
        cr.execute(query)
        purchase_order = cr.fetchall()
        if purchase_order:
            data = {
                'pur_name': purchase_order[0][0] if purchase_order[0] else '',
                'date_order': purchase_order[0][1],
            }
            purchase_order = data
            return purchase_order
        else:
            return False



class VatDashboard (models.Model):
    _name = 'vat.dashboard'
    _description = 'VAT Dashboard'

    @api.model
    def get_user_employee_details(self):
        uid = request.session.uid
        employee = self.env['res.users'].sudo().search_read([('id', '=', uid)], limit=1)

        if employee or uid == 1:
            employee = self.env['res.users'].sudo().search_read([], limit=1) if uid == 1 else employee
            today = datetime.strftime(datetime.today(), '%Y-%m-%d')

            first_day = datetime.today().replace(day=1)
            last_day = last_day_of_month(first_day)
            
            vat_bal = """
                        SELECT 
                            a.*,
                            b.*,
                            a.amount - b.amount_tax    AS difference
                        FROM
                        (
                            SELECT COALESCE(SUM(amount),0) AS amount FROM evl_payments 
                                                WHERE purpose='vat' OR purpose='vatin'
                        )
                            a
                        CROSS JOIN
                        (
                            SELECT COALESCE(SUM(so.amount_tax),0)   AS amount_tax  FROM sale_Order so
                        WHERE so.state='sale' AND so.invoice_status='invoiced' 
                        )
                            b            
                """
            cr = self._cr
            cr.execute(vat_bal)
            vat_balalce = cr.fetchall()
            vds_bal ="""SELECT
                                a.*,
                                b.*,
                                a.amount - b.amount    AS difference
                                FROM
                                
                                (SELECT  COALESCE(SUM(amount),0) AS amount FROM evl_vdspayments) a
                            CROSS JOIN

                        (SELECT  COALESCE(SUM(amount),0) AS amount FROM evl_vdssale) b
                            """
            cr = self._cr
            cr.execute(vds_bal)
            vds_balance = cr.fetchall()

            s_query = """SELECT name, date_order, id FROM sale_order
                        WHERE invoice_status ='invoiced' AND state='sale' 
                        ORDER BY id desc LIMIT 1"""
            cr = self._cr
            cr.execute(s_query)


            sale_order = cr.fetchall()

            query = """ SELECT name, date_order, id FROM purchase_order
                        WHERE invoice_status ='invoiced' AND state='purchase' 
                        ORDER BY id desc LIMIT 1"""
            cr = self._cr
            cr.execute(query)
            purchase_order = cr.fetchall()

            # sale_t_q ="""SELECT COALESCE(SUM(amount_total),0.0) ,COALESCE(COUNT(*),0) FROM purchase_order po WHERE po.state='purchase' AND po.invoice_status='invoiced' 
            #             AND po.date_order >= '2020-03-01' AND po.date_order <= '2020-03-31'"""
            # cr = self._cr
            # cr.execute(sale_t_q)
            # sale_tot = cr.fetchall()
            
            sale_t_q ="""SELECT COALESCE(SUM(amount_total),0.0) ,COALESCE(COUNT(*),0) FROM sale_order so WHERE so.state='sale' AND so.invoice_status='invoiced' 
                        AND so.date_order >= '%s' AND so.date_order <= '%s'""" %(first_day.date(),last_day.date())
            cr = self._cr
            cr.execute(sale_t_q)
            sale_tot = cr.fetchall()

            pur_t_q ="""SELECT COALESCE(SUM(amount_total),0.0) ,COALESCE(COUNT(*),0) FROM sale_order so WHERE so.state='purchase' AND so.invoice_status='invoiced' 
                        AND so.date_order >= '%s' AND so.date_order <= '%s'"""  %(first_day.date(),last_day.date())
            cr = self._cr
            cr.execute(pur_t_q)
            pur_tot = cr.fetchall()
            
            # import pdb; pdb.set_trace()
            if date.today().day >= 10:
                next_return = (date.today() + relativedelta(months=1, day=10))# - timedelta(1) 
            else:
                next_return = (date.today() + relativedelta(day=10))# - timedelta(1) 

            days = (next_return - date.today()).days
            next_return = next_return.strftime("%d %B, %Y")
            next_return = "Next: " + next_return

            data = {
                'vat_balalce':"%.2f" %(vat_balalce[0][2]) if  len(vat_balalce) != False else "%.2f" %(0.00),
                'vds_balance': "%.2f" %(vds_balance[0][2])  if  len(vds_balance) != False else "%.2f" %(0.00),
                'next_return' : next_return,
                'days':days,
                'pur_name': purchase_order[0][0] if len(purchase_order) > 0 else '',
                'date_order': purchase_order[0][1].strftime("%b %d, %Y %H:%M") if len(purchase_order) > 0  else '',
                'pur_id': purchase_order[0][2] if len(purchase_order) > 0  else '',
                'sale_name': sale_order[0][0] if len(sale_order) > 0  else '',
                'sale_date': sale_order[0][1].strftime("%b %d, %Y %H:%M") if len(sale_order) > 0  else '',
                'sale_id': sale_order[0][2] if len(sale_order) > 0 else '',
                'sale_tot' : "%.2f" %(sale_tot[0][0]) if len(sale_tot) > 0  else '',
                'sale_ct': sale_tot[0][1] if len(sale_tot) > 0 else '',
                'pur_tot': "%.2f" %(pur_tot[0][0]) if len(pur_tot) > 0  else '',
                'pur_ct': pur_tot[0][1] if len(pur_tot) > 0 else '',         
            }
            
            employee[0].update(data)
            return employee
        else:
            return False



    @api.model
    def get_vat_balance(self):
        cr = self._cr
        month_list = []
        vat_balance = []
        vat_acc =[]
        vat_p =[]
        join_trend = []
        resign_trend = []
        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        for month in month_list:
            vals = {'l_month': month,'vat': 0}
            vat_balance.append(vals)
        for month in month_list:
            vals2 = {'l_month': month,'vat': 0}
            vat_acc.append(vals2)
        for month in month_list:
            vals3 = {'l_month': month,'vat': 0}
            vat_p.append(vals3)

        # print(vat_balance);import pdb; pdb.set_trace()
        
        # cr.execute('''select to_char(date_order, 'Month YYYY') as l_month, COALESCE(SUM(amount_tax),0.0) as count from sale_order 
        # WHERE date_order BETWEEN CURRENT_DATE - INTERVAL '6 months'
        # AND CURRENT_DATE + interval '1 month - 1 day' AND state='sale' AND invoice_status='invoiced'
        # group by l_month''')
        cr.execute('''with data as (
                        select 
                                to_char(date_order, 'Month YYYY') as l_month, 
                                COALESCE(SUM(amount_tax),0.0) as count from sale_order 
                                WHERE date_order BETWEEN CURRENT_DATE - INTERVAL '6 months'
                                AND CURRENT_DATE + interval '1 month - 1 day' AND state='sale' AND invoice_status='invoiced'
                                group by l_month
                        )

                        select
                        l_month,
                        sum(count) over (order by l_month asc rows between unbounded preceding and current row)
                        from data ''')
        
        vat = cr.fetchall()


        for line in vat:
            match = list(filter(lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ', ''), vat_acc))
            if match:
                match[0]['vat'] = line[1]

        for join in vat_acc:
            join['l_month'] = join['l_month'].split(' ')[:1][0].strip()[:3] 

        # print(vat);print("vat_acc");print(vat_acc)

        cr.execute('''select to_char(date_submit, 'Month YYYY') as l_month, COALESCE(SUM(amount),0.0) from evl_payments 
        WHERE date_submit BETWEEN CURRENT_DATE - INTERVAL '6 months'
        AND CURRENT_DATE + interval '1 month - 1 day'
        group by l_month''')
        vat_pay = cr.fetchall()


        for line in vat_pay:
            match = list(filter(lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ', ''), vat_p))
            if match:
                match[0]['vat'] = line[1]

        for x in vat_p:
            x['l_month'] = x['l_month'].split(' ')[:1][0].strip()[:3]   

        # print(vat_pay);print("vat_p");print(vat_p)
        for x in vat_balance:
            x['l_month'] = x['l_month'].split(' ')[:1][0].strip()[:3] 
        for i in range(0,len(vat_balance)):
            if vat_acc[i]['l_month'] == vat_p[i]['l_month']:
                vat_balance[i]['vat'] = abs(vat_p[i]['vat'] - vat_acc[i]['vat'])
        for i in range(0,len(vat_balance)):
            if i > 0:
                vat_balance[i]['vat'] = abs(vat_balance[i-1]['vat'] + vat_balance[i]['vat'])
        
        # print(vat_balance)

        return vat_balance





    @api.model
    def vat_vs_vds(self):
        cr = self._cr
        month_list = []
        join_trend = []
        resign_trend = []
        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        for month in month_list:
            vals = {
                'l_month': month,
                'count': 0
            }
            join_trend.append(vals)
        for month in month_list:
            vals = {
                'l_month': month,
                'count': 0
            }
            resign_trend.append(vals)
        
        cr.execute('''select to_char(date_order, 'Month YYYY') as l_month, COALESCE(SUM(amount_tax),0.0) as count from sale_order 
        WHERE date_order BETWEEN CURRENT_DATE - INTERVAL '6 months'
        AND CURRENT_DATE + interval '1 month - 1 day' AND state='sale' AND invoice_status='invoiced'
        group by l_month''')
        join_data = cr.fetchall()


        # cr.execute('''select to_char(joining_date, 'Month YYYY') as l_month, count(id) from hr_employee 
        # WHERE joining_date BETWEEN CURRENT_DATE - INTERVAL '6 months'
        # AND CURRENT_DATE + interval '1 month - 1 day'
        # group by l_month''')
        # join_data = cr.fetchall()
        cr.execute('''select to_char(date_submit, 'Month YYYY') as l_month, COALESCE(SUM(amount),0.0) as count from evl_payments 
        WHERE date_submit BETWEEN CURRENT_DATE - INTERVAL '6 months'
        AND CURRENT_DATE + interval '1 month - 1 day'
        group by l_month''')
        resign_data = cr.fetchall()
        # cr.execute('''select to_char(resign_date, 'Month YYYY') as l_month, count(id) from hr_employee 
        # WHERE resign_date BETWEEN CURRENT_DATE - INTERVAL '6 months'
        # AND CURRENT_DATE + interval '1 month - 1 day'
        # group by l_month;''')
        # resign_data = cr.fetchall()

        for line in join_data:
            match = list(filter(lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ', ''), join_trend))
            if match:
                match[0]['count'] = line[1]
        for line in resign_data:
            match = list(filter(lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ', ''), resign_trend))
            if match:
                match[0]['count'] = line[1]
        for join in join_trend:
            join['l_month'] = join['l_month'].split(' ')[:1][0].strip()[:3]
        for resign in resign_trend:
            resign['l_month'] = resign['l_month'].split(' ')[:1][0].strip()[:3]
        graph_result = [{
            'name': 'VAT',
            'values': join_trend
        }, {
            'name': 'Payments',
            'values': resign_trend
        }]



        return graph_result