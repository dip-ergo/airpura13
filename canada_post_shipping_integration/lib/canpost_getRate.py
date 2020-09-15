# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Syncoria Inc. (<https://www.syncoria.com>)
#    You should have received a copy of the License along with this program.

#################################################################################


import logging
import base64
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import dump
from xml.dom import minidom
import requests
import logging
import re
_logger = logging.getLogger(__name__)


class ConfigRate(object):

    def __init__(self, environment=None, prod_username=None, prod_password=None, dev_username=None, dev_password=None):
        self.environment = environment
        if not self.environment and dev_username and dev_password:
            self.username = dev_username
            self.password = dev_password
            self.url = 'https://ct.soa-gw.canadapost.ca/rs/ship/price'
        elif self.environment and prod_username and prod_password:
            self.username = prod_username
            self.password = prod_password
            self.url = 'https://soa-gw.canadapost.ca/rs/ship/price'
        else:
            raise Exception("Credentials Missing: Config must be correct format")
        self.header = {
            'Accept': 'application/vnd.cpc.ship.rate-v4+xml',
            'Content-Type': 'application/vnd.cpc.ship.rate-v4+xml',
            'Authorization': 'Basic {}'.format(base64.b64encode("{}:{}".format(self.username, self.password).encode('utf-8')).decode('utf-8')),
            'Accept-language': 'en-CA',
        }


class CanpostGetRate(object):

    class Dimensions():

        def __init__(self, length=None, width=None, height=None):
            self.length = length    # Required
            self.width = width      # Required
            self.height = height    # Required

    class ParcelCharacteristics():

        def __init__(self, weight=None, unpackeged=None, mailing_tube=None, oversized=None):
            self.weight = weight                  # Required
            self.unpackeged = unpackeged
            self.mailing_tube = mailing_tube
            self.oversized = oversized

    class Options():

        obj_count = 0

        def __init__(self, option_code=None, option_amount=None):
            if (CanpostGetRate.Options.obj_count < 20):
                CanpostGetRate.Options.obj_count += 1
                self.option_code = option_code             # Required
                self.option_amount = option_amount           # Required depend upon code
            else:
                raise Exception("Limit Exceed: Options can't be more than 20")

    class Services():
        obj_count = 0

        def __init__(self, service_code=None):
            if (CanpostGetRate.Services.obj_count < 20):
                CanpostGetRate.Services.obj_count += 1
                self.service_code = service_code               # Required
            else:
                raise Exception("Limit Exceed: Sercvices can't be more than 20")

    class Domestic():

        def __init__(self, postal_code=None):
            self.domestic = True
            self.postal_code = postal_code             # Required 

    class UnitedStates():

        def __init__(self, zip_code=None):
            self.zip_code = zip_code                # Required\

    class International():

        def __init__(self, country_code=None, postal_code=None):
            self.international = True
            self.country_code = country_code            # Required
            self.postal_code = postal_code

    def __init__(self, environment=None, prod_username=None, prod_password=None, dev_username=None, dev_password=None):
        self.__rate_config = ConfigRate(**{'environment': environment, 'prod_username': prod_username, 'prod_password': prod_password, 'dev_username': dev_username, 'dev_password': dev_password})
        self.options = []
        self.services = []

    def add_mailQuote(self, customer_number=None, contract_id=None, promo_code=None, quote_type=None, expected_mailing_date=None, origin_postal_code=None):
        self.customer_number = customer_number
        self.contract_id = contract_id
        self.promo_code = promo_code
        self.quote_type = quote_type
        self.expected_mailing_date = expected_mailing_date
        self.origin_postal_code = origin_postal_code

    @staticmethod
    def get_responseData(root):
        data = {}
        for child in root.getchildren():
            if child.getchildren():
                data[re.split('\\}\\b', child.tag)[-1]] = CanpostGetRate.get_responseData(child)
            elif child.attrib and child.attrib.get('rel'):
                    data[child.attrib['rel']] = child.attrib
            else:
                data[re.split('\\}\\b', child.tag)[-1]] = child.text
        return data

    @staticmethod
    def transform_data(xml):
        root = ElementTree.fromstring(xml)
        data = CanpostGetRate.get_responseData(root)
        return data

    @staticmethod
    def pretify(element):
        rough_string = ElementTree.tostring(element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t")

    @staticmethod
    def add_text(elem, text):
        elem.text = text
        return elem

    def __validate_data(self):                             # need to add try catch here
        if self.quote_type == 'commercial' and not self.customer_number and not contract_id:
            raise Exception("Required element Customer Number or Contract Id is missing")
        if not self.parcel_characteristics.weight:
            raise Exceptiaption_codeon("Required element weight is missing")
        elif float(self.parcel_characteristics.weight) <= 0:
            raise Exception("Weight can't be Zero or less than Zero")
        if not self.origin_postal_code:
            raise Exception("Required element origin-postal-code is missing")
        return True

    def __create_xml(self):
        mail_scenerio = Element('mailing-scenario', attrib={'xmlns': 'http://www.canadapost.ca/ws/ship/rate-v4'})
        if self.quote_type == 'commercial':
            CanpostGetRate.add_text(SubElement(mail_scenerio, 'customer-number'), self.customer_number)
            CanpostGetRate.add_text(SubElement(mail_scenerio, 'contract-id'), self.contract_id)
        self.promo_code and CanpostGetRate.add_text(SubElement(mail_scenerio, 'promo-code'), self.promo_code)
        CanpostGetRate.add_text(SubElement(mail_scenerio, 'quote-type'), self.quote_type)
        self.expected_mailing_date and CanpostGetRate.add_text(SubElement(mail_scenerio, 'expected-mailing-date'), self.expected_mailing_date)            
        if self.options:
            options = SubElement(mail_scenerio, 'options')
            for opt in self.options:
                option = SubElement(options, 'option')
                CanpostGetRate.add_text(SubElement(option, 'option-code'), opt.option_code)
                opt.option_amount and CanpostGetRate.add_text(SubElement(option, 'option-amount'), opt.option_amount)
        parcel_characteristics = SubElement(mail_scenerio, 'parcel-characteristics')
        CanpostGetRate.add_text(SubElement(parcel_characteristics, 'weight'), self.parcel_characteristics.weight)
        if self.parcel_characteristics.dimension.length or self.parcel_characteristics.dimension.width or self.parcel_characteristics.dimension.height:
            dimensions = SubElement(parcel_characteristics, 'dimensions')
        CanpostGetRate.add_text(SubElement(dimensions, 'length'), self.parcel_characteristics.dimension.length)
        CanpostGetRate.add_text(SubElement(dimensions, 'width'), self.parcel_characteristics.dimension.width)
        CanpostGetRate.add_text(SubElement(dimensions, 'height'), self.parcel_characteristics.dimension.height)        
        CanpostGetRate.add_text(SubElement(parcel_characteristics, 'unpackaged'), 'false')
        CanpostGetRate.add_text(SubElement(parcel_characteristics, 'mailing-tube'), 'false')
        CanpostGetRate.add_text(SubElement(parcel_characteristics, 'oversized'), 'false')
        services = SubElement(mail_scenerio, 'services')
        CanpostGetRate.add_text(SubElement(services, 'service-code'), self.services.service_code)        
        CanpostGetRate.add_text(SubElement(mail_scenerio, 'origin-postal-code'), self.origin_postal_code)        
        destination = SubElement(mail_scenerio, 'destination')
        if hasattr(self,'domestic'):
            domestic = SubElement(destination, 'domestic')
            CanpostGetRate.add_text(SubElement(domestic, 'postal-code'), self.domestic.postal_code)
        elif hasattr(self,'international'):
            international = SubElement(destination, 'international')
            CanpostGetRate.add_text(SubElement(international, 'country-code'), self.international.country_code)
            CanpostGetRate.add_text(SubElement(international, 'postal-code'), self.international.postal_code)
        elif hasattr(self,'united_states'):
            united_states = SubElement(destination, 'united-states')
            CanpostGetRate.add_text(SubElement(united_states, 'zip-code'), self.united_states.zip_code)
        xml_data = CanpostGetRate.pretify(mail_scenerio)   
        return xml_data

    def getRate(self):
        if self.__validate_data():
            data = self.__create_xml()
            response = requests.post(data=data, url=self.__rate_config.url, headers=self.__rate_config.header)
            response = CanpostGetRate.transform_data(response.content) 
            return response
