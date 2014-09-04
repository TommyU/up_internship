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
from openerp.addons.workflow_china import workflow_func
from openerp.tools.translate import _

class internship_request(osv.osv):
    _name = 'internship.request'

    _columns = {
        'state':fields.selection([
                                     ('draft','draft'),
                                     ('director_audit','director approval'),
                                     ('hr','HR approval'),
                                     ('meal_card','working card info'),
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
        'meal_card_no': fields.char(size=32, string='working card no.', required=False, help="meal card number"),
        'meal_card_memo': fields.char(size=256, string='working card memo.', required=False, help="meal card memo"),
        'meal_card_status': fields.selection([('dispatched','dispatched'),('reserved','reserved'),('returned','returned')], string='working card status',  required=False),
        'pledge_money_state': fields.selection([('payed','payed'),('returned','returned')], string='pledge money state',  required=False),
        'hotel_checkout_date': fields.date(string='hotel checkout date',  required=False),
        'resignation_date': fields.date(string='resignation date',  required=False),
        'diet_record_needed':fields.selection([('yes','yes'),('no','no')],string='diet records required'),
        'diet_record': fields.binary(string='diet record',  required=False),
        'internship': fields.many2one('hr.member', string='internship',  required=True),
        'audditing_logs':fields.function(workflow_func._get_workflow_logs, string='auditting logs', type='one2many', relation="workflow.logs",readonly=True),
        }

    _defaults={
        'state':'draft',

    }

    def create(self, cr, uid, vals, context={}):
        """
        当一个实习生进入到草稿-已离院状态间，用户不能再创建新的实习申请记录
        """
        if vals.get('internship',False):
            ids = self.search(cr, uid, [('internship','=',vals.get('internship',-1)),('state','not in',('draft','stoped','resigned'))], context =context)
            if ids:
                raise osv.except_osv(_('Fobbidden!'),
                                     _('This intern has another request which is under audditting!.'))

        return super(internship_request,self).create(cr,uid,vals,context=context)

    def unlink(self, cr, uid, ids, context={}):
        """
        限制删除在跑的单据
        """
        for req in self.browse(cr,uid,ids,context=context):
            if req.state not in ('draft','stoped'):
                raise osv.except_osv(_('Fobbidden!'),
                                     _('Records that are not in draf status could not be deleted!'))

        return super(internship_request,self).unlink(cr,uid,ids,context=context)

internship_request()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
