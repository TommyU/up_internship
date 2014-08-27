# -*- coding: utf-8 -*-
#/#############################################################################
#
#    Your Company
#    Copyright (C) 2004-TODAY Your Company(www.yourcompany.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#/#############################################################################
from osv import osv, fields

class internship_request(osv.osv):
    _name = 'internship.request'

    _columns = {
        'state':fields.selection([
                                     ('draft','draft'),
                                     ('director_audit','director approval'),
                                     ('hr','HR approval'),
                                     ('meal_card','meal card info'),
                                     ('accepted','accepted'),
                                     ('to_resign','to resign'),
                                     ('manager_appr','manager approval'),
                                     ('diet_record','diet records upload'),
                                     ('director_appr','director approval'),
                                     ('checking_out','checking out'),
                                     ('resigned','resigned'),
                                     ('stoped','stoped'),
                                 ],string='state'),
        'preset_dept': fields.many2one('hr.department', string='preset dept.',  required=True),
        'preset_instructor': fields.many2one('hr.employee', string='preset instructor',  required=False),
        'start_date': fields.date(string='start date',  required=True),
        'end_date': fields.date(string='end date',  required=True),
        'checkin_company_date': fields.date(string='checkin company date',  required=False),
        'checkin_hotel_date': fields.date(string='checkin hotel date',  required=False),
        'hotel_receptionist': fields.char(size=64, string='hotel receptionist ', required=False, help="hotel receptionist "),
        'arrival_notice': fields.binary(string='arrival notice',  required=False),
        'meal_card_no': fields.char(size=32, string='meal card no.', required=False, help="meal card number"),
        'meal_card_status': fields.selection([('dispatched','dispatched'),('reserved','reserved'),('returned','returned')], string='meal card status',  required=False),
        'pledge_money_state': fields.selection([('payed','payed'),('returned','returned')], string='pledge money state',  required=False),
        'hotel_checkout_date': fields.date(string='hotel checkout date',  required=False),
        'resignation_date': fields.date(string='resignation date',  required=False),
        'diet_record': fields.binary(string='diet record',  required=False),
        'internship': fields.many2one('hr.member', string='internship',  required=True),
        }

    _defaults={
        'state':'draft',

    }

internship_request()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
