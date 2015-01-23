# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
##############################################################################

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc

class internship_request_wizard(osv.osv_memory):
    _name = "internship.request.wizard"
    _description = "internship request wizard"
    
    _columns = {
                'name':fields.char(string=u'To do',help='the name of this action',size=128,),
                #'comment':fields.char(string=u'comments',help='the infomation you want to deliver to person of the next step',size=512),
    }
    _defaults = {
        #'name': 1,
    }
    
    def mark_hr_member_as_social_secured(self, cr, uid, ids, context={}):
        hr_member_ids = context.get('active_ids') or [context.get('active_id')]
        # if not hr_member_ids:
        #     raise osv.except_osv(u'警告',u'请至少选择一个实习生!')
        hr_member_obj = self.pool.get('hr.member')
        for hm in hr_member_obj.browse(cr, 1, hr_member_ids, context=context):
            hm.write({'social_security_processed':True,
                      'social_security_processer':uid,
                      'social_security_processed_date':fields.date.context_today(hr_member_obj,cr, uid)},context=context)

    def mark_hr_member_as_social_security_out(self, cr, uid, ids, context={}):
        hr_member_ids = context.get('active_ids') or [context.get('active_id')]
        # if not hr_member_ids:
        #     raise osv.except_osv(u'警告',u'请至少选择一个实习生!')
        hr_member_obj = self.pool.get('hr.member')
        for hm in hr_member_obj.browse(cr, 1, hr_member_ids, context=context):
            hm.write({'social_security_out':True,
                      'social_security_outer':uid,
                      'social_security_out_date':fields.date.context_today(hr_member_obj,cr, uid)},context=context)
internship_request_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
