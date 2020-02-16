# -*- coding: utf-8 -*-

from odoo import models, fields, api


class bloodGroup(models.Model):
    _name = "evl.bloodgroup"
    _description = "Blood Group"
    _rec_name = 'employee_id'

    
    
    
    @api.depends('group')
    def name_get(self):
        result = []
        for record in self:
            
            
            name = record.group
            
            result.append((record.id, name))
        return result
    
    
    employee_id = fields.Many2one('hr.employee', string='Employee',store=True)

    group = fields.Char(string="")


class reference(models.Model):
    _name = "evl.reference"
    _description = "Employee Reference"
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee',store=True)
    name = fields.Char(string="Name")
    refNumber = fields.Char(string="Contact")

class nominee(models.Model):
    _name = "evl.employee.nominee"
    _description = "Employee Nominee"
    _rec_name = 'employee_id'



    employee_id = fields.Many2one('hr.employee', string='Employee',store=True)
    name = fields.Char(string="Nominee Name")
    contact = fields.Char(string='Contact Number')
    
    address = fields.Char(string='Address')
    relation = fields.Char(string='Relation with Employee')
    percentage = fields.Float(string='% of Benefit.')
    


class education(models.Model):
    _name = "evl.education"
    _description = "Education"
    _rec_name = 'institute'
    


    institute = fields.Char(string="Institute")
    degree = fields.Char(string="Name of Degree")
    studyField = fields.Char(string="Field of Study")
    employee_id = fields.Many2one('hr.employee', string='Employee',store=True)

    fromDate = fields.Date(string="From")
    toDate = fields.Date(string="To")
    result = fields.Char(string="CGPA/Grade")


class experience(models.Model):
    _name = "evl.work.experience"
    _description = "Work Experience"
    _rec_name = 'position'

    position = fields.Char(string="Position")
    department = fields.Char(string="Department")
    organization = fields.Char(string="Organization")

    employee_id = fields.Many2one('hr.employee', string='Employee',store=True)

    fromDate = fields.Date(string="From")
    toDate = fields.Date(string="To")
    duration = fields.Char(string="Duration of Experience")


class training(models.Model):
    _name = "evl.training"
    _description = "Employee Training"
    _rec_name = 'title'
    

    title = fields.Char("Title")
    organization = fields.Char("Name of Organization")

    employee_id = fields.Many2one('hr.employee','Employee',store=True)

    fromDate = fields.Date("From")
    toDate = fields.Date("To")
    duration = fields.Char("Duration of Training")

class punishments(models.Model):
    _name = "evl.punishments"
    _description = "Employee Punishments"
    _rec_name = 'employee_id'

    @api.depends('employee_id')
    def name_get(self):
        result = []
        for record in self:      
            result.append((record.id, record.employee_id.name))
        return result

  
    @api.onchange('employee_id')
    def _onchange_field(self):
        self.department_id = self.employee_id.department_id
    
    
    employee_id = fields.Many2one('hr.employee','Employee',store=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('eevl.punishments'),store= "True")
    department_id = fields.Many2one('hr.department','Department',related = 'employee_id.department_id',store= "True")

    pDate = fields.Date("Date")
    note = fields.Char(string='Remark')


class evlEmployee(models.Model):
    _inherit = "hr.employee"

    fatherName = fields.Char(string="Father's Name")

    mothersName = fields.Char(string="Mother's Name")
    spouseName = fields.Char(string="Spouse")

    religion = fields.Selection(
                [("one", "Islam"), ("two", "Hindu"), ("three", "Christian")], string=""
            )
    
    # def write(self, values):
    #     """
    #         Update all record(s) in recordset, with new value comes as {values}
    #         return True on success, False otherwise
    
    #         @param values: dict of new values to be set
    
    #         @return: True on success, False otherwise
    #     """
    #     import pdb; pdb.set_trace()
    
    #     result = super(evlEmployee, self).write(values)
    
    #     return result
    
    nid = fields.Char(string="National Id")
    
    group = fields.Many2one("evl.bloodgroup", string="Blood Group",compute='_compute_field_name' )

    reference = fields.Many2many(string="Employee Reference", comodel_name="evl.reference")

    education = fields.Many2many(string="Qualifications", comodel_name="evl.education")
    workExperience = fields.Many2many(string="Experiences", comodel_name="evl.work.experience")
    training = fields.Many2many(string="Trainings",comodel_name="evl.training")


    punishments = fields.Many2many(string="Punishments", comodel_name="evl.punishments")
    nominee = fields.Many2many(string="Nominees", comodel_name="evl.employee.nominee")
    presentAddress = fields.Char(string='Present Address')
    permanentAddress = fields.Char(string='Permanenet Address')


  
    def _compute_field_name(self):
        
        self.sudo().punishments =  [(6,0, [i.id for i in self.env['evl.punishments'].sudo().search([('employee_id','=',self.id)])])]

        self.sudo().education =  [(6,0, [i.id for i in self.env['evl.education'].sudo().search([('employee_id','=',self.id)])])]
        self.sudo().workExperience =  [(6,0, [i.id for i in self.env['evl.work.experience'].sudo().search([('employee_id','=',self.id)])])]
        self.sudo().training =  [(6,0, [i.id for i in self.env['evl.training'].sudo().search([('employee_id','=',self.id)])])]
        self.sudo().group = self.env['evl.bloodgroup'].sudo().search([('employee_id','=',self.id)]).id

        self.sudo().nominee =  [(6,0, [i.id for i in self.env['evl.employee.nominee'].sudo().search([('employee_id','=',self.id)])])]

        return
