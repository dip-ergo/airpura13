# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Syncoria Inc. (<https://www.syncoria.com>)
#    You should have received a copy of the License along with this program.

#################################################################################

from ..lib.canpost_getRate import CanpostGetRate
from odoo import fields, models, api
from odoo.exceptions import Warning, ValidationError, UserError
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import dump
from xml.dom import minidom
from ..lib import canpost_contract_shipping as ccs
from ..lib import canpost_non_contract_shipping as ncs
from . import canpost_json_request
from .canpost_json_request import JsonRequestParatmeters as rp
import base64
import requests
import logging
import binascii
import re
_logger = logging.getLogger(__name__)


class CanpostDeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _compute_can_generate_return(self):
        for carrier in self:
            carrier.can_generate_return = True

    @staticmethod
    def pretify(element):
        rough_string = ElementTree.tostring(element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t")

    @api.model
    def __create_data(self, order, packaging_id, package):
        config = self.wk_get_carrier_settings(['canpost_test_username', 'canpost_test_password', 'canpost_production_username', 'canpost_production_password', 'prod_environment'])
        data = dict(
            environment=config['prod_environment'],
            dev_username=config['canpost_test_username'],
            dev_password=config['canpost_test_password'],
            prod_username=config['canpost_production_username'],
            prod_password=config['canpost_production_password']
        )
        rate_obj = CanpostGetRate(**data)
        mail_quote = dict(
            quote_type=self.canpost_quote_type
        )
        if self.canpost_quote_type == 'commercial':
            mail_quote['customer_number'] = self.canpost_customer_number
            mail_quote['contract_id'] = self.canpost_contract_id
            mail_quote['promo_code'] = self.canpost_promo_code
        mail_quote['origin_postal_code'] = order.warehouse_id.partner_id.zip.replace(' ','').replace('-','')
        rate_obj.add_mailQuote(**mail_quote)

        if self.canpost_option_type:
            for option_obj in self.canpost_option_type:
                if option_obj.code == 'COV':
                    continue
                elif option_obj.code == 'COD':
                    obj = rate_obj.Options(**{'option_code': option_obj.code, 'option_amount': str(order.amount_total)})
                    rate_obj.options.append(obj)
                    continue
                obj = rate_obj.Options(**{'option_code': option_obj.code})
                rate_obj.options.append(obj)
        rate_obj.parcel_characteristics = rate_obj.ParcelCharacteristics(**{'weight': str(package.get('weight')) or '1'})
        dimension = dict(
            length=str(package.get('length')) or '1',
            width=str(package.get('width')) or '1',
            height=str(package.get('height')) or '1'
        )
        rate_obj.parcel_characteristics.dimension = rate_obj.Dimensions(**dimension)
        rate_obj.services = rate_obj.Services(**{'service_code': self.canpost_service_type.code})
        if order.partner_id.country_id.name in 'Canada':
            rate_obj.domestic = rate_obj.Domestic(**{'postal_code': order.partner_id.zip.replace(' ','').replace('-','')})
        elif order.partner_id.country_id.name in 'United States':
            rate_obj.united_states = rate_obj.UnitedStates(**{'zip_code': order.partner_id.zip.replace(' ','').replace('-','')})
        else:
            rate_obj.international = rate_obj.International(**{'country_code': order.partner_id.country_id.code, 'postal_code': order.partner_id.zip.replace(' ','').replace('-','')})
        return rate_obj

    @api.model
    def __canpost_get_rate(self, order=None):
        recipient = order.partner_shipping_id if order.partner_shipping_id else order.partner_id
        currency_id = self.get_shipment_currency_id(order)                  # Method of Backbone Shipping
        try:
            currency_code = currency_id.name     #       Add try
            packaging_obj = self.env['product.packaging']
            result = 0.0
            if not currency_id:
                currency_id = order.currency_id
            self.wk_validate_data(order=order)                              # Method of Backbone Shipping
            package_items = self.wk_get_order_package(order=order)          # Method of Backbone Shipping
            items = self.wk_group_by('packaging_id', package_items)         # Method of Backbone Shipping
            for order_packaging_id, wk_packaging_ids in items:
                packaging_id = packaging_obj.browse(order_packaging_id)
                # Use here packaging_id in api
                # rate_request = self.__canpost_preprocessing(packaging_id, order=order)
                for wk_packaging_id in wk_packaging_ids:
                    weight = float(self._get_api_weight(wk_packaging_id.get('weight',None)))           # Method of backbone
                    package = dict(
                        weight=weight,
                        length=wk_packaging_id.get('length'),
                        width=wk_packaging_id.get('width'),
                        height=wk_packaging_id.get('height')
                    )
                rate_obj = self.__create_data(order, packaging_id, package)
                response = rate_obj.getRate()
                if response.get('price-quote'):
                    amount = float(response['price-quote']['price-details']['due'])
                else:
                    error_message = response['message']['description']
                    error_message_desc = re.findall("}.*{", error_message)
                    if error_message_desc:
                        error_message = error_message_desc[-1]
                        error_message = error_message[1:-1]
                    raise Exception(error_message)
                result += amount
                error = False
                success = False
            return dict(
                currency_id=currency_id,
                price=result,
                currency=currency_code,
                success=True)
        except Exception as e:
            return dict(
                error_message=e,
                success=False
            )

    @api.model
    def canada_post_rate_shipment(self, order):
        response = self.__canpost_get_rate(order)
        if not response.get('error_message'):
            response['error_message'] = None
        if not response.get('price'):
            response['price'] = 0
        if not response.get('warning_message'):
            response['warning_message'] = None
        if not response.get('success'):
            return response
        price = self.convert_shipment_price(response)                             # method of backone
        response['price'] = price
        return response


    # @api.one
    def canada_post_send_shipping(self,pickings):
        result = {'tracking_number': '','weight':'', 'attachments': []}
        quote_type = self.canpost_quote_type

        delivery_spec_data = {}
        try:
            config = self.wk_get_carrier_settings(['canpost_contract_id','canpost_method_of_payment','canpost_test_username','canpost_test_password','canpost_service_type','prod_environment','canpost_production_username','canpost_production_password','canpost_mailed_on_behalf_of','canpost_customer_number','canpost_quote_type'])

            if len(self.canpost_option_type) == 0:
                delivery_spec_data['Options'] = False

            if quote_type == "commercial":
                request_obj = ccs
            elif quote_type == "counter":
                request_obj = ncs

            obj = canpost_json_request.jsonAPIEndpoints(**config)

            endpoint_json_data = obj.get_JsonAPIEndpoints(pickings)
            shipment_json_data = obj.get_JsonShipment(pickings)
            delivery_specification_json_data = obj.get_JsonDeliverySpecification(pickings)
            sender_address_details_json_data = obj.get_JsonAddressDetails(pickings,request_for ='sender')
            destination_address_details_json_data = obj.get_JsonAddressDetails(pickings,request_for = 'destination')
            parcel_json_data = {}
            preferences_json_data = obj.get_JsonPreferences(pickings)
            settlementinfo_json_data = obj.get_JsonSettlementInfo(pickings)
            if quote_type == 'commercial':
                return_specification_json_data = obj.get_JsonReturnSpecification(pickings)

            if quote_type == 'commercial':
                APIEND = ccs.APIEndpoints(**endpoint_json_data).postEndpoint()
                POSTHEADERS = ccs.APIEndpoints(**endpoint_json_data).postHttpHeaders()
                GETHEADERS = ccs.APIEndpoints(**endpoint_json_data).getHttpHeaders()
            elif quote_type == "counter":
                APIEND = ncs.APIEndpoints(**endpoint_json_data).postEndpoint()
                POSTHEADERS = ncs.APIEndpoints(**endpoint_json_data).postHttpHeaders()
                GETHEADERS = ncs.APIEndpoints(**endpoint_json_data).getHttpHeaders()


            xml_element = request_obj.Shipment(**shipment_json_data).create_Shipment()
            xml_element = request_obj.DeliverySpecification(**delivery_specification_json_data).create_DeliverySpecification(xml_element,**delivery_spec_data)
            xml_element = request_obj.AddressDetails(**sender_address_details_json_data).create_AddressDetails(xml_element, with_in="delivery-spec",request_for ='sender')
            xml_element = request_obj.AddressDetails(**destination_address_details_json_data).create_AddressDetails(xml_element, with_in="delivery-spec",request_for = 'destination')
            packaging_ids = self.wk_group_by_packaging(pickings=pickings)
            total_package = 0
            for packaging_id, package_ids in packaging_ids.items():
                packaging_code = packaging_id.shipper_package_code
                total_package += len(package_ids)
                for package_id in package_ids:
                    parcel_json_data = obj.get_JsonParcelCharacterstics(package_id)
                    xml_element = request_obj.ParcelCharacterstics(**parcel_json_data).create_ParcelCharacterstics(xml_element)

            for option in self.canpost_option_type:
                data = {}
                data['option-code'] = option.code
                if option.code == "COD":
                    if not pickings.origin:
                        continue
                    else:
                        data['option-amount'] = str(self.env['sale.order'].search([('name','=',pickings.origin)]).amount_total)
                        data['option-qualifier-1'] = 'true'
                elif option.code == "COV":
                    data['option-amount'] = parcel_json_data['cover_amount']
                xml_element = request_obj.Options(**data).create_Options(xml_element)

            xml_element = request_obj.Preferences(**preferences_json_data).create_Preferences(xml_element)
            xml_element = request_obj.SettlementInfo(**settlementinfo_json_data).create_SettlementInfo(xml_element)


            if quote_type == 'commercial':
                xml_element = request_obj.ReturnSpecification(**return_specification_json_data).create_ReturnSpecification(xml_element)

                xml_element = request_obj.AddressDetails(**sender_address_details_json_data).create_AddressDetails(xml_element, with_in="return-spec",request_for = 'return-recipient')


            xml = self.pretify(xml_element)
            response = requests.post(headers=POSTHEADERS,url=APIEND,data=xml)
            response = CanpostGetRate.transform_data(response.content)
            if not response.get('shipment-id'):
                error_message = response['message']['description']
                error_message_desc = re.findall("}.*{", error_message)
                if error_message_desc:
                    error_message = error_message_desc[-1]
                    error_message = error_message[1:-1]
                raise Exception(error_message)
            label_link = response['links']['label']['href']

            #---------Changes made by Real Haque---------------
            #ReturnLabel not working for canada post even if True
            #Need to solve this
            if self.return_label_on_delivery == True:
                returnLabelLink = response['links']['returnLabel']['href']
                returnlabelresponse = requests.get(headers=GETHEADERS,url=returnLabelLink)
                pickings.canpost_returnlabel = self.env['ir.attachment'].create({
                    'datas': base64.b64encode(returnlabelresponse.content),
                    'name': self.get_return_label_prefix() + "-stock_picking_id-"+ str(pickings.id),
                    'res_model': 'stock.picking',
                })
            #---------|||||||||||||||||||||||||---------------
            result['tracking_number'] = response['tracking-pin']
            response = requests.get(headers=GETHEADERS,url=label_link)
            
            result['weight'] = parcel_json_data.get('weight')
            result['attachments'] = [('CANADA' + result['tracking_number'] + '.pdf',response.content)]



            return result
        except Exception as e:
            raise UserError(e)

    @api.model
    def canada_post_get_tracking_link(self, pickings):
        return 'https://www.canadapost.ca/trackweb/en#/resultList?searchFor=' + '%s' % pickings.carrier_tracking_ref

    @api.model
    def canada_post_cancel_shipment(self, pickings):
        raise Warning("Canada Post Does Not provide Cancellation service")


    @api.model
    def canada_post_get_return_label(self, pickings, tracking_number, origin_date):

        pickings.canpost_returnlabel.write({'res_id':pickings.id})

        pickings.message_post(
            body= "Return Label Generated. Attachment id: {}".format(pickings.canpost_returnlabel.id),
            subject="Return Label Generated",
            attachment_ids= [pickings.canpost_returnlabel.id]
        )
