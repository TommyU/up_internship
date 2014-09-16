# -*- coding: utf-8 -*-
#/#############################################################################
#
#    Your Company
#    Copyright (C) 2004-TODAY Your Company(www.odoo.com).
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

from openerp.osv import osv, fields


class recruitment_interships(osv.Model):
    _inherit='hr.member'

    def _get_internships(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        model = self._name
        if not model:
            return {}
        model_obj = self.pool.get(model)
        internship_obj = self.pool.get('internship.request')
        for ms in model_obj.browse(cr,uid,ids,context=context):
            res[ms.id]= internship_obj.search(cr,uid,[('internship','=',ms.id),('state','not in',('draft',))])
        return res

    def _interning(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        model = self._name
        if not model:
            return {}
        model_obj = self.pool.get(model)
        internship_obj = self.pool.get('internship.request')
        for ms in model_obj.browse(cr,uid,ids,context=context):
            res[ms.id]= bool(internship_obj.search(cr,uid,[('internship','=',ms.id),('state','not in',('draft','stoped','resigned'))]))
        return res

    _columns = {
        'interning':fields.function(_interning, string='interning', type='boolean',readonly=True),
        'internships': fields.function(_get_internships, string='internships', type='one2many', relation="internship.request",readonly=True),
    }

recruitment_interships()
