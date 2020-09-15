# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Syncoria Inc. (<https://www.syncoria.com>)
#    You should have received a copy of the License along with this program.

#################################################################################

from odoo.exceptions import Warning, ValidationError
from odoo import fields, models

class ProductPackage(models.Model):
    _inherit = 'product.package'

    delivery_type = fields.Selection(selection_add=[('canada_post', 'Canada Post')])


class ProductPackaging(models.Model):
    _inherit = 'product.packaging'

    package_carrier_type = fields.Selection(selection_add=[('canada_post', 'Canada Post')])


class CanPostShipping(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('canada_post', 'Canada Post')])
    canpost_test_username = fields.Char(string="Development User Name")
    canpost_test_password = fields.Char(string="Development Password")
    canpost_production_username = fields.Char(string="Production User Name")
    canpost_production_password = fields.Char(string="Production Password")
    canpost_service_type = fields.Many2one(string="Service Type", comodel_name="canpost.service.type")
    canpost_option_type = fields.Many2many(string="Desired Options", comodel_name="canpost.option.type")
    canpost_quote_type = fields.Selection(selection=[('commercial', 'Commercial'), ('counter', 'Counter')], string="Customer Type", default='counter')
    canpost_customer_number = fields.Char(string="Customer Number")
    canpost_contract_id = fields.Char(string="Contract ID")
    canpost_promo_code = fields.Char(string="Promo Code")
    canpost_method_of_payment = fields.Many2one(string="Intended Method of Payment" , comodel_name="canpost.intended.payment.method")
    canpost_mailed_on_behalf_of = fields.Char(string="Mailed on Behalf of")

class CanpostServiceType(models.Model):
    _name = "canpost.service.type"
    _description = "Canada Post Service Type"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)


class CanpostOptionType(models.Model):
    _name = "canpost.option.type"
    _description = "Canada Post Option Type"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)


class CanpostIntendedPaymentMethod(models.Model):
    _name = "canpost.intended.payment.method"
    _description = "Canada Post Intended Payment Method"

    name = fields.Char(string='Name', required=True)

class CanpostStockPicking(models.Model):
    _inherit = "stock.picking"
    canpost_returnlabel = fields.Many2one(comodel_name = "ir.attachment")
