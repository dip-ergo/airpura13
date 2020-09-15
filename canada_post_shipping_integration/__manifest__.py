# -*- coding: utf-8 -*-
#################################################################################
# Author      : Syncoria Inc. (<https://www.syncoria.com>)
# Copyright(c): 2020 Syncoria Inc. 
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
#################################################################################
{
  "name"                 :  "Canada Post Shipping Integration",
  "summary"              :  """Integrate Canada Post Shipping functionality directly within ODOO ERP applications to deliver  logistical efficiencies.""",
  "category"             :  "Website/Shipping Logistics",
  "version"              :  "1.0.4",
  "author"               :  "Syncoria Inc. ",
  "license"              :  "Other proprietary",
  "website"              :  "https://www.syncoria.com",
  "description"          :  """Integrate Canada Post shipping functionality directly within ODOO ERP applications to deliver  logistical efficiencies.""",
  # "live_test_url"        :  "http://odoodemo.webkul.com/?module=canada_post_shipping_integration",
  "depends"              :  [
                             'odoo_shipping_service_apps',
                             #'website_sale_delivery',
                            ],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'views/canada_post_delivery_carrier.xml',
                             'views/product_packaging.xml',
                             'data/data.xml',
                             'data/delivery_demo.xml',
                            ],
  "demo"                 :  ['data/demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  199,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}
