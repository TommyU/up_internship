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


class internship_hotel_receptionist(osv.Model):
    _name='internship.hotel.receptionist'

    _columns = {
        'name':fields.char(size=32, string='name', required=True, help="name of the receptionist"),
        'phone': fields.char(size=32, string='phone', required=False, help="phone number of the receptionist"),
    }

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','phone'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['phone']:
                name = name+' - '+record['phone']
            res.append((record['id'], name))
        return res

internship_hotel_receptionist()
