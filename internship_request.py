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
    _inherit=["mail.thread",'wkf.auddit.osv']
    _name = 'internship.request'
    _dept_field ='preset_dept'
    _module_categ_name='internship request'
    _rec_name ='name'

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

    def _get_name(self, cr, uid, ids, name, arg, context=None):
        res ={}.fromkeys(ids,u'实习管理流程')
        return  res

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
                                     ('director_appr',u'餐费审批'),
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
        #'c_date': fields.date(string='create date',  required=True),
        'name':fields.function(_get_name,type='char'),
        'applier':fields.many2one('res.users',string="applier"),
        'hr_notes':fields.char('notes', max_length=1024),
        }

    _defaults={
        'state':'new',
        #'applier':lambda self,cr,uid,c:uid,
        #'c_date':fields.date.context_today,
    }

    def create(self, cr, uid, vals, context={}):
        """
        当一个实习生进入到草稿-已离院状态间，用户不能再创建新的实习申请记录
        """
        if vals.get('internship',False):
            ids = self.search(cr, 1, [('internship','=',vals.get('internship',-1)),('state','not in',('draft','stoped','resigned'))], context =context)
            if ids:
                raise osv.except_osv(_('Fobbidden!'),
                                     _('This intern has another request which is under audditting!.'))

        return super(internship_request,self).create(cr,uid,vals,context=context)

    def unlink(self, cr, uid, ids, context={}):
        """
        限制删除在跑的单据
        """
        for req in self.browse(cr,uid,ids,context=context):
            if uid!=1 and req.state not in ('draft','stoped'):
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
            # class usr(object):
            #     def __init__(self,mobile_phone=False):
            #         self.mobile_phone = mobile_phone
            # users = [usr(request.hotel_receptionist_tel),]
            if sms_obj:
                # sms_obj.send_sms_to_users(
                #     cr,
                #     uid,
                #     users,  # 接受用户    这里请使用 browse()方式得到的结果， 不要使用 id值
                #     u'实习管理流程', #发送信息的表名 这里其实是一个标示，名字可以中文，能说清这个信息是从哪里发出的就行，例如 ：实习生--张XX短信
                #     request.hotel_reception_message,  #短信正文
                #     'internship.request', #来自模块   如果是hr.member 发出，这里就填 hr.member
                #     ids[0], #来自ID
                #     context=context
                # )
                sid = sms_obj.create(cr, uid,
                                     {'to': request.hotel_receptionist_tel.replace(' ','').replace('-',''),  #手机号码，如果多个人用,隔开
                                      'content': request.hotel_reception_message, #短信内容
                                      'model': 'internship.request', # 相关模块
                                      'res_id': ids[0]}, #相关ID
                                     context=context)
        except Exception,ex:
            pass

    def _get_arg(self, cr, key, id, context={}):
        """
        从参数表internship_request_args获取信息
        :param cr:
        :param key:参数名
        :param id:self._name对象的实例id
        :param context:
        :return:
        """
        cr.execute("select value from internship_request_args where key = '%s'"%(key,))
        msg = cr.fetchall()
        msg_obj = self.pool.get('workflow.message')
        if msg and len(msg)>0:
            msg = msg[0][0]
            return msg_obj._compile_msg(cr, msg, self._name, id, context=context)
        return ''


    def submit(self, cr, uid, ids, context={}):
        #self.send_email(cr, uid, ids[0],sys_email='tommy.ywt@gmail.com',subject='sys email')
        for data in self.browse(cr, uid, ids, context):
            try:
                context.update({'mail_create_nosubscribe':True})#默认不给关注的人发消息
                #cm_ids = self.get_uids(cr, uid, data.id, 'up_internship.group_badge_card_manager', data, context=context)
                #group_clerk_uids = self.get_uids(cr, uid, data.id, 'up_internship.group_clerk', data, context=context)
                # self.send_BA_msg(cr, uid, data.id,
                #                  u'[实习管理流程]' + data.internship.name + '(state code:'+data.state + ')',
                #                  content='',
                #                  subject=u'系统消息[实习管理流程]'+data.internship.name +'实习申请',
                #                  context={})
                mailed_users= []
                msg_obj = self.pool.get('workflow.message')
                auditors = self.get_audditors(cr, data)
                msg=''
                #审批(大蚂蚁和短信）
                bill_type=u'实习' if data.state in ('new','director_audit','hr', 'meal_card','accepted') else u'离院'
                for au_id in auditors:
                    if au_id in mailed_users:
                        continue
                    mailed_users.append(au_id)
                    msg = msg_obj.get_message(cr,au_id, self._name, data.id, 'submit', context=context)
                    if not msg:
                        continue
                    #_logger.warn('[msg debug]sms msg:%s'% msg)
                    self.message_post(cr, uid, ids,
                                      body=msg or u'%s%s申请单已经提交至您，可能需要您审批或者查阅。'%(data.internship.name,bill_type),
                                      subject=u'[实习管理流程]'+data.internship.name  + bill_type +u'申请',
                                      subtype='mail.mt_comment', #一定要是这个,
                                      type='comment', #一定要是这个TYPE,
                                      context=context,
                                      user_ids=[au_id],  #user_id 列表,
                                      group_xml_ids='',# 形如 xx.xxxx,xxx.xxx  的形式,
                                      #以上两个二选一使用，全用也兼容
                                      is_send_ant=True,
                                      is_send_sms=True,
                                      is_send_sys=False,
                                      sms_body=''
                    )

                #审批（系统消息）
                if auditors and msg:
                    self.message_post(cr, uid, ids,
                                      body=msg or u'%s%s申请单已经提交至您，可能需要您审批或者查阅。'%(data.internship.name,bill_type),
                                      subject=u'[实习管理流程]'+data.internship.name  + bill_type +u'申请',
                                      subtype='mail.mt_comment', #一定要是这个,
                                      type='comment', #一定要是这个TYPE,
                                      context=context,
                                      user_ids=auditors,  #user_id 列表,
                                      group_xml_ids='',# 形如 xx.xxxx,xxx.xxx  的形式,
                                      #以上两个二选一使用，全用也兼容
                                      is_send_ant=False,
                                      is_send_sms=False,
                                      is_send_sys=True,
                                      sms_body=''
                    )
                    _logger.info('[internship.request] message_post with is_send_sys to True called!')

                #知会（大蚂蚁和短信）
                followers_msgs = msg_obj.get_followers_messages(cr, self._name, data.id, 'submit', context=context)
                msg = ''
                f_uids= []
                for line in followers_msgs:
                    if line and line.get('follower_uid',False):
                        msg = line.get('msg', False) or u'%s%s申请单已经提交。'%(data.internship.name,bill_type)
                        f_uids.append([line.get('follower_uid',False)])
                        self.message_post(cr, uid, ids,
                                          body= msg,
                                          subject=u'[实习管理流程]'+data.internship.name  + bill_type +u'申请',
                                          subtype='mail.mt_comment', #一定要是这个,
                                          type='comment', #一定要是这个TYPE,
                                          context=context,
                                          user_ids=[line.get('follower_uid',False)],  #user_id 列表,
                                          group_xml_ids='',# 形如 xx.xxxx,xxx.xxx  的形式,
                                          #以上两个二选一使用，全用也兼容
                                          is_send_ant=True,
                                          is_send_sms=True,
                                          is_send_sys=False,
                                          sms_body=''
                        )
                #知会（系统消息）
                if f_uids:
                    self.message_post(cr, uid, ids,
                                      body= msg,
                                      subject=u'[实习管理流程]'+data.internship.name + bill_type + u'申请',
                                      subtype='mail.mt_comment', #一定要是这个,
                                      type='comment', #一定要是这个TYPE,
                                      context=context,
                                      user_ids=[line.get('follower_uid',False)],  #user_id 列表,
                                      group_xml_ids='',# 形如 xx.xxxx,xxx.xxx  的形式,
                                      #以上两个二选一使用，全用也兼容
                                      is_send_ant=False,
                                      is_send_sms=False,
                                      is_send_sys=True,
                                      sms_body=''
                    )

                #特别补充
                #. 入院，所长批后，发短信给【工作卡管理员】和实习生
                if data.state == 'hr':
                    sms_obj = self.pool.get('sms.sms')
                    #实习生
                    msg = self._get_arg(cr, u'[实习管理流程]所长审批后知会实习生消息', data.id, context=context)
                    if not msg:
                        msg = u'深规院[%s]拟同意接受你的实习申请，请你按照申请的实习时间(%s)准时报到，并保持手机畅通。'
                        msg = msg%(data.preset_dept.name,data.start_date)
                    sid = sms_obj.create(cr, uid,
                                         {'to': data.internship.moblie.replace(' ','').replace('-',''),  #手机号码，如果多个人用,隔开
                                          'content': msg, #短信内容
                                          'model': 'internship.request', # 相关模块
                                          'res_id': data.id}, #相关ID
                                         context=context)
                    #工作卡管理员(up_internship.group_badge_card_manager)
                    cm_ids = self.get_uids(cr, uid, data.id, 'up_internship.group_badge_card_manager', data,context=context)
                    if cm_ids:
                        msg = self._get_arg(cr, u'[实习管理流程]所长审批后知会工作卡管理员消息', data.id, context=context)
                        if not msg:
                            msg = u'[%s]提出申请拟接收实习生%s(实习开始时间:%s)，请及时登录内网处理。'
                            msg = msg%(data.preset_dept.name,data.internship.name,data.start_date)
                        self.message_post(cr, uid, ids,
                                          body= msg,
                                          subject=u'[实习管理流程]'+data.internship.name +u'实习申请',
                                          subtype='mail.mt_comment', #一定要是这个,
                                          type='comment', #一定要是这个TYPE,
                                          context=context,
                                          user_ids=cm_ids,  #user_id 列表,
                                          group_xml_ids='',# 形如 xx.xxxx,xxx.xxx  的形式,
                                          #以上两个二选一使用，全用也兼容
                                          is_send_ant=True,
                                          is_send_sms=True,
                                          #is_send_sys=True,
                                          sms_body=''
                        )

                    #部门文员(up_internship.group_clerk)
                    group_clerk_uids = self.get_uids(cr, uid, data.id, 'up_internship.group_clerk', data,context=context)
                    if group_clerk_uids:
                        msg = self._get_arg(cr, u'[实习管理流程]所长审批后知会部门文员消息', data.id, context=context)
                        if not msg:
                            msg = u'实习生%s已通过审批进入本所，请及时与对方联系办理入院手续(实习开始时间:%s)。'
                            msg = msg%(data.internship.name,data.start_date)
                        self.message_post(cr, uid, ids,
                                          body= msg,
                                          subject=u'[实习管理流程]'+data.internship.name +u'实习申请',
                                          subtype='mail.mt_comment', #一定要是这个,
                                          type='comment', #一定要是这个TYPE,
                                          context=context,
                                          user_ids=group_clerk_uids,  #user_id 列表,
                                          group_xml_ids='',# 形如 xx.xxxx,xxx.xxx  的形式,
                                          #以上两个二选一使用，全用也兼容
                                          is_send_ant=True,
                                          is_send_sms=True,
                                          sms_body=''
                        )
                        #pass
                #实习生其他消息补充 2015/1/8
                #“离院审批”后提醒实习生“到办公室高斌处退回工作卡”
                #“餐费审批”后提醒实习生“到办公室马丽处办理离院退房手续”
                msg =''
                if data.state == 'manager_appr':
                    #实习生
                    msg = self._get_arg(cr, u'[实习管理流程]离院审批后知会实习生消息', data.id, context=context)
                    if not msg:
                        msg = u'请到办公室高斌处退回工作卡。'
                        #msg = msg%(data.preset_dept.name,)
                elif data.state == 'checking_out':
                    msg = self._get_arg(cr, u'[实习管理流程]餐费审批后知会实习生消息', data.id, context=context)
                    if not msg:
                        msg = u'请到办公室马丽处办理离院退房手续。'
                        #msg = msg%(data.preset_dept.name,)
                if msg:
                    sms_obj = self.pool.get('sms.sms')
                    sid = sms_obj.create(cr, uid,
                                         {'to': data.internship.moblie.replace(' ','').replace('-',''),  #手机号码，如果多个人用,隔开
                                          'content': msg, #短信内容
                                          'model': 'internship.request', # 相关模块
                                          'res_id': data.id}, #相关ID
                                         context=context)

            except Exception,ex:
                _logger.exception(u'upintership.request exception')
                pass

    def reject(self, cr, uid ,ids, context={}):
        for data in self.browse(cr, uid, ids, context):
            try:
                msg_obj = self.pool.get('workflow.message')
                auditors = self.get_audditors(cr, data)
                #审批
                for au_id in auditors:
                    msg = msg_obj.get_message(cr,au_id, self._name, data.id, 'reject', context=context)
                    self.message_post(cr, uid, ids,
                                      body=msg or u'%s实习申请单已经退回至您，可能需要您审批或者查阅。'%(data.internship.name,),
                                      subject=u'[实习管理流程]'+data.internship.name +u'实习申请',
                                      subtype='mail.mt_comment', #一定要是这个,
                                      type='comment', #一定要是这个TYPE,
                                      context=context,
                                      user_ids=[au_id],  #user_id 列表,
                                      group_xml_ids='',# 形如 xx.xxxx,xxx.xxx  的形式,
                                      #以上两个二选一使用，全用也兼容
                                      is_send_ant=True,
                                      is_send_sms=True,
                                      sms_body=''
                    )
                #知会
                followers_msgs = msg_obj.get_followers_messages(cr, self._name, data.id, 'reject', context=context)
                for line in followers_msgs:
                    if line and line.get('follower_uid',False):
                        msg = line.get('msg', False) or u'%s实习申请单已经提交。'%(data.internship.name,)
                        self.message_post(cr, uid, ids,
                                          body= msg,
                                          subject=u'[实习管理流程]'+data.internship.name +u'实习申请',
                                          subtype='mail.mt_comment', #一定要是这个,
                                          type='comment', #一定要是这个TYPE,
                                          context=context,
                                          user_ids=[line.get('follower_uid',False)],  #user_id 列表,
                                          group_xml_ids='',# 形如 xx.xxxx,xxx.xxx  的形式,
                                          #以上两个二选一使用，全用也兼容
                                          is_send_ant=True,
                                          is_send_sms=True,
                                          sms_body=''
                        )
            except Exception,ex:
                _logger.error(str(ex))
                pass

internship_request()

class internship_request_args(osv.osv):
    _name = 'internship.request.args'
    _columns={
        'key': fields.char('key',size=512),
        'value': fields.char('value',size=1024),
        }
internship_request_args()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
