# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Syncoria Inc. (<https://www.syncoria.com>)
#    You should have received a copy of the License along with this program.

#################################################################################

import requests
import base64
import xml.etree.ElementTree as etree
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import dump
from xml.dom import minidom

class APIEndpoints():

    def __init__(self,**kwargs):
        self.userid = kwargs.get('userid')
        self.password = kwargs.get('password')
        self.request_for = kwargs.get('request_for')
        self.customer_number = kwargs.get('customer_number')
        self.mobo = kwargs.get('mobo')

    def postEndpoint(self):
        APIEND = dict(
            Development = "ct.soa-gw.canadapost.ca",
            Production = "soa-gw.canadapost.ca"
        )
        request_for = self.request_for
        customer_number = self.customer_number
        mobo = self.mobo

        return "https://{}/rs/{}/{}/shipment".format(APIEND.get(
            'Development' if request_for == 'Development' else 'Production'
        ),customer_number,mobo)

    def postHttpHeaders(self):
        return {
            'Accept': 'application/vnd.cpc.shipment-v8+xml',
            'Content-Type': 'application/vnd.cpc.shipment-v8+xml',
            'Authorization': 'Basic {}'.format(base64.b64encode("{}:{}".format(self.userid, self.password).encode("utf-8")).decode('utf-8')),
            'Accept-language': 'en-CA',
        }
    def getHttpHeaders(self):
        return {
            'Accept': 'application/pdf',
            'Authorization': 'Basic {}'.format(base64.b64encode("{}:{}".format(self.userid, self.password).encode("utf-8")).decode('utf-8')),
            'Accept-language': 'en-CA',
        }

class SettlementInfo():
    def __init__(self,**kwargs):
        self.contract_id = kwargs.get('contract-id')
        self.mop = kwargs.get('intended-method-of-payment')
        self.promo_code = kwargs.get('promo_code')

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element

    def create_SettlementInfo(self,root,**kwargs):
        settlement = root.find('delivery-spec/settlement-info')
        if type(settlement) == Element:
            self.contract_id and self.add_text(SubElement(settlement,'contract-id'),self.contract_id)
            self.mop and self.add_text(SubElement(settlement,'intended-method-of-payment'),self.mop)
            self.promo_code and self.add_text(SubElement(settlement,'promo-code'),self.promo_code)
        return root

class Preferences():
    def __init__(self,**kwargs):
        self.show_packing_instructions = kwargs.get('show-packing-instructions')
        self.show_postage_rate = kwargs.get('show-postage-rate')
        self.show_insured_value = kwargs.get('show-insured-value')

    @staticmethod
    def add_text(element, text):
        element.text = str(text)
        return element

    def create_Preferences(self,root,**kwargs):
        preference = root.find('delivery-spec/preferences')
        if type(preference) == Element:
            self.show_packing_instructions and self.add_text(SubElement(preference,'show-packing-instructions'),self.show_packing_instructions)
            self.show_postage_rate and self.add_text(SubElement(preference,'show-postage-rate'),self.show_postage_rate)
            self.show_insured_value and self.add_text(SubElement(preference,'show-insured-value'),self.show_insured_value)
        return root

class PrintPreferences():
    def __init__(self,**kwargs):
        self.output_format = kwargs.get('output-format')
        self.encoding = kwargs.get('encoding')

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element

    def create_PrintPreferences(self,root,**kwargs):
        preference = root.find('delivery-spec/print-preferences')
        if type(preference) == Element:
            self.output_format and self.add_text(SubElement(preference,'output-format'),self.output_format)
            self.encoding and self.add_text(SubElement(preference,'encoding'),self.encoding)
        return root

class Notifications():
    def __init__(self,**kwargs):
        self.email = kwargs.get('email')
        self.on_shipment = kwargs.get('on-shipment')
        self.on_exception = kwargs.get('on-exception')
        self.on_delivery = kwargs.get('on-delivery')

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element

    def create_Notifications(self,root,**kwargs):
        notification = root.find('delivery-spec/notification')
        if type(notification) == Element:
            self.email and self.add_text(SubElement(notification,'email'),self.email)
            self.on_shipment and self.add_text(SubElement(notification,'on-shipment'),self.on_shipment)
            self.on_exception and self.add_text(SubElement(notification,'on-exception'),self.on_exception)
            self.on_delivery and self.add_text(SubElement(notification,'on-delivery'),self.on_delivery)
        return root

class ParcelCharacterstics():
    def __init__(self,**kwargs):
        self.weight = kwargs.get('weight')
        self.length = kwargs.get('length')
        self.width = kwargs.get('width')
        self.height = kwargs.get('height')
        self.unpackaged = kwargs.get('unpackaged')
        self.mailing_tube = kwargs.get('mailing-tube')
        self.oversized = kwargs.get('oversized')

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element

    def create_ParcelCharacterstics(self,root,**kwargs):
        parcel = root.find('delivery-spec/parcel-characteristics')
        if type(parcel) == Element:
            self.weight and self.add_text(SubElement(parcel,'weight'),self.weight)
            dimensions = SubElement(parcel,'dimensions')
            if type(dimensions) == Element:
                self.height and self.add_text(SubElement(dimensions,'length'),self.length)
                self.width and self.add_text(SubElement(dimensions,'width'),self.width)
                self.height and self.add_text(SubElement(dimensions,'height'),self.height)
                self.unpackaged and self.add_text(SubElement(parcel,'unpackaged'),self.unpackaged)
                self.mailing_tube and self.add_text(SubElement(parcel,'mailing-tube'),self.mailing_tube)
                self.oversized and self.add_text(SubElement(parcel,'oversized'),self.oversized)
        return root

class Options():
    def __init__(self,**kwargs):
        self.option_code = kwargs.get('option-code')
        self.option_amount = kwargs.get('option-amount')
        self.option_qualifier_1 = kwargs.get('option-qualifier-1')
        self.option_qualifier_2 = kwargs.get('option-qualifier-2')

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element

    def create_Options(self,root,**kwargs):
        options = root.find('delivery-spec/options')
        if type(options) == Element:
            option = SubElement(options,'option')
            if type(option) == Element:
                if self.option_code:
                    self.add_text(SubElement(option,'option-code'),self.option_code)
                if self.option_amount:
                    self.add_text(SubElement(option,'option-amount'),self.option_amount)
                if self.option_qualifier_1:
                    self.add_text(SubElement(option,'option-qualifier-1'),self.option_qualifier_1)
                if self.option_qualifier_2:
                    self.add_text(SubElement(option,'option-qualifier-2'),self.option_qualifier_2)
        return root

class AddressDetails():

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element

    def __init__(self,**kwargs):
        self.name = kwargs.get('name')
        self.company = kwargs.get('company')
        self.contact_phone = kwargs.get('contact-phone')
        self.address_line_1 = kwargs.get('address-line-1')
        self.address_line_2 = kwargs.get('address-line-2')
        self.city = kwargs.get('city')
        self.prov_state = kwargs.get('prov-state')
        self.country_code = kwargs.get('country-code')
        self.postal_zip_code = kwargs.get('postal-zip-code')

    def create_AddressDetails(self,root,**kwargs):
        addr = root.find('{}/{}'.format(kwargs.get('with_in'),kwargs.get('request_for')))
        if type(addr) == Element:
            self.name and self.add_text(SubElement(addr,'name'),self.name)
            self.company and self.add_text(SubElement(addr,'company'),self.company)
            if kwargs.get('request_for') == 'sender':
                self.contact_phone and self.add_text(SubElement(addr,'contact-phone'),self.contact_phone)
            address_details = SubElement(addr,'address-details')
            if type(address_details) == Element:
                self.address_line_1 and self.add_text(SubElement(address_details,'address-line-1'),self.address_line_1)
                self.address_line_2 and self.add_text(SubElement(address_details,'address-line-2'),self.address_line_2)
                self.city and self.add_text(SubElement(address_details,'city'),self.city)
                self.prov_state and self.add_text(SubElement(address_details,'prov-state'),self.prov_state)
                if not kwargs.get('request_for') == 'return-recipient':
                    self.country_code and self.add_text(SubElement(address_details,'country-code'),self.country_code)
                self.postal_zip_code and self.add_text(SubElement(address_details,'postal-zip-code'),self.postal_zip_code)
        return root

class DeliverySpecification():

    def __init__(self,**kwargs):
        self.service_code = kwargs.get('service-code')

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element


    def create_DeliverySpecification(self,root,**kwargs):
        delivery_spec = root.find('delivery-spec')
        if type(delivery_spec) == Element:
            if self.service_code:
                self.add_text(SubElement(delivery_spec,'service-code'),self.service_code)            #required
            SubElement(delivery_spec,'sender')                                                   #required
            SubElement(delivery_spec,'destination')
            if kwargs.get('Options', True):                                              #required
                SubElement(delivery_spec,'options')                                         #optional
            SubElement(delivery_spec,'parcel-characteristics')                                   #required
            # SubElement(delivery_spec,'notification')                                             #conditionally required
            # SubElement(delivery_spec,'print-preferences')                                        #optional
            SubElement(delivery_spec,'preferences')                                              #required
            SubElement(delivery_spec,'settlement-info')                                          #required
        return root

class ReturnSpecification():
    def __init__(self,**kwargs):
        self.service_code = kwargs.get('service_code')
        self.return_notification = kwargs.get('return_notification')

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element

    def create_ReturnSpecification(self,root,**kwargs):
        return_spec = root.find('return-spec')
        if type(return_spec) == Element:
            self.service_code and self.add_text(SubElement(return_spec,'service-code'),self.service_code)
            SubElement(return_spec,'return-recipient')
            self.return_notification and self.add_text(SubElement(return_spec,'return-notification'),self.return_notification)
        return root

class Shipment():

    def __init__(self,**kwargs):
        self.customer_request_id = kwargs.get('customer-request-id')
        self.group_id = kwargs.get('group-id')
        self.transmit_shipment = kwargs.get('transmit-shipment')
        self.quickship_label_requested = kwargs.get('quickship-label-requested')
        self.requested_shipping_point = kwargs.get('requested-shipping-point')
        self.cpc_pickup_indicator = kwargs.get('cpc-pickup-indicator')
        self.shipping_point_id = kwargs.get('shipping-point-id')
        self.expected_mailing_date = kwargs.get('expected-mailing-date')
        self.provide_pricing_info = kwargs.get('provide-pricing-info')
        self.provide_receipt_info = kwargs.get('provide-receipt-info')

    @staticmethod
    def add_text(element, text):
        element.text = text
        return element


    def create_Shipment(self,**kwargs):
        root = Element('shipment', attrib={'xmlns':'http://www.canadapost.ca/ws/shipment-v8'})
        if type(root) == Element:
            if self.customer_request_id:
                self.add_text(SubElement(root,'customer-request-id'),self.customer_request_id)                   #optional
            if self.group_id:
                self.add_text(SubElement(root,'group-id'),self.group_id)                                         #conditionally required
            if self.transmit_shipment:
                self.add_text(SubElement(root,'transmit-shipment'),self.transmit_shipment)                       #conditionally required
            if self.quickship_label_requested:
                self.add_text(SubElement(root,'quickship-label-requested'),self.quickship_label_requested)       #optional
            if self.requested_shipping_point:
                self.add_text(SubElement(root,'requested-shipping-point'),self.requested_shipping_point)         #conditionally required
            if self.cpc_pickup_indicator:
                self.add_text(SubElement(root,'cpc-pickup-indicator'),self.cpc_pickup_indicator)                 #optional
            if self.shipping_point_id:
                self.add_text(SubElement(root,'shipping-point-id'),self.shipping_point_id)                       #conditionally required
            if self.expected_mailing_date:
                self.add_text(SubElement(root,'expected-mailing-date'),self.expected_mailing_date)               #optional
            if self.provide_pricing_info:
                self.add_text(SubElement(root,'provide-pricing-info'),self.provide_pricing_info)                 #optional
            if self.provide_receipt_info:
                self.add_text(SubElement(root,'provide-receipt-info'),self.provide_receipt_info)                 #optional
        SubElement(root,'delivery-spec')                                                                 #required
        SubElement(root,'return-spec')                                                                   #optional
        # SubElement(root,'pre-authorized-payment')                                                        #optional
        return root




    # class GetArtifact():
        # pass
#
    # class TransmitShipment():
        # pass
#
    # class GetManifest():
        # pass