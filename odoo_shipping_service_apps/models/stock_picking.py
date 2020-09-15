# -*- coding: utf-8 -*-
#################################################################################
# Copyright (c) 2020 Syncoria Inc. (<https://www.syncoria.com/>)
#    You should have received a copy of the License along with this program.

#################################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def get_picking_price(self, package_id):
        move_line_ids = self.env['stock.move.line'].search(
            [('result_package_id', '=', package_id.id)])
        return sum([x.qty_done * x.product_id.list_price for x in move_line_ids])

    @api.model
    def wk_update_package(self, package_id=None):
        if self.carrier_id.delivery_type not in ['base_on_rule', 'fixed']:
            packaging_id = package_id.packaging_id
            if package_id and (not packaging_id):
                packaging_id = self.carrier_id.packaging_id
                package_id.packaging_id = packaging_id.id
            amount = self.get_picking_price(package_id)
            package_id.cover_amount = packaging_id.get_cover_amount(amount)
        return True

    def put_in_pack(self):
        self.ensure_one()
        cover=0
        carrier_id = self.carrier_id
        move_line_ids = [po for po in self.move_line_ids if po.qty_done > 0 and not po.result_package_id]
        total_weight = sum([po.qty_done * po.product_id.weight for po in move_line_ids])
        if carrier_id.packaging_id.cover_amount_option == 'fixed':
            cover = self.carrier_id.packaging_id.cover_amount
        else:
            cover_amount = sum([po.qty_done * po.product_id.lst_price for po in move_line_ids])
            cover = cover_amount
        
        if total_weight == 0 :
            shipping_weight = self.carrier_id.default_product_weight
        else:
            shipping_weight = total_weight
        if self.sale_id.carrier_id:
            package = False
            for pack in self.product_id.wk_packaging_ids:
                if pack.package_carrier_type == self.sale_id.carrier_id.delivery_type:
                    package = pack
        if package == False and len(self.product_id.wk_packaging_ids) > 0:
            package = self.product_id.wk_packaging_ids[0]

        res = super(StockPicking, self).put_in_pack()
        shipping_weight = self.product_id.weight
        
        if package != False:
            shipping_weight = package.max_weight
        
        if res:
            if package != False and type(res) != dict:
                res.write({
                    'packaging_id':package.id,
                    'length':package.length,
                    'width':package.width,
                    'height':package.height,
                    'shipping_weight':shipping_weight,
                    'cover_amount':cover,
                })

        if res and (type(res) == dict):
            context = res.get('context') and res.get(
                'context').copy() or dict()
            delivery_type = context.get('current_package_carrier_type')
            ctx = {
                'no_description':
                not(delivery_type in ['fedex', 'dhl', 'ups', 'auspost', 'canada_post','purolator']),
                'no_cover_amount':
                    not(delivery_type in [
                        'fedex', 'dhl', 'ups', 'usps', 'auspost', 'canada_post','purolator']),
                'no_edt_document':
                    not(delivery_type in ['fedex', 'ups']),
                'current_package_picking_id': self.id,
            }
            
            if carrier_id and carrier_id.delivery_type not in ['base_on_rule', 'fixed']:
                ctx['default_delivery_packaging_id'] = self.carrier_id.packaging_id.id
                ctx['default_height'] = self.carrier_id.packaging_id.height
                ctx['default_width'] = self.carrier_id.packaging_id.width
                ctx['default_length'] = self.carrier_id.packaging_id.length
                ctx['default_cover_amount'] = cover
                ctx['default_shipping_weight'] = shipping_weight
                if package:
                    ctx['default_delivery_packaging_id'] = package.id
                    ctx['default_height'] = package.height
                    ctx['default_width'] = package.width
                    ctx['default_length'] = package.length
                    ctx['default_cover_amount'] = package.cover_amount#cover*(package.cover_amount/100)
            context.update(ctx)
            res['context'] = context
        return res

    @api.depends('package_ids')
    def _compute_cover_amount(self):
        for obj in self:
            obj.cover_amount = sum(obj.package_ids.mapped('cover_amount'))

    label_genrated = fields.Boolean(string='Label Generated', copy=False)
    shipment_uom_id = fields.Many2one(related='carrier_id.uom_id', readonly="1",
                                      help="Unit of measurement for use by Delivery method", copy=False)

    date_delivery = fields.Date(string='Expected Date Of Delivery',
                                help='Expected Date Of Delivery :The delivery time stamp provided by Shipment Service', copy=False, readonly=1)
    weight_shipment = fields.Float(
        string='Send Weight', copy=False, readonly=1)
    cover_amount = fields.Float(
        string='Cover Amount',
        compute='_compute_cover_amount',
        copy=False, readonly=1)

    def action_cancel(self):
        for obj in self:
            if obj.label_genrated == True:
                raise ValidationError(
                    'Please cancel the shipment before canceling  picking! ')
        return super(StockPicking, self).action_cancel()

    def do_new_transfer(self):
        for pick in self:
            carrier_id = pick.carrier_id
            if carrier_id and (carrier_id.delivery_type not in ['base_on_rule', 'fixed']):
                if not len(pick.package_ids):
                    raise ValidationError(
                        'Create the package first for picking %s before sending to shipper.' % (pick.name))
        return super(StockPicking, self).do_new_transfer()

    def send_to_shipper(self):
        if not self.carrier_id.delivery_type == 'purolator':
            self.ensure_one()
            if self.carrier_id.delivery_type and (self.carrier_id.delivery_type not in ['base_on_rule', 'fixed']):
                if not len(self.package_ids):
                    raise ValidationError(
                        'Create the package first for picking %s before sending to shipper.' % (self.name))
                else:
                    # try:
                    res = self.carrier_id.send_shipping(self)
                    self.carrier_price = res.get('exact_price')
                    self.carrier_tracking_ref = res.get(
                        'tracking_number') and res.get('tracking_number').strip(',')
                    self.label_genrated = True
                    self.date_delivery = res.get('date_delivery')
                    self.weight_shipment = float(res.get('weight'))
                    msg = _("Shipment sent to carrier %s for expedition with tracking number %s") % (
                        self.carrier_id.delivery_type, self.carrier_tracking_ref)
                    self.message_post(
                        body=msg,
                        subject="Attachments of tracking",
                        attachments=res.get('attachments')
                    )
                    # except Exception as e:
                    #     return self.carrier_id._shipping_genrated_message(e)

                    # if self.carrier_tracking_ref:
                    #     try:
                    #         for tracking_no in self.carrier_tracking_ref.split(","):
                    #             data = {
                    #                 "track_number": tracking_no,
                    #                 "title": "Canada Post",
                    #                 "carrier_code": "Custom Value"
                    #                 }
                    #             self.sale_id.magento_update_track(data)
                    #     except Exception as e:
                    #         _logger.info(str(e.args))

        elif self.carrier_id.delivery_type == 'purolator':
            self.ensure_one()
            res = self.carrier_id.send_shipping(self)[0]
            self._add_delivery_cost_to_so()
            # if self.carrier_id.free_over and self.sale_id and self.sale_id._compute_amount_total_without_delivery() >= self.carrier_id.amount:
            #     res['exact_price'] = 0.0
            # self.carrier_price = res['exact_price'] * (1.0 + (self.carrier_id.margin / 100.0))
            # if res['tracking_number']:
            #     self.carrier_tracking_ref = res['tracking_number']
            # order_currency = self.sale_id.currency_id or self.company_id.currency_id
            # msg = _("Shipment sent to carrier %s for shipping with tracking number %s<br/>Cost: %.2f %s") % (self.carrier_id.name, self.carrier_tracking_ref, self.carrier_price, order_currency.name)
            # self.message_post(body=msg)
            # self._add_delivery_cost_to_so()

    @api.model
    def unset_fields_prev(self):
        self.carrier_tracking_ref = False
        self.carrier_price = False
        self.label_genrated = False
        self.date_delivery = False
        self.weight_shipment = False
        self.number_of_packages = False
        return True

    def cancel_shipment(self):
        self.ensure_one()
        # try:
        if self.carrier_id.void_shipment:
            self.carrier_id.cancel_shipment(self)
            msg = "Shipment of  %s  has been canceled" % self.carrier_tracking_ref
            self.message_post(body=msg)
            self.unset_fields_prev()

        else:
            msg = 'Void Shipment not allowed, please contact your Admin to enable the  Void Shipment for %s.' % (
                self.carrier_id.name)
            self.message_post(
                body=msg, subject="Not allowed to Void the Shipment.")
            return self.carrier_id._shipping_genrated_message(msg)
        # except Exception as e:
        #     return self.carrier_id._shipping_genrated_message(e)
