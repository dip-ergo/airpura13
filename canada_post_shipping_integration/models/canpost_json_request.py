# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Syncoria Inc. (<https://www.syncoria.com>)
#    You should have received a copy of the License along with this program.

#################################################################################

from odoo.exceptions import Warning, ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)


class JsonRequestParatmeters():
    try:
        def __init__(self,*args,**kwargs):
            self.canadapost_user_name = kwargs.get('user_name')
            self.canadapost_password = kwargs.get('password')
            self.canadapost_customer_number = kwargs.get('customer_id')
            self.canadapost_request_for = kwargs.get('request_for')
            self.canadapost_mobo = kwargs.get('mobo')
            self.canadapost_quote_type = kwargs.get('quote_type')

        def get_JsonAPIEndpoints(self,pickings,**kwargs):
            if self.canadapost_quote_type == "commercial":
                return {
                'userid':self.canadapost_user_name,
                'password':self.canadapost_password,
                'request_for':self.canadapost_request_for,
                'customer_number':self.canadapost_customer_number,
                'mobo':self.canadapost_mobo,
                }

            elif self.canadapost_quote_type == "counter":
                return {
                'userid':self.canadapost_user_name,
                'password':self.canadapost_password,
                'request_for':self.canadapost_request_for,
                'customer_number':self.canadapost_customer_number,
                }

            else:
                raise UserError("Quote Type must be 'commercial' or 'counter'")

        def get_JsonShipment(self,pickings,**kwargs):

            recipient_data =  pickings.carrier_id.get_shipment_recipient_address(picking=pickings)

            if self.canadapost_quote_type == "commercial":
                return {
                        'requested-shipping-point' : recipient_data.get('zip'),
                        'transmit-shipment' : 'true',
                }
            elif self.canadapost_quote_type == "counter":
                return {
                        'requested-shipping-point' : recipient_data.get('zip'),
                }
            else:
                raise UserError("Quote Type must be 'commercial' or 'counter'")

        def get_JsonDeliverySpecification(self,pickings,**kwargs):

            return {
                'service-code': pickings.carrier_id.canpost_service_type.code
            }

        def get_JsonAddressDetails(self,pickings,**kwargs):

            if kwargs.get('request_for') == 'sender':
                data =pickings.carrier_id.get_shipment_shipper_address(picking=pickings)
                data['company_name'] = pickings.company_id.name
            elif kwargs.get('request_for') == 'destination':
                data = pickings.carrier_id.get_shipment_recipient_address(picking=pickings)
            else:
                raise UserError("request_for should be 'sender' or 'destination'")
            

            return{
                    'name':data.get('name'),
                    'company':data.get('company_name'),
                    'contact-phone':data.get('phone'),
                    'address-line-1':data.get('street'),
                    'address-line-2' :data.get('street2'),
                    'city':data.get('city'),
                    'prov-state':data.get('state_code'),
                    'country-code':data.get('country_code'),
                    'postal-zip-code':data.get('zip'),
            }

        def get_JsonParcelCharacterstics(self,package_id,**kwargs):
            package_data = {}
            pck_data = package_id.read(
                ['description', 'name', 'shipping_weight', 'cover_amount'])
            pkg_data = package_id.read(['height', 'width', 'length'])
            package_data.update(pck_data[0])
            package_data.update(pkg_data[0])
            return{
                'weight': str(package_data.get('shipping_weight')),
                'length': str(package_data.get('length')),
                'width': str(package_data.get('width')),
                'height': str(package_data.get('height')),
                'cover_amount': str(package_data.get('cover_amount'))
            }

        def get_JsonPreferences(self,pickings,**kwargs):
            return{
                'show-packing-instructions':'true',
                'show-postage-rate':'true',
                'show-insured-value':'false',
            }

        def get_JsonSettlementInfo(self,pickings,**kwargs):
            if self.canadapost_quote_type == "commercial":
                return {
                    "contract-id" : pickings.carrier_id.canpost_contract_id,
                    'intended-method-of-payment': pickings.carrier_id.canpost_method_of_payment.name,
                    'promo_code':pickings.carrier_id.canpost_promo_code
                }
            elif self.canadapost_quote_type == "counter":
                return {
                    'promo_code':pickings.carrier_id.canpost_promo_code,
                }
            else:
                raise UserError("Quote Type must be 'commercial' or 'counter'")

        def get_JsonReturnSpecification(self,pickings,**kwargs):

            data =pickings.carrier_id.get_shipment_shipper_address(picking=pickings)

            return {
            'service_code': pickings.carrier_id.canpost_service_type.code,
            'return_notification': data.get('email')
        }        

    except Exception as e:
        raise UserError(e)

def jsonAPIEndpoints(**config):
    try:
        if config.get('prod_environment'):
            obj = JsonRequestParatmeters(**{
                'user_name':config.get('canpost_production_username'),
                'password':config.get('canpost_production_password'),
                'customer_id':config.get('canpost_customer_number'),
                'request_for':'Production',
                'mobo':config.get('canpost_mailed_on_behalf_of'),
                'quote_type':config.get('canpost_quote_type'),
                })

        else:
            obj = JsonRequestParatmeters(**{
                'user_name':config.get('canpost_test_username'),
                'password':config.get('canpost_test_password'),
                'customer_id':config.get('canpost_customer_number'),
                'request_for':'Development',
                'mobo':config.get('canpost_mailed_on_behalf_of'),
                'quote_type':config.get('canpost_quote_type'),
                })

        return obj
        
    except Exception as e:
        raise UserError(e)