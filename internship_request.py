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
from osv import osv, fields
from openerp.addons.workflow_china import workflow_func
from openerp.tools.translate import _
from openerp import tools
import hashlib
import itertools
import logging
import os
import re
_logger = logging.getLogger(__name__)
class internship_request(osv.osv):
    _name = 'internship.request'

    def _name_get_resname(self, cr, uid, ids, object, method, context):
        data = {}
        for attachment in self.browse(cr, uid, ids, context=context):
            model_object = attachment.res_model
            res_id = attachment.res_id
            if model_object and res_id:
                model_pool = self.pool.get(model_object)
                res = model_pool.name_get(cr,uid,[res_id],context)
                res_name = res and res[0][1] or False
                if res_name:
                    field = self._columns.get('res_name',False)
                    if field and len(res_name) > field.size:
                        res_name = res_name[:field.size-3] + '...'
                data[attachment.id] = res_name
            else:
                data[attachment.id] = False
        return data

    # 'data' field implementation
    def _full_path(self, cr, uid, location, path):
        # location = 'file:filestore'
        assert location.startswith('file:'), "Unhandled filestore location %s" % location
        location = location[5:]

        # sanitize location name and path
        location = re.sub('[.]','',location)
        location = location.strip('/\\')

        path = re.sub('[.]','',path)
        path = path.strip('/\\')
        return os.path.join(tools.config['root_path'], location, cr.dbname, path)

    def _file_read(self, cr, uid, location, fname, bin_size=False):
        full_path = self._full_path(cr, uid, location, fname)
        r = ''
        try:
            if bin_size:
                r = os.path.getsize(full_path)
            else:
                r = open(full_path,'rb').read().encode('base64')
        except IOError:
            _logger.error("_read_file reading %s",full_path)
        return r

    def _file_write(self, cr, uid, location, value):
        bin_value = value.decode('base64')
        fname = hashlib.sha1(bin_value).hexdigest()
        # scatter files across 1024 dirs
        # we use '/' in the db (even on windows)
        fname = fname[:3] + '/' + fname
        full_path = self._full_path(cr, uid, location, fname)
        try:
            dirname = os.path.dirname(full_path)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            open(full_path,'wb').write(bin_value)
        except IOError:
            _logger.error("_file_write writing %s",full_path)
        return fname

    def _file_delete(self, cr, uid, location, fname):
        count = self.search(cr, 1, [('diet_record_fname','=',fname)], count=True)
        if count <= 1:
            full_path = self._full_path(cr, uid, location, fname)
            try:
                os.unlink(full_path)
            except OSError:
                _logger.error("_file_delete could not unlink %s",full_path)
            except IOError:
                # Harmless and needed for race conditions
                _logger.error("_file_delete could not unlink %s",full_path)

    def _data_get(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        result = {}
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        bin_size = context.get('bin_size')
        for attach in self.browse(cr, uid, ids, context=context):
            if location and attach.diet_record_fname:
                result[attach.id] = self._file_read(cr, uid, location, attach.diet_record_fname, bin_size)
            else:
                result[attach.id] = attach.diet_record_db_datas
        return result

    def _data_set(self, cr, uid, id, name, value, arg, context=None):
        # We dont handle setting data to null
        if not value:
            return True
        if context is None:
            context = {}
        location = self.pool.get('ir.config_parameter').get_param(cr, uid, 'ir_attachment.location')
        file_size = len(value.decode('base64'))
        if location:
            attach = self.browse(cr, uid, id, context=context)
            if attach.diet_record_fname:
                self._file_delete(cr, uid, location, attach.diet_record_fname)
            fname = self._file_write(cr, uid, location, value)
            super(internship_request, self).write(cr, uid, [id], {'diet_record_fname': fname, 'diet_record_file_size': file_size}, context=context)
        else:
            super(internship_request, self).write(cr, uid, [id], {'diet_record_db_datas': value, 'diet_record_file_size': file_size}, context=context)
        return True

    _columns = {
        'state':fields.selection([
                                     ('new','new'),
                                     ('director_audit','director approval'),
                                     ('hr','HR approval'),
                                     ('meal_card','working card info'),
                                     ('accepted',u'实习中'),
                                     ('to_resign',u'离院审批'),
                                     ('manager_appr',u'工作卡退回'),
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
        #'hotel_receptionist': fields.char(size=64, string='hotel receptionist ', required=False, help="hotel receptionist "),
        'hotel_receptionist': fields.many2one('internship.hotel.receptionist', string='hotel receptionist ', required=False, help="hotel receptionist "),
        'hotel_receptionist_tel': fields.char('receptionist phone',size=32),
        'hotel_reception_message': fields.char('reception message',size=256),
        'arrival_notice': fields.binary(string='arrival notice',  required=False),
        'meal_card_no': fields.char(size=32, string='working card no.', required=False, help="meal card number"),
        'meal_card_memo': fields.char(size=256, string='working card memo.', required=False, help="meal card memo"),
        'meal_card_status': fields.selection([('dispatched','dispatched'),('reserved','reserved'),('returned','returned')], string='working card status',  required=False),
        'pledge_money_state': fields.selection([('payed','payed'),('returned','returned'),('unpayed','unpayed')], string='pledge money state',  required=False),
        'hotel_checkout_date': fields.date(string='hotel checkout date',  required=False),
        'hotel_checkout_hour': fields.selection([('2','2:00 PM'),('6','6:00 PM')],string='hotel checkout hour',  required=False),
        'resignation_date': fields.date(string='resignation date',  required=False),
        'diet_record_needed':fields.selection([('yes','yes'),('no','no')],string='diet records required'),
        'diet_record': fields.function(_data_get, fnct_inv=_data_set, string='diet record', type="binary", nodrop=True),
        'diet_record_name': fields.char('File Name',size=256),
        'diet_record_fname': fields.char('Stored Filename', size=256),
        'diet_record_db_datas': fields.binary('Database Data'),
        'diet_record_file_size': fields.integer('File Size'),
        'internship': fields.many2one('hr.member', string='internship',  required=True),
        'audditing_logs':fields.function(workflow_func._get_workflow_logs, string='auditting logs', type='one2many', relation="workflow.logs",readonly=True),
        'c_date': fields.date(string='create date',  required=True),
        }

    _defaults={
        'state':'new',
        'c_date':fields.date.context_today,
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

    def onchange_hotel_receptionist(self, cr, uid, ids,receptionist_id, context={}):
        if not receptionist_id:
            return {}
        re = self.pool.get('internship.hotel.receptionist').browse(cr, uid, receptionist_id, context)
        return {'value':{
            'hotel_receptionist_tel':re.phone or '',
            'hotel_reception_message':re.msg or '',
        }}

    def onchange_internship(self, cr, uid, ids, internship_id, context={}):
        if not internship_id:
            return {}
        mem = self.pool.get('hr.member').browse(cr,uid,internship_id,context )
        return {'value':{'start_date':mem.start_date,'end_date':mem.end_date}}

    def notify_receptionist(self, cr, uid, ids, context={}):
        try:
            request  = self.browse(cr, uid, ids[0], context)
            sms_obj = self.pool.get('sms.sms')
            class usr(object):
                def __init__(self,mobile_phone=False):
                    self.mobile_phone = mobile_phone
            users = [usr(request.hotel_receptionist_tel),]
            if sms_obj:
                sms_obj.send_sms_to_users(
                    cr,
                    uid,
                    users,  # 接受用户    这里请使用 browse()方式得到的结果， 不要使用 id值
                    u'实习管理流程', #发送信息的表名 这里其实是一个标示，名字可以中文，能说清这个信息是从哪里发出的就行，例如 ：实习生--张XX短信
                    request.hotel_reception_message,  #短信正文
                    'internship.request', #来自模块   如果是hr.member 发出，这里就填 hr.member
                    ids[0], #来自ID
                    context=context
                )
        except Exception,ex:
            pass


internship_request()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
