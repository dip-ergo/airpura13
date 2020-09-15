# -*- coding: utf-8 -*-
#################################################################################
##    Copyright (c) 2020 Syncoria Inc. (<https://www.syncoria.com/>)
#    You should have received a copy of the License along with this program.

#################################################################################

from . import  models
from . import wizard
from . import  tools

def pre_init_check(cr):
	from odoo.service import common
	from odoo.exceptions import Warning
	version_info = common.exp_version()
	server_serie =version_info.get('server_serie')
	if server_serie!='13.0':raise Warning('Module support Odoo series 13.0 found {}.'.format(server_serie))
	return True
