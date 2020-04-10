# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import copy 
from itertools import groupby

class VatNineOne(models.Model):
    _name = 'vat.ninetwo'
    _description = 'VAT NineTwo'


    print_name = fields.Char("print_name") 
    bin = fields.Char("bin") 
    company = fields.Char("company") 
    address = fields.Char("address") 
    business_type = fields.Char("business_type") 
    operation_type = fields.Char("operation_type") 

    tax_period = fields.Char("tax_period") 

    month = fields.Selection(
                    [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                    ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                    ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                    string='Month')
    year = fields.Integer( string='Year')
    
    type = fields.Integer("type") 
    last = fields.Integer("last") 
    date = fields.Char("date")     
    
    note1_z_t = fields.Char("note1_z_t")    
    note2_z_t = fields.Char("note2_z_t") 
    note3_t = fields.Char("note3_t") 
    note4_t = fields.Char("note4_t") 
    note5_t = fields.Char("note5_t") 

    
    note6_t = fields.Char("note6_t") 
    note7_t = fields.Char("note7_t") 
    note8_t = fields.Char("note8_t") 
    note9_t = fields.Char("note9_t") 
    # zero_total_loc = fields.Char("zero_total_loc") 
    # zero_total_for = fields.Char("zero_total_for") 
    
    exempt_total_loc = fields.Char("exempt_total_loc") 
    exempt_total_for = fields.Char("exempt_total_for") 
    standard_total_loc = fields.Char("standard_total_loc") 
    standard_total_for = fields.Char("standard_total_for") 
    nstandard_total_loc = fields.Char("nstandard_total_loc") 
    nstandard_total_for = fields.Char("nstandard_total_for") 
    specific_total_loc = fields.Char("specific_total_loc") 
    notreyat_total_loc = fields.Char("notreyat_total_loc") 
    notreyat_total_for = fields.Char("notreyat_total_for") 
    notreyatser_total_loc = fields.Char("notreyatser_total_loc") 
    notreyatser_total_for = fields.Char("notreyatser_total_for") 
    total_pur = fields.Char("total_pur") 
    
    note12 = fields.Char("note12") 
    note13 = fields.Char("note13") 
    note14 = fields.Char("note14") 
    note15 = fields.Char("note15")
    note16 = fields.Char("note16")           


    note17 = fields.Char("note17") 
    note18 = fields.Char("note18") 
    note19 = fields.Char("note19")
    note20 = fields.Char("note20") 
    note21 = fields.Char("note21")

    note22 = fields.Text("note22") 
    note23 = fields.Text("note23") 
    note24 = fields.Text("note24") 
    note25 = fields.Text("note25") 
    note26 = fields.Text("note26") 
    note27 = fields.Text("note27") 
    note28 = fields.Text("note28") 
    note29 = fields.Text("note29") 
 


    #------------------Rows Data
    note1_z_l = fields.Char("note1_z_l") 
    note2_z_l = fields.Char("note2_z_l")
    note3_l = fields.Char("note3_l")
    note4_l = fields.Char("note4_l")

    note6_z_l = fields.Char("note6_z_l")
    note7_z_l = fields.Char("note7_z_l")
    note8_l = fields.Char("note8_l")
    note9_l = fields.Char("note8_l")
    note9_l = fields.Char("note9_l")
    note10_l = fields.Char("note10_l")



    

    note3_l = fields.Text("note3_l")     
    note4_l = fields.Text("note4_l")   
    note5_l = fields.Text("note5_l")   
    note6_l = fields.Text("note6_l")   
    note7_l = fields.Text("note7_l")   
    note8_l = fields.Text("note8_l")   

    note22_t = fields.Text("note8_l")  
    note23_t = fields.Text("note23_t") 
    note24_t = fields.Text("note24_t") 
    note25_t = fields.Text("note25_t") 
    note26_t = fields.Text("note26_t") 
    note27_t = fields.Text("note27_t") 
    note28_t = fields.Text("note28_t")  

    note30 = fields.Text("note30")



    @api.model
    def create(self,values):
        copy_flag = values['copy_flag']
        del(values['copy_flag'])


        rec = super(VatNineOne, self).create(values)
        rec.month = values['tax_period']['month']
        rec.year = values['tax_period']['year']
        

        if copy_flag == False:
        
            for key,value in values.items():
                if key in ['note1_z_l','note2_z_l','note3_l','note4_l','note5_l','note7_l','note8_l',
                            'note10_z_l','note11_z_f', 'note12_z_l','note13_z_f','note14_z_l','note15_z_f','note15_z_f',
                            'note16_l','note17_f','note18_l','note19_l','note20_f','note21_l','note22_f']:

                    for item in value:
                        sub=self.env['subform.ka']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)

                if key in ['note24','note29']:
                    for item in value:                    
                        sub=self.env['subform.yuo']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)

                if key in ['note6_l','note18_l']:
                    for item in value:
                        sub=self.env['subform.ga']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)

                if key in ['note30_l']:
                    for item in value:
                        sub=self.env['subform.co']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)

                if key in ['note52_t','note53_t','note54_t','note55_t','note56_t','note57_t','note58_t','note59_t','note60_t','note61_t']:
                    for item in value:
                        sub=self.env['subform.cho']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)
        return rec
class SubformKa(models.Model):
    #ka, kha together
    _name = 'subform.ka'
    _description = 'Subform Ka'
    _rec_name = 'id'

    sn = fields.Char(string="Sn", required=True)
    pro_des= fields.Char(string="pro_des")
    pro_hs= fields.Char(string="pro_hs")
    pro_name= fields.Char(string="pro_name")
    pro_price= fields.Char(string="pro_price")
    pro_sd= fields.Char(string="pro_sd")
    pro_vat= fields.Char(string="pro_vat")
    pro_vat= fields.Char(string="pro_vat")
    comment = fields.Char('comment')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")


    def create(self,values):
        rec = super(SubformKa, self).create(values)
        return rec


class SubformKha(models.Model):
    #Yuo and Gha#NOte 24,note29
    _name = 'subform.yuo'
    _description = 'Subform Yo'
    _rec_name = 'id'

    sn = fields.Integer(string="Sn", required=True)
    cus_bin= fields.Char(string="pro_des")
    cus_name= fields.Char(string="cus_name")
    cus_address= fields.Char(string="cus_address")
    pro_price= fields.Char(string="pro_price")
    pro_vat= fields.Char(string="pro_vat")
    invoice_no= fields.Char(string="invoice_no")
    invoice_date= fields.Char(string="invoice_date")
    account_code = fields.Char('account_code')
    comment = fields.Char('comment')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")

    @api.model
    def create(self,values):
        rec = super(SubformKha, self).create(values)
        return rec


class SubformCo(models.Model):
    #Cho
    _name = 'subform.co'
    _description = 'Subform Cho'
    _rec_name = 'id'

    sn = fields.Integer(string="Sn", required=True)
    billentry= fields.Char(string="billentry")
    date= fields.Char(string="date")
    cus_house= fields.Char(string="cus_house")
    atv_amt= fields.Char(string="atv_amt")
    comment = fields.Char('account_code')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")

    @api.model
    def create(self,values):
        rec = super(SubformCo, self).create(values)
        return rec



class SubformGa(models.Model):
    #Ga
    _name = 'subform.ga'
    _description = 'Subform Ga'
    _rec_name = 'id'

    sn = fields.Char(string="Sn", required=True)
    pro_des= fields.Char(string="pro_des")
    pro_hs= fields.Char(string="pro_hs")
    pro_name= fields.Char(string="pro_name")
    pro_price= fields.Char(string="pro_price")
    pro_sd= fields.Char(string="pro_sd")
    pro_vat= fields.Char(string="pro_vat")
    pro_vat= fields.Char(string="pro_vat")
    comment = fields.Char('comment')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")


    def create(self,values):
        rec = super(SubformGa, self).create(values)
        return rec


class SubformCho(models.Model):
    #Ga
    _name = 'subform.cho'
    _description = 'Subform cho'
    _rec_name = 'id'

    sn = fields.Char(string="Sn", required=True)
    pro_des= fields.Char(string="pro_des")
    pro_hs= fields.Char(string="pro_hs")
    pro_name= fields.Char(string="pro_name")
    pro_price= fields.Char(string="pro_price")
    pro_sd= fields.Char(string="pro_sd")
    pro_vat= fields.Char(string="pro_vat")
    pro_vat= fields.Char(string="pro_vat")
    comment = fields.Char('comment')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")


    def create(self,values):
        rec = super(SubformCho, self).create(values)
        return rec