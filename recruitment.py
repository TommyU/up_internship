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

    #_interning_search
    def _intern_status_search(self, cr, uid, obj, name, args, context):
        if args:
            state = args[0][2]
            if isinstance(state, (str,unicode)):
                state = [state]
            # intern_obj = self.pool.get('internship.request')
            # iids=intern_obj.search(cr, uid, [('state','=',state)],context=context)
            # ids =[x.internship.id for x in intern_obj.browse(cr,uid, iids,context=context)]
            #以上算法无法处理有多次实习的记录
            sql="""select id, internship,state from internship_request where internship in
                    (
                      select internship from internship_request b where b.state in (%s)
                    ) order by id desc"""%('\''+'\',\''.join(state)+'\'')
            cr.execute(sql)
            res = cr.fetchall()
            # 8;14;"meal_card"
            # 7;3;"meal_card"
            # 6;3;"resigned"
            # 5;7;"meal_card"
            #===>(internship有相同则取最上面一条）
            # 8;14;"meal_card"
            # 7;3;"meal_card"
            # 5;7;"meal_card"
            ids=[]
            res_=[]
            for i in range(len(res)):
                if res[i][1] not in ids:
                    ids.append(res[i][1])
                    res_.append(res[i])#得到最新的实习记录的状态（若有重复实习记录）
            if res_:
                res_ = [x for x in res_ if x[2] in state]#若有重复则最新的状态等于目标状态
                ids = [x[1] for x in res_]
                if ids:
                    return [('id', 'in', tuple(ids))]
        return [('id', '=', '0')]

    def _status(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        model = self._name
        if not model:
            return {}
        model_obj = self.pool.get(model)
        internship_obj = self.pool.get('internship.request')
        for ms in model_obj.browse(cr,uid,ids,context=context):
            in_ids = internship_obj.search(cr,1,[('internship','=',ms.id)])#,('state','not in',('draft','stoped','resigned'))
            if in_ids:
                res[ms.id] = internship_obj.browse(cr, uid, in_ids[-1], context).state
            else:
                res[ms.id] ='none'
        return res

    def _internCD(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        model = self._name
        if not model:
            return {}
        model_obj = self.pool.get(model)
        internship_obj = self.pool.get('internship.request')
        for ms in model_obj.browse(cr,uid,ids,context=context):
            in_ids = internship_obj.search(cr,uid,[('internship','=',ms.id),('state','not in',('stoped','resigned'))])
            if in_ids:
                d = internship_obj.browse(cr, uid, in_ids[-1], context).c_date
                if d:
                    res[ms.id] = d
                else:
                    res[ms.id]=False
            else:
                res[ms.id]=False
        return res

    _columns = {
        'interning':fields.function(_interning,string='interning', type='boolean',readonly=True),
        'internships': fields.function(_get_internships, string='internships', type='one2many', relation="internship.request",readonly=True),
        'intern_status':fields.function(_status,fnct_search=_intern_status_search, string='intern status', type='selection',readonly=True,
                                 selection=[
                                     ('none','none'),
                                     ('new','new'),
                                     ('director_audit','director approval'),
                                     ('hr','HR approval'),
                                     ('meal_card','working card info'),
                                     ('accepted',u'实习中'),
                                     ('to_resign',u'离院审批'),
                                     ('manager_appr',u'工作卡退回'),
                                     ('diet_record','diet records upload'),
                                     ('director_appr',u'餐费审批'),
                                     ('checking_out','checking out'),
                                     ('resigned','resigned'),
                                     ('stoped','stoped'),
                                 ]),
        'intern_create_date':fields.function(_internCD, string='intern starting date', type='date',readonly=True),
    }

recruitment_interships()
