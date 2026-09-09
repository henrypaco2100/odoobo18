# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    sd_tipo_pro_reg = fields.Selection(
        selection=[
            ("pro", "PRO"),
            ("reg", "REG"),
            ("coe_pro", "COE PRO"),
            ("coe_reg", "COE REG"),
        ],
        string="Tipo Odoobo PRO/REG/COE",
        copy=False,
        index=True,
    )
    sd_product_tmpl_id = fields.Many2one(
        "product.template",
        string="Producto Odoobo",
        copy=False,
        ondelete="set null",
        index=True,
    )
