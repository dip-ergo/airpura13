# -*- coding: utf-8 -*-
#################################################################################
##    Copyright (c) 2020 Syncoria Inc. (<https://www.syncoria.com/>)
#    You should have received a copy of the License along with this program.

#################################################################################
from collections import  Counter
from datetime import datetime, timedelta
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _
from odoo.exceptions import  ValidationError
import logging
_logger = logging.getLogger(__name__)
Delivery = [
    ('none','None'),
    ('fixed','Fixed'),
    ('base_on_rule','Base on Rule'),
    ('fedex','fedex'),
    ('ups','ups'),
    ('usps','USPS'),
    ('auspost','auspost'),

]
AmountOption=[
    ('fixed', 'Fixed Amount'),
    ('percentage', '%  of Product Price')
]



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    def manage_package_type(self):
        self.ensure_one()
        res = super(StockMoveLine,self).manage_package_type()
        if res and (type(res)==dict):
            delivery_type = self.picking_id.carrier_id.delivery_type not in ['base_on_rule', 'fixed']  and self.picking_id.carrier_id.delivery_type or 'none'
            context = res.get('context') and res.get('context').copy() or dict()
            ctx={
                'no_description':
                        not(delivery_type in ['fedex', 'dhl', 'ups', 'auspost', 'canada_post'] and delivery_type or False ),
                'no_cover_amount' :
                        not(delivery_type in ['fedex', 'dhl', 'ups', 'usps', 'auspost', 'canada_post'] and delivery_type or False ),
                'no_edt_document' :
                    not(delivery_type in ['fedex','ups'] and delivery_type or False ),
                'current_package_picking_id' :self.picking_id.id,
            }
            context.update(ctx)
            res['context']=context
            self.picking_id.wk_update_package(self.result_package_id)
        return res


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"


    height = fields.Integer(
        string='Height'
    )
    width = fields.Integer(
        string='Width'
    )
    length = fields.Integer(
        string='Length'
    )
    cover_amount = fields.Integer(
        string='Cover Amount',
        help='This is the declared value/cover amount for an individual package.'
    )
    description = fields.Text(
        string='Description',
        help='The text describing the package.'
    )
    order_id = fields.Many2one(
        comodel_name='sale.order'
    )
    _sql_constraints = [
        ('positive_cover_amount', 'CHECK(cover_amount>=0)', 'Cover Amount must be positive (cover_amount>=0).'),
         ('positive_shipping_weight', 'CHECK(shipping_weight>=0)', 'Shipment weight must be positive (shipping_weight>=0).'),

    ]


    @api.onchange('delivery_packaging_id', 'shipping_weight')
    def _onchange_packaging_weight(self):
        self.height = self.delivery_packaging_id.height
        self.width = self.delivery_packaging_id.width
        # self.length = self.delivery_packaging_id.length
        # Issue with length
        self.cover_amount = self.delivery_packaging_id.cover_amount
        _logger.info("===%r====%r====+%r====%r"%(self.height,self.width,self.length,self.cover_amount))
        if self.delivery_packaging_id.max_weight and self.shipping_weight > self.delivery_packaging_id.max_weight:
            warning_mess = {
            'title': _('Package too heavy!'),
            'message': _('The weight of your package is higher than the maximum weight authorized for this package type. Please choose another package type.')
            }
            return {'warning': warning_mess}

    @api.onchange('delivery_packaging_id')
    def onchange_delivery_packaging_id(self):
        print()
        packaging_id = self.delivery_packaging_id
        if packaging_id:
            value = dict(
                height = packaging_id.height,
                width = packaging_id.width,
                length = packaging_id.length,
                cover_amount = packaging_id.cover_amount,
        
            )
        #     _logger.info("===%r=="%(value))
        #     return {'value': value}

        if packaging_id:
            self.height = packaging_id.height
            self.width = packaging_id.width
            # self.length = packaging_id.length
            self.cover_amount=packaging_id.get_cover_amount(self.cover_amount)
            _logger.info("===%r====%r====+%r====%r"%(self.height,self.width,self.length,self.cover_amount))


    #------------------------------------------------------
    # @api.onchange('delivery_packaging_id')
    # def onchange_delivery_packaging_id(self):
    #     packaging_id = self.delivery_packaging_id
    #     if packaging_id:
    #         value = dict(
    #             height = packaging_id.height,
    #             width = packaging_id.width,
    #             length = packaging_id.length,
    #             cover_amount = packaging_id.cover_amount,
        
    #         )
    #     #     _logger.info("===%r=="%(value))
    #     #     return {'value': value}
    #     if packaging_id:
    #         self.write({
    #             'height':packaging_id.height,
    #             'width':packaging_id.width,
    #             'length':packaging_id.length,
    #             'cover_amount':packaging_id.get_cover_amount(self.cover_amount)
    #         })
    #         _logger.info("===%r====%r====+%r====%r"%(self.height,self.width,self.length,self.cover_amount))
    #         # return {'value': value}
    #         # return {
    #         #     'type': 'ir.actions.client',
    #         #     'tag': 'reload',
    #         # }
    #         response = {
    #             'type': 'ir.actions.window',
    #             'tag': 'reload',
    #             'height':packaging_id.height,
    #             'width': packaging_id.width,
    #             'length':packaging_id.length,
    #             'context':
    #                 {
    #                     'default_height': packaging_id.height,
    #                     'default_width': packaging_id.width,
    #                     'default_length': packaging_id.length,
    #                 }
    #         }
    #         return response

    @api.depends('delivery_packaging_id')
    def _compute_weight_uom_name(self):
        print("ODOO:SHIPPING_compute_weight_uom_name")
        packaging_id = self.delivery_packaging_id
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        for package in self:
            package.weight_uom_name = weight_uom_id.name
            package.height = packaging_id.height
            package.width = packaging_id.width
            package.length = packaging_id.length
            package.cover_amount=packaging_id.get_cover_amount(package.cover_amount)
            response = {
                'type': 'ir.actions.window',
                'tag': 'reload',
                'height':packaging_id.height,
                'width': packaging_id.width,
                'length':packaging_id.length,
                'context':
                    {
                        'default_height': packaging_id.height,
                        'default_width': packaging_id.width,
                        'default_length': packaging_id.length,
                    }
            }
            return response

    #-------------------------------------------------------------------
    def get_shipping_fields(self):
        return ['height', 'width', 'length', 'cover_amount', 'description']

    def update_shipping_package(self,stock_quant_package_id):
        data  = self.read(self.get_shipping_fields())[0]
        data.pop('id')
        stock_quant_package_id.write(data)
        return True

    def put_in_pack(self):
        packaging_id = self.delivery_packaging_id
        if packaging_id and  (packaging_id.package_carrier_type not in ['none']):
            if packaging_id and (packaging_id.max_weight < self.shipping_weight):
                msz = _('Shipment weight should be less then {max_weight} kg  as {max_weight} kg is the max weight limit set  for {name}  .'.format(max_weight=packaging_id.max_weight,name=packaging_id.name))
                _logger.info("Weight Check: %s  ",msz)
                raise ValidationError(msz)
        
        ctx = dict(self._context)        
        ctx['default_cover_amount'] = self.cover_amount
        ctx['default_shipping_weight'] = self.shipping_weight
        ctx['default_height'] = self.height
        ctx['default_width'] = self.width
        ctx['default_length'] = self.length
        super(ChooseDeliveryPackage,self.with_context(ctx)).put_in_pack()
        
        # packaging_id = self.delivery_packaging_id
        # if packaging_id and  (packaging_id.package_carrier_type not in ['none']):
            # if packaging_id and (packaging_id.max_weight < self.shipping_weight):
                # msz = _('Shipment weight should be less then {max_weight} kg  as {max_weight} kg is the max weight limit set  for {name}  .'.format(max_weight=packaging_id.max_weight,name=packaging_id.name))
                # _logger.info("Weight Check: %s  ",msz)
                # raise ValidationError(msz)
        # stock_quant_package_id = self.stock_quant_package_id
        # self.update_shipping_package(stock_quant_package_id)
        return None


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"
    package_carrier_type = fields.Selection(related='packaging_id.package_carrier_type')
    height = fields.Integer(string='Height')
    width = fields.Integer(string='Width')
    length = fields.Integer(string='Length')
    cover_amount = fields.Integer(string='Cover Amount', help='This is the declared value/cover amount for an individual package.')
    description = fields.Text(string='Description', help='The text describing the package.')

    order_id = fields.Many2one(comodel_name='sale.order')
    # # def get_shipping_fields()
    # @api.onchange('packaging_id')
    # def set_package_data(self):
    #     if self.packaging_id:
    #         if not self.height: self.height = self.packaging_id.height
    #         if not self.width: self.width = self.packaging_id.width
    #         if not self.length: self.length = self.packaging_id.length
    #         if not self.cover_amount: self.cover_amount = self.packaging_id.cover_amount
