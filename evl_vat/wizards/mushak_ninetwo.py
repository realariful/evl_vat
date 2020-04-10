
#-*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from odoo import api, fields, models, _
from odoo.tools.misc import get_lang
from datetime import datetime,timedelta
import bangla
from odoo.exceptions import UserError

def last_day_of_month(any_day):
    import datetime
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def get_local_time(self):
    from datetime import datetime,timedelta
    import pytz
    user_tz = self.env.user.tz or pytz.utc

    if str(user_tz) == 'UTC':
        raise UserError(_("Please setup timezone for you."))
    else:
        local = pytz.timezone(user_tz)
        local_time = datetime.now().astimezone(local) 
        return local_time

def get_years():
    year_list = []
    crn_year = datetime.now().year
    for i in range(2019, crn_year+1):
        year_list.append((str(i), str(i)))
    return year_list


class ReportMushakVATReturn2(models.Model):
    _name = 'mushak.vatreturntwo'
    _description = 'Mushak 9.2 (VAT Return)'

    month = fields.Selection(
                        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                        string='Month' , required=True)
    year = fields.Selection(get_years(), string='Year', dafault='10' , required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    product_selection = fields.Boolean(
        'All Product', default=False,
        help="By checking this product selection field, you select all products.")
    product_id = fields.Many2one(
        'product.product', 'Product',## ('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), 
        domain="[('categ_id.name','=','Raw Material'),('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')
    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)
        
    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='portrait', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id


    sub_date =  fields.Date('Submission Date'  , required=True)
 

    def _build_contexts(self, data):
        #Need to find start date and end date
        from datetime import datetime
        first_of_month = datetime.today().replace(month=int(self.month)).replace(day=1).replace(year=int(self.year)).date()
        import datetime
        last_of_month =  last_day_of_month(datetime.date(first_of_month.year,first_of_month.month,1 ))

        result = {}
        # result['company_id'] = data['form']['company_id'][0] or False

        
        page1={}

        address = self.company_id.street if self.company_id.street != False else ''
        address = address + ',' + self.company_id.street2 if self.company_id.street2 != False else address
        address = address + ',' + self.company_id.city if self.company_id.city != False else address
        address = address + ',' + self.company_id.country_id.name if self.company_id.country_id.name != False else address


        page1= {
            'part1':
                    {
                            'bin':self.company_id.vat,
                            'company':self.company_id.name,
                            'address':address,
                            'business_type': dict(self.company_id._fields['owner_type'].selection).get(self.company_id.owner_type),
                            'operation_type' : dict(self.company_id._fields['economic_activity'].selection).get(self.company_id.economic_activity),
                        },

                'part2': {
                            'tax_period': {'month': self.month,'year':self.year},
                            'type': '1',
                            'last':'1',
                            'date' : self.sub_date.strftime("%d/%m/%Y")
                        },

                        'pg_no': '1','report_date': self.report_time.strftime("%d/%m/%Y %H:%M")
                    }
        #--------------------------------------------------------------------------------------------
        
 
        subform = {}
        sub_ka = {}


        #COALESCE( round(  es.amount ,2), 0.00)
        #-------------------------Working
        #Query for sales Order (Note 10-20)
        #Sales query using account_move
        #Make sure everything from account_move
        sol_query_new = """ 
                        SELECT 
                            ROW_NUMBER() OVER (ORDER BY eh.hscode) as sn,
                            eh.description as pro_des,
                            eh.hscode as pro_hs,	
                            sol.name as pro_name, 
                            COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                            COALESCE(round( CAST(SUM(sol.vat_sd) as numeric), 2),0.00) as pro_sd,
                            COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                            so.sale_type as comment
                        FROM sale_order_line sol
                            LEFT JOIN product_product pp ON sol.product_id = pp.id
                            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                            LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                            LEFT JOIN sale_order so ON sol.order_id = so.id	
                            LEFT JOIN account_move am ON so.name = am.invoice_origin
                        WHERE so.invoice_status = 'invoiced' AND sol.sale_subtype = %s
                            AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s 
                            AND so.company_id = %s
                            AND so.sale_type = %s AND so.sale_type2 = %s
                        GROUP BY eh.description,eh.hscode,sol.name,so.sale_type

                        """ 
        soltot_query_new = """
                          SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                                COALESCE(SUM(sol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                                
                                FROM sale_order_line sol


                                LEFT JOIN product_product pp ON sol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN sale_order so ON sol.order_id = so.id	
                                LEFT JOIN account_move am ON so.name = am.invoice_origin
    
                                WHERE so.invoice_status = 'invoiced' AND sol.sale_subtype = %s
                                        AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  
                                        AND so.company_id = %s
                                        AND so.sale_type = %s AND so.sale_type2 = %s


                                """



        sol_query = """ 
                        SELECT 
                            ROW_NUMBER() OVER (ORDER BY eh.hscode) as sn,
                            eh.description as pro_des,
                            eh.hscode as pro_hs,	
                            sol.name as pro_name, 
                            COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                            COALESCE(round( CAST(SUM(sol.vat_sd) as numeric), 2),0.00) as pro_sd,
                            COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                            so.sale_type as comment
                        FROM sale_order_line sol
                            LEFT JOIN product_product pp ON sol.product_id = pp.id
                            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                            LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                            LEFT JOIN sale_order so ON sol.order_id = so.id	
                            LEFT JOIN account_move am ON so.name = am.invoice_origin
                        WHERE so.invoice_status = 'invoiced' AND sol.sale_subtype = %s
                            AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s 
                            AND so.company_id = %s
                            AND so.sale_type = %s
                        GROUP BY eh.description,eh.hscode,sol.name,so.sale_type

                        """ 
        soltot_query = """
                          SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                                COALESCE(SUM(sol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                                
                                FROM sale_order_line sol


                                LEFT JOIN product_product pp ON sol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN sale_order so ON sol.order_id = so.id	
                                LEFT JOIN account_move am ON so.name = am.invoice_origin
    
                                WHERE so.invoice_status = 'invoiced' AND sol.sale_subtype = %s
                                        AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  
                                        AND so.company_id = %s
                                        AND so.sale_type = %s


                                """
      
        sol_total = """
                        SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                                COALESCE(SUM(sol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                                
                                FROM sale_order_line sol


                                LEFT JOIN product_product pp ON sol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN sale_order so ON sol.order_id = so.id	
                                LEFT JOIN account_move am ON so.name = am.invoice_origin
    
                                WHERE so.invoice_status = 'invoiced'  
                                        AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s AND so.company_id =%s

                                """


        row_loc =   [{'sn' : '-','pro_des' : '-', 'pro_hs' : '-', 'pro_name' : '-', 'pro_price' : 0.00, 'pro_sd' : 0.00, 'pro_vat' : 0.00, 'comment' : '',} ]
        row_for =   [{'sn' : '-', 'pro_des' : '-', 'pro_hs' : '-', 'pro_name' : '-', 'pro_price' : 0.00, 'pro_sd' : 0.00, 'pro_vat' : 0.00, 'comment' : '', } ]

        sol_Cat = ['zero','exempt','standard', 'high', 'specific', 'not_reyat','retail']
        for cate in sol_Cat:
            if cate == 'zero':
                #direct
                self.env.cr.execute(sol_query_new, (cate, first_of_month, last_of_month,self.company_id.id,'foreign','direct'))   
                note1_z_l = self.env.cr.dictfetchall() 
                
                self.env.cr.execute(soltot_query_new, (cate, first_of_month,last_of_month,self.company_id.id,'foreign','direct')) 
                note1_z_t = self.env.cr.dictfetchall()

                #indirect
                self.env.cr.execute(sol_query_new, (cate, first_of_month,last_of_month,self.company_id.id,'foreign','indirect'))   
                note2_z_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(soltot_query_new, (cate, first_of_month,last_of_month,self.company_id.id,'foreign','indirect'))     
                note2_z_t = self.env.cr.dictfetchall() 
                note1_z_l = row_loc if len(note1_z_l) == 0 else note1_z_l
                note2_z_t = row_for if len(note2_z_l) == 0 else note2_z_l 


            if cate == 'exempt':               
                #Local
                self.env.cr.execute(sol_query, ('exempt', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note3_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(soltot_query, ('exempt', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note3_t = self.env.cr.dictfetchall() 
                note3_l = row_loc if len(note3_l) == 0 else note3_l

            if cate == 'standard':
                #Local
                self.env.cr.execute(sol_query, ('standard', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note4_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(soltot_query, ('standard', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note4_t = self.env.cr.dictfetchall() 
                note4_l = row_loc if len(note4_l) == 0 else note4_l

        self.env.cr.execute(sol_total, (first_of_month, last_of_month,self.company_id.id,))   
        note5_t = self.env.cr.dictfetchall() 

        note5_t_ga = note5_t[0]['pro_vat']



        #Purchase order starts
        rows_query = """ 
                            SELECT 
                                    ROW_NUMBER() OVER (ORDER BY eh.hscode) as sn,
                                    eh.description as pro_des,
                                    eh.hscode as pro_hs,	
                                    pol.name as pro_name, 
                                    ROUND(SUM(pol.price_subtotal),2) as pro_price, 
                                    COALESCE(SUM(pol.vat_sd), 0.00 ) as pro_sd,
                                    round( CAST(SUM(pol.price_tax) as numeric), 2) as pro_vat,
                                    po.purchase_type as comment
                                FROM purchase_order_line pol 

                                
                                LEFT JOIN product_product pp ON pol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id	
                                 LEFT JOIN account_move as am ON po.id = am.bill_origin
    
                                WHERE po.invoice_status = 'invoiced' AND pol.purchase_subtype = %s
                                        AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s 
                                        AND po.purchase_type = %s
                       
                                GROUP BY eh.description,eh.hscode,pol.name,po.purchase_type

                        """ 
        tot_query = """
                            SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(ROUND(SUM(pol.price_subtotal),2),0.00) as pro_price, 
                                COALESCE(SUM(pol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(pol.price_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                            FROM purchase_order_line pol 
                                LEFT JOIN product_product pp ON pol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id	
                                LEFT JOIN account_move as am ON po.id = am.bill_origin
        
                            WHERE po.invoice_status = 'invoiced' AND pol.purchase_subtype = %s
                                    AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s 
                                    AND po.purchase_type = %s


                                """
      
        zero_total = """
                            SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(ROUND(SUM(pol.price_subtotal),2),0.00) as pro_price, 
                                COALESCE(SUM(pol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(pol.price_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                            FROM purchase_order_line pol 
                                LEFT JOIN product_product pp ON pol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id	
                                LEFT JOIN account_move as am ON po.id = am.bill_origin
                
                                WHERE (po.invoice_status = 'invoiced' AND pol.purchase_subtype = %s
                                    AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s  AND po.purchase_type =%s )
                                OR 
                                    (po.invoice_status = 'invoiced' AND pol.purchase_subtype = %s
                                            AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s  AND po.purchase_type = %s) 
                       
                                """
        
        #Note 23 excludes zero and exempt
        pur_total = """
                            SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(ROUND(SUM(pol.price_subtotal),2),0.00) as pro_price, 
                                COALESCE(SUM(pol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(pol.price_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                            FROM purchase_order_line pol 
                                LEFT JOIN product_product pp ON pol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id	
                                LEFT JOIN account_move as am ON po.id = am.bill_origin
                
                                WHERE po.invoice_status = 'invoiced'AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s 
                                                                     
                       
                                """
                                #  AND pol.purchase_subtype != 'zero' AND pol.purchase_subtype != 'exempt'


        row_loc =   [{
                        'sn' : '-',
                        'pro_des' : '-', 
                        'pro_hs' : '-', 
                        'pro_name' : '-', 
                        'pro_price' : 0.00, 
                        'pro_sd' : 0.00, 
                        'pro_vat' : 0.00, 
                        'comment' : 'local', 
                    } ]
        row_for =   [{
                    'sn' : '-',
                    'pro_des' : '-', 
                    'pro_hs' : '-', 
                    'pro_name' : '-', 
                    'pro_price' : 0.00, 
                    'pro_sd' : 0.00, 
                    'pro_vat' : 0.00, 
                    'comment' : 'foreign', 
                } ]
        cats = ['exempt','standard', 'not_standard', 'special','specific']
        for cat in cats:
            if cat == 'exempt':               
                #Local
                self.env.cr.execute(rows_query, ('exempt', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note6_z_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(tot_query, ('exempt', first_of_month, last_of_month,self.company_id.id,'local' ))   
                exempt_total_loc = self.env.cr.fetchall() 
                # note6_ka = exempt_total_loc[0][4]  
                # note6_kha = exempt_total_loc[0][6] 

            if cat == 'standard':               
                #Local                
                self._cr.execute(rows_query, ('standard', first_of_month, last_of_month,self.company_id.id,'local'))  
                note7_z_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('standard', first_of_month, last_of_month,self.company_id.id,'local'))  
                standard_total_loc = self.env.cr.fetchall() 
                               
            if cat == 'not_standard':
                #Local                
                self._cr.execute(rows_query, ('not_standard', first_of_month, last_of_month,self.company_id.id,'local'))  
                note8_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('not_standard', first_of_month, last_of_month,self.company_id.id,'local' ))  
                nstandard_total_loc = self.env.cr.fetchall() 
                
            if cat == 'special':
                #Local                
                self._cr.execute(rows_query, ('special', first_of_month, last_of_month,self.company_id.id,'local'))  
                note9_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('special', first_of_month, last_of_month,self.company_id.id,'local' ))  

                # import pdb; pdb.set_trace()
                special_total_loc = self.env.cr.fetchall()                
                note9_l = row_loc if len(note9_l) == 0 else note9_l


            if cat == 'specific':
                #Local                
                self._cr.execute(rows_query, ('not_reyat_ser', first_of_month, last_of_month,self.company_id.id,'local'))  
                note10_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('not_reyat_ser', first_of_month, last_of_month,self.company_id.id,'local' ))  
                # notreyatser_total_loc = self.env.cr.fetchall() 
                specific_total_loc = self.env.cr.fetchall()                

                note10_l = row_loc if len(note10_l) == 0 else note10_l

        self.env.cr.execute(pur_total, (first_of_month, last_of_month,self.company_id.id,))   
        note11 = total_pur = self.env.cr.fetchall() 
        # note11note11_kha = total_pur

        note12 = 0.00#Bortoman kormeyede prodeyo mot kor
        note13 = 0.00#Somaponi jer er sohito somoboyer por n=bortoman kormeyede prodeyo mot kor
                    #12-21

        note14 = 0.00#Unpaid vat interest#Needs to be calculated
        note15_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='pen'"""
        self._cr.execute(note15_q,(first_of_month, last_of_month, self.company_id.id))  
        note15 = self.env.cr.fetchall()[0][0] #Punishment and Fines  

        #Afgari sulko????
        note16 = 0.00
        note16_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='dev'"""
        self._cr.execute(note16_q,(first_of_month, last_of_month, self.company_id.id))  
        note16 = self.env.cr.fetchall()[0][0] #Afgari sulko

        #--------------------------------
        note17_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='dev'"""
        self._cr.execute(note16_q,(first_of_month, last_of_month, self.company_id.id))  
        note17 = self.env.cr.fetchall()[0][0] #Development Surcharge
        
        
        note18_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='info'"""

        self._cr.execute(note18_q,(first_of_month, last_of_month, self.company_id.id))  
        note18 =  self.env.cr.fetchall()[0][0]#Information Techonology Development Surcharge

        note19_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='health'"""        
        
        self._cr.execute(note19_q ,(first_of_month, last_of_month, self.company_id.id))  
        note19 = self.env.cr.fetchall()[0][0]#('health', 'Health Protection Surcharge')

        note20_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='env'"""         
        self._cr.execute(note20_q,(first_of_month, last_of_month, self.company_id.id))        
        note20 = self.env.cr.fetchall()[0][0]#('env', 'Environment Protecttion Surcharge'),


        #*******************************************

        month = str(self.month) -1 if int(self.month) -1 >0 else '12'
        year = str(self.year) if int(self.month) -1 >0 else int(self.year) -1 
        # note21 = self.env['vat.ninetwo'].sudo().search([('month','=',month),('year','=',year)], order ='id desc', limit=1).note30
        note21 = 0.00
        if not note21:
            note21 = 0.00

        
        #PART-8: Treasury Payments
        # print('----------------')
        import datetime
        last_month_end = first_of_month - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        #Calculation from evl_payments model        


        note22_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'vat'"""         
        self._cr.execute(note22_q,(first_of_month, last_of_month, self.company_id.id))        
        note22 = self.env.cr.fetchall()[0][0]#Treasury Paid VAT

        note22_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
                        AND ep.purpose = 'sd' 
                        GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note22_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note22_t = self.env.cr.dictfetchall()#Treasury Paid VAT#Subform_kha
        




        note23_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'vatin'"""         
        self._cr.execute(note23_q,(first_of_month, last_of_month, self.company_id.id))        
        note23 = self.env.cr.fetchall()[0][0]#Tvatin


        note23_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				AND ep.purpose = 'vatin' 
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note23_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note23_t = self.env.cr.dictfetchall()#Tvatin#kha
       

        note24_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='pen'"""         
        self._cr.execute(note24_q,(first_of_month, last_of_month, self.company_id.id))        
        note24 = self.env.cr.fetchall()[0][0]#Punishment and Fines  

        note24_q_t = """SELECT 
                            ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                            ep.challan as challan,
                            ep.bank as bank,	
                            ep.branch as branch,
                            ep.date_submit as date, 
                            ep.acc_code as acc_code,
                            COALESCE(ep.amount, 0.00) as amt,
                            null as comment                                 
                        FROM evl_payments as ep   
                            WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
                            AND  ep.purpose = 'surcharge' AND ep.surcharge_type='pen'
                            GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note24_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note24_t = self.env.cr.dictfetchall()

        ##Excide Dauty
        note25_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'excise'"""         
        self._cr.execute(note25_q,(first_of_month, last_of_month, self.company_id.id))        
        note25 = self.env.cr.fetchall()[0][0]#Excide Dauty


        note25_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE( round(  ep.amount ,2), 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				AND ep.purpose = 'excise'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note25_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note25_t = self.env.cr.dictfetchall()

        ##Development Surcharge
        note26_q = """SELECT COALESCE( round(  es.amount ,2), 0.00) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='dev'"""         
        
        self._cr.execute(note26_q,(first_of_month, last_of_month, self.company_id.id))        
        # import pdb; pdb.set_trace()
        # print(note26)
        note26 = self.env.cr.fetchall()[0][0] if len(self.env.cr.fetchall()) > 0 else 0.00#Development Surcharge
        note26_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE( round(  ep.amount ,2), 0.00) as amt,
                                    null as comment                                  
                    
                        FROM evl_payments as ep                                 
                                       WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				    AND ep.purpose = 'surcharge' AND ep.surcharge_type='dev'
                    GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note26_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note26_t = self.env.cr.dictfetchall()

        ##Information Techonology Development Surcharge
        note27_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='info'"""         
        self._cr.execute(note27_q,(first_of_month, last_of_month, self.company_id.id))        
        note27 = self.env.cr.fetchall()[0][0]#Information Techonology Development Surcharge

        note27_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				  AND ep.purpose = 'surcharge' AND ep.surcharge_type='info'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note27_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note27_t = self.env.cr.dictfetchall()



        ##('health', 'Health Protection Surcharge')
        note28_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='health'"""         
        self._cr.execute(note28_q,(first_of_month, last_of_month, self.company_id.id))        
        note28 = self.env.cr.fetchall()[0][0]#('health', 'Health Protection Surcharge')

        note28_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				   AND ep.purpose = 'surcharge' AND ep.surcharge_type='health'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note28_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note28_t = self.env.cr.dictfetchall()

        #('env', 'Environment Protecttion Surcharge'),
        note29_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='env'"""         
        self._cr.execute(note29_q,(first_of_month, last_of_month, self.company_id.id))        
        note29 = self.env.cr.fetchall()[0][0]#('env', 'Environment Protecttion Surcharge'),

        note29_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				   AND ep.purpose = 'surcharge' AND ep.surcharge_type='health'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note29_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note29_t = self.env.cr.dictfetchall()


        note30 = note22 - note13

        sub_ka = { 
                    'print_name':'Main Copy',
                    #Part1
                    'bin':self.company_id.vat,
                    'company':self.company_id.name,
                    'address':address,
                    'business_type': dict(self.company_id._fields['owner_type'].selection).get(self.company_id.owner_type),
                    'operation_type' : dict(self.company_id._fields['economic_activity'].selection).get(self.company_id.economic_activity),

                    #Part2
                    'tax_period': {'month': self.month,'year':self.year},
                    'type': '1',
                    'last':'1',
                    'date' : self.sub_date.strftime("%d/%m/%Y"),
                    
                    
                    #  'total_pur':total_pur,
                    
                    'note1_z_l': note1_z_l,
                    'note1_z_t':note1_z_t,
                    'note2_z_l':note2_z_l,
                    'note2_z_t':note2_z_t,
                    'note3_l':note3_l,
                    'note3_t':note3_t,
                    'note4_l':note4_l,
                    'note4_t':note4_t,
                    'note5_t':note5_t,
                    'note6_z_l':note6_z_l,
                    'exempt_total_loc':exempt_total_loc,
                    'note7_z_l':note7_z_l,
                    'standard_total_loc':standard_total_loc,
                    'nstandard_total_loc':nstandard_total_loc,
                    'specific_total_loc' : specific_total_loc,      
                    'special_total_loc' : special_total_loc,      

                    'note8_l':note8_l,
                    # 'note9_t':note9_t,
                    'note9_l' : note9_l,
                         
                    'note11':note11,

                    'note10_l': note10_l,
                    # 'notreyatser_total_loc': notreyatser_total_loc,


                    'note12':note12,
                    'note13':note13,

                   
                    'note14': note14,
                    'note15': note15,
                    'note16': note16,
                    'note17': note17,
                    'note18': note18,
                    'note19': note19,
                    'note20': note20,
                    'note21': note21,

                    'note22':note22,
                    'note22_t': note22_t,                     
                    'note23':note23,
                    'note23_t': note23_t,                     
                    'note24':note24,
                    'note24_t': note24_t, 
                    'note25_t':note25_t,
                    'note25':note25,
                    'note26_t':note26_t,
                    'note26':note26,
                    'note27_t':note27_t,

                    'note27':note27,

                    'note28':note28,
                    
                    'note28_t':note28_t,
                    'note29':note29,
                    'note29_t': note29_t,
                    'note30':note30,
                    
              
                    'report_date':self.report_time,

                    'total_pur':total_pur,


                    }       
        page2={}
        page2 = {'sub_ka':sub_ka}
        pages ={'page1' : page1, 'page2' : page2 , 'sub_ka' :  sub_ka} 

        pg_no = pg_toto =1
    
        result = {}
        # result['company_id'] = data['form']['company_id'][0] or False
        result['pages'] = pages

        return result

    def _print_report(self, data,id):
        raise NotImplementedError()

    def _generate_data(self,sub_ka,rec_id):       

        ka=self.env['subform.co'].search([('id','=',rec_id)])
        for row in ka:
            if row.note_type in ['note1_z_l','note2_z_l','note3_l','note4_l','note5_l','note7_l','note8_l',
                        'note10_z_l','note11_z_f', 'note12_z_l','note13_z_f','note14_z_l','note15_z_f','note15_z_f',
                        'note16_l','note17_f','note18_l','note19_l','note20_f','note21_l','note22_f']:                    

                sub_ka[row.note_type].append(row.read(list(set(row._fields))))

        yuo=self.env['subform.yuo'].search([('id','=',rec_id)])
        for row in yuo:
            if row.note_type in ['note24','note29']:
                sub_ka[row.note_type].append(row.read(list(set(row._fields))))

        ga=self.env['subform.yuo'].search([('id','=',rec_id)])
        for row in ga:
            if row.note_type in ['note6_l','note18_l']:
                sub_ka[row.note_type].append(row.read(list(set(row._fields))))

        co=self.env['subform.yuo'].search([('id','=',rec_id)])
        for row in co:
            if row.note_type in ['note30_l']:
                sub_ka[row.note_type].append(row.read(list(set(row._fields))))


        cho=self.env['subform.yuo'].search([('id','=',rec_id)])
        for row in cho:
            if row.note_type in ['note52_t','note53_t','note54_t','note55_t','note56_t','note57_t','note58_t','note59_t','note60_t','note61_t']:
                sub_ka[row.note_type].append(row.read(list(set(row._fields))))

        sub_ka = sub_ka[0]
        len_check = len(self.env['vat.nineone'].search([('month','=',self.month),('year','=',self.year)]))
        sub_ka['print_name'] = 'Copy 1' if len_check == 1 else ('Copy 2' if len_check > 1 else 'Main Copy')

        sub_ka['tax_period'] = {}
        sub_ka['tax_period']['month'] = sub_ka['month']
        sub_ka['tax_period']['year'] = sub_ka['year']
        return sub_ka





    def convert_bangla(self,data):
        sub_ka = data['pages']['sub_ka']
        
        for key,value in sub_ka.items():
            if key == 'special_total_loc':
                import pdb; pdb.set_trace()
            if key in ['note12','note13','note14','note15','note16','note17','note18','note19','note20','note21',
                        'note22','note23','note24','note25','note26','note27','note28','note29','note30']:
                sub_ka[key] =  bangla.convert_english_digit_to_bangla_digit(str(sub_ka[key])) if sub_ka[key] != None else ''

            if key in ['note1_z_t','note2_z_t','note3_t','note4_t','note5_t','note6_t','note7_t','note8_t'
                ,'note9_t','note10_z_l','note11_z_f',
                'note22_t','note23_t','note24_t','note25_t','note26_t','note27_t','note28_t','note29_t'
                
                ,'zero_total_loc','zero_total_for','exempt_total_loc',
                'exempt_total_for','standard_total_loc','standard_total_for','nstandard_total_loc',
                'nstandard_total_for','specific_total_loc','notreyat_total_loc','special_total_loc'
                'notreyat_total_for','notreyatser_total_loc','notreyatser_total_for',
                'total_pur', 'note24_t', 'note29_t', 
                'note1_z_l','note2_z_l','note3_l','note4_l','note5_l','note6_l',
                'note7_l',]:

                if type(sub_ka[key]) != float:
                    for line in sub_ka[key]:
                        
                        if type(line) == dict:
                            for key,value in line.items():   
                                    if key in ['sn','pro_price','pro_sd','pro_vat']:
                                        line[key] =  bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''

                        if type(line) == tuple:

                            line = list(line)                    
                            line[4] =  bangla.convert_english_digit_to_bangla_digit(str(line[4])) if line[4] != None else ''
                            line[5] =  bangla.convert_english_digit_to_bangla_digit(str(line[5])) if line[5] != None else ''
                            line[6] =  bangla.convert_english_digit_to_bangla_digit(str(line[6])) if line[6] != None else ''
                            sub_ka[key][0] = tuple(line)   

        data['pages']['sub_ka'] = sub_ka
        return data

        # else:
        #     return data
            # #------------------------------------

    def check_mushak(self,data):
        
        check = self.env['vat.nineone'].search([('month','=',self.month),('year','=',self.year)],order='id asc',limit=1)
        if len(check) > 0:
            copy_flag=True
            sub_ka = check.read(list(set(check._fields)))
            sub_ka = self._generate_data(sub_ka,check.id)
            pages={}


            for key,value in sub_ka.items():
                if key in ['note25_t','note27_t','note28_t','note30_t','note31_t','note33_t',
                    'note34_t', 'note36', 'note35','note36','note37','note38','note39','note40',
                    'note41','note42','note43','note44','note45','note46',
                    'note47','note48','note49','note50','note51','note52',
                    'note53' ,'note54' , 'note55', 'note56', 'note57' ,  'note58', 
                    'note59', 'note60', 'note61' , 'note62' , 'note63', ]:
                    sub_ka[key] = float(sub_ka[key])
                    
                if key in ['note1_z_t','note2_z_t','note3_t','note4_t','note5_t','note6_t','note7_t','note8_t'
                    ,'note9_t','note10_z_l','note11_z_f','note12_z_l','note13_z_f','note14_z_l','note15_z_f',
                    'note16_l','note17_f','note18_l','note19_l','note20_f','note21_l','note22_f',
                    'note8_l','note24','note29','note52_t','note53_t','note54_t','note55_t','note56_t','note57_t','note58_t',
                    'note59_t','note60_t','note61_t','zero_total_loc','zero_total_for','exempt_total_loc',
                    'exempt_total_for','standard_total_loc','standard_total_for','nstandard_total_loc',
                    'nstandard_total_for','specific_total_loc','notreyat_total_loc',
                    'notreyat_total_for','notreyatser_total_loc','notreyatser_total_for',
                    'total_pur', 'note24_t','debit_note_vat', 'note29_t', 'credit_note_vat',
                    'note1_z_l','note2_z_l','note3_l','note4_l','note5_l','note6_l',
                    'note7_l',]:
                    
                    import ast

                    mm = sub_ka[key].strip('][')
                    sub_ka[key] = [ast.literal_eval(mm)] if len(mm) > 0 else []
                    if len(sub_ka[key]) > 0:
                        if type(sub_ka[key][0]) == tuple and len(sub_ka[key][0]) > 0:
                            if type(sub_ka[key][0][0]) == dict: 
                                x=[]
                                for item in sub_ka[key][0]:
                                    x.append(item)
                                sub_ka[key] = x

       
            sub_ka['copy_flag'] = True
            page1= { 'pg_no': '1','report_date': self.report_time.strftime("%d/%m/%Y %H:%M") }
            pages['sub_ka'] = sub_ka

            page2={}
            page2 = {'sub_ka':sub_ka}
            pages ={'page1' : page1, 'page2' : page2 , 'sub_ka' :  sub_ka} 

            data['pages'] = pages

        # #------------------------------------
        else:


            copy_flag=False
            rows = self._build_contexts(data)       
            data['pages'] = rows['pages']
            data['pages']['sub_ka']['copy_flag'] = False

            # #------------------------------------
            rec = self.env['vat.nineone']
            rec.month = self.month
            rec.year =self.year
            
            self.env['vat.nineone'].create(data['pages']['sub_ka'],)  


        return data

    def print_preview(self): 
        data = self.check_mushak({})
        data = self.convert_bangla(data) if self.language == 'bangla' else data


        return self.env.ref('evl_vat.mushak_9_2_preview').report_action(self, data=data)


    def print_mushak_9_1(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('sale.order.line', 'purchase.order.line')
        data['form'] = self.read()[0]
        data = self.check_mushak({})
        data = self.convert_bangla(data) if self.language == 'bangla' else data
        return self.env.ref('evl_vat.mushak_9_2_action').report_action(self, data=data)

 
 