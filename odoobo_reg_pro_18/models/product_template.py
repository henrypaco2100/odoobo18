# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError


EDITORIAL_EDITION_SELECTION = [
    ("Primera", "Primera"), ("Segunda", "Segunda"), ("Tercera", "Tercera"),
    ("Cuarta", "Cuarta"), ("Quinta", "Quinta"), ("Sexta", "Sexta"),
    ("Séptima", "Séptima"), ("Octava", "Octava"), ("Novena", "Novena"),
    ("Décima", "Décima"), ("Decimoprimera", "Decimoprimera"),
    ("Decimosegunda", "Decimosegunda"), ("Decimotercera", "Decimotercera"),
    ("Decimocuarta", "Decimocuarta"), ("Decimoquinta", "Decimoquinta"),
]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # -------------------------------------------------------------------------
    # Datos editoriales preservados de sd_plural_v13
    # -------------------------------------------------------------------------
    sd_informacion_adicional = fields.Text("Información Adicional")
    sd_autor = fields.Char("Autor")
    sd_autor_id = fields.Many2one(
        "res.partner",
        string="Autor Partner",
        domain="[('sd_es_autor', '=', True)]",
        ondelete="restrict",
    )
    sd_tematica = fields.Char("Temática")
    sd_coleccion = fields.Char("Colección")
    sd_gestion_publicacion = fields.Char("Año Publicación")
    sd_edicion = fields.Selection(EDITORIAL_EDITION_SELECTION, string="Edición")
    sd_deposito_legal = fields.Char("Depósito Legal")
    sd_observaciones = fields.Text("Observaciones")
    sd_paginas = fields.Integer("Páginas")
    sd_formato = fields.Char("Formato")
    sd_tipo_tapa = fields.Char("Tipo de Tapa")
    sd_precio_FOB_USD = fields.Char("Precio FOB USD")
    sd_tiraje = fields.Char("Tiraje")
    sd_comentarios = fields.Text("Reseña")
    sd_libro_lcv = fields.Boolean("Libro LCV")
    sd_codigo_interno = fields.Char("Código Interno", index="trigram")

    # -------------------------------------------------------------------------
    # PRO / REG / COE
    # -------------------------------------------------------------------------
    sd_pro_reg_enabled = fields.Boolean(
        string="Aplicar PRO/REG",
        default=False,
        help="Genera y asigna los impuestos dedicados PRO y REG del producto.",
    )
    sd_coe_enabled = fields.Boolean(
        string="Aplicar COE PRO/REG",
        default=False,
        help="Genera y asigna los impuestos dedicados COE PRO y COE REG del producto.",
    )
    sd_tipo_importe = fields.Selection(
        selection=[
            ("fixed", "Fijo por unidad"),
            ("percent", "Porcentaje sobre el precio"),
            ("division", "Porcentaje sobre el precio, impuesto incluido"),
            ("group", "Grupo de impuestos (compatibilidad v13)"),
        ],
        string="Cálculo de impuestos",
        default="fixed",
        required=True,
    )
    sd_amount_impuesto = fields.Float(
        string="Importe / Porcentaje",
        digits=(16, 4),
        help="Valor usado por PRO/REG y COE PRO/REG, manteniendo la lógica del módulo v13.",
    )

    sd_cuenta_pro = fields.Many2one("account.account", string="Cuenta PRO", compute="_compute_sd_author_accounts", readonly=True)
    sd_cuenta_reg = fields.Many2one("account.account", string="Cuenta REG", compute="_compute_sd_author_accounts", readonly=True)
    sd_cuenta_coe = fields.Many2one("account.account", string="Cuenta COE PRO", compute="_compute_sd_author_accounts", readonly=True)
    sd_cuenta_coe_reg = fields.Many2one("account.account", string="Cuenta COE REG", compute="_compute_sd_author_accounts", readonly=True)

    sd_tax_pro_id = fields.Many2one("account.tax", string="Impuesto PRO generado", company_dependent=True, copy=False, readonly=True, ondelete="set null")
    sd_tax_reg_id = fields.Many2one("account.tax", string="Impuesto REG generado", company_dependent=True, copy=False, readonly=True, ondelete="set null")
    sd_tax_coe_pro_id = fields.Many2one("account.tax", string="Impuesto COE PRO generado", company_dependent=True, copy=False, readonly=True, ondelete="set null")
    sd_tax_coe_reg_id = fields.Many2one("account.tax", string="Impuesto COE REG generado", company_dependent=True, copy=False, readonly=True, ondelete="set null")

    @api.depends("sd_autor_id")
    @api.depends_context("company")
    def _compute_sd_author_accounts(self):
        for product in self:
            author = product.sd_autor_id.with_company(self.env.company) if product.sd_autor_id else False
            product.sd_cuenta_pro = author.sd_cuenta_pro if author else False
            product.sd_cuenta_reg = author.sd_cuenta_reg if author else False
            product.sd_cuenta_coe = author.sd_cuenta_coe if author else False
            product.sd_cuenta_coe_reg = author.sd_cuenta_coe_reg if author else False

    @api.onchange("sd_autor_id")
    def _onchange_sd_autor_id(self):
        for product in self:
            product.sd_autor = product.sd_autor_id.name if product.sd_autor_id else False
            if product.sd_autor_id:
                product.sd_pro_reg_enabled = True
                author = product.sd_autor_id.with_company(self.env.company)
                if author.sd_cuenta_coe and author.sd_cuenta_coe_reg:
                    product.sd_coe_enabled = True
            else:
                product.sd_pro_reg_enabled = False
                product.sd_coe_enabled = False

    @api.model_create_multi
    def create(self, vals_list):
        Partner = self.env["res.partner"]
        prepared = []
        for vals in vals_list:
            vals = dict(vals)
            author_id = vals.get("sd_autor_id")
            if author_id:
                author = Partner.browse(author_id)
                vals.setdefault("sd_autor", author.name)
                vals.setdefault("sd_pro_reg_enabled", True)
            prepared.append(vals)
        products = super().create(prepared)
        if not self.env.context.get("odoobo_skip_tax_sync"):
            products._sync_odoobo_taxes(validate=False)
        return products

    def write(self, vals):
        vals = dict(vals)
        if "sd_autor_id" in vals:
            author = self.env["res.partner"].browse(vals["sd_autor_id"]) if vals["sd_autor_id"] else False
            vals["sd_autor"] = author.name if author else False
        res = super().write(vals)
        watched = {"sd_autor_id", "sd_pro_reg_enabled", "sd_coe_enabled", "sd_tipo_importe", "sd_amount_impuesto"}
        if not self.env.context.get("odoobo_skip_tax_sync") and watched & set(vals):
            self._sync_odoobo_taxes(validate=False)
        return res

    # Código interno: en Odoo 18 name_get fue sustituido por display_name.
    @api.depends("name", "default_code", "sd_codigo_interno")
    def _compute_display_name(self):
        super()._compute_display_name()
        for product in self:
            if product.sd_codigo_interno and product.display_name:
                product.display_name = f"{product.display_name} [{product.sd_codigo_interno}]"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        result = super().name_search(name=name, args=args, operator=operator, limit=limit)
        if not name or (limit and len(result) >= limit):
            return result
        existing_ids = [record_id for record_id, _display in result]
        extra_domain = list(args or []) + [("sd_codigo_interno", operator, name)]
        if existing_ids:
            extra_domain.append(("id", "not in", existing_ids))
        remaining = None if not limit else max(limit - len(result), 0)
        extras = self.search(extra_domain, limit=remaining)
        return result + [(record.id, record.display_name) for record in extras]

    def action_sd_sync_pro_reg_taxes(self):
        self._sync_odoobo_taxes(validate=True)
        return True

    def _odoobo_get_tax_group(self, company):
        country = company.account_fiscal_country_id or company.country_id
        if not country:
            raise UserError(_("La compañía %s no tiene país fiscal configurado.", company.display_name))
        TaxGroup = self.env["account.tax.group"].with_company(company)
        group = TaxGroup.search([
            ("name", "=", "PRO/REG/COE Odoobo"),
            ("company_id", "=", company.id),
            ("country_id", "=", country.id),
        ], limit=1)
        if not group:
            group = TaxGroup.create({
                "name": "PRO/REG/COE Odoobo",
                "company_id": company.id,
                "country_id": country.id,
            })
        return group

    def _odoobo_prepare_tax_vals(self, company, group, kind, amount):
        self.ensure_one()
        country = company.account_fiscal_country_id or company.country_id
        labels = {"pro": "PRO", "reg": "REG", "coe_pro": "COE PRO", "coe_reg": "COE REG"}
        sequences = {"pro": 90, "reg": 91, "coe_pro": 92, "coe_reg": 93}
        label = labels[kind]
        return {
            "name": f"{label} | {self.display_name} | #{self.id}",
            "invoice_label": label,
            "type_tax_use": "sale",
            "amount_type": self.sd_tipo_importe,
            "amount": amount,
            "sequence": sequences[kind],
            "company_id": company.id,
            "country_id": country.id,
            "tax_group_id": group.id,
            "price_include_override": "tax_excluded",
            "include_base_amount": False,
            "is_base_affected": False,
            "sd_tipo_pro_reg": kind,
            "sd_product_tmpl_id": self.id,
        }

    def _odoobo_configure_tax_account(self, tax, account):
        tax.invoice_repartition_line_ids.filtered(lambda line: line.repartition_type == "tax").write({"account_id": account.id})
        tax.refund_repartition_line_ids.filtered(lambda line: line.repartition_type == "tax").write({"account_id": account.id})

    def _odoobo_ensure_tax(self, company, kind, amount, account, group):
        self.ensure_one()
        field_by_kind = {
            "pro": "sd_tax_pro_id",
            "reg": "sd_tax_reg_id",
            "coe_pro": "sd_tax_coe_pro_id",
            "coe_reg": "sd_tax_coe_reg_id",
        }
        product = self.with_company(company)
        tax_field = field_by_kind[kind]
        tax = product[tax_field]
        Tax = self.env["account.tax"].with_company(company)
        vals = product._odoobo_prepare_tax_vals(company, group, kind, amount)
        if tax and tax.exists() and tax.company_id == company:
            tax.write(vals)
        else:
            tax = Tax.create(vals)
            product.with_context(odoobo_skip_tax_sync=True).write({tax_field: tax.id})
        product._odoobo_configure_tax_account(tax, account)
        return tax

    def _odoobo_unlink_generated(self, kinds):
        self.ensure_one()
        field_by_kind = {
            "pro": "sd_tax_pro_id", "reg": "sd_tax_reg_id",
            "coe_pro": "sd_tax_coe_pro_id", "coe_reg": "sd_tax_coe_reg_id",
        }
        generated = self.env["account.tax"]
        for kind in kinds:
            generated |= self[field_by_kind[kind]]
        if generated:
            commands = [Command.unlink(tax.id) for tax in generated if tax in self.taxes_id]
            if commands:
                self.with_context(odoobo_skip_tax_sync=True).write({"taxes_id": commands})

    def _odoobo_validate_pair(self, label, accounts, validate):
        self.ensure_one()
        errors = []
        if not self.sd_autor_id:
            errors.append(_("Debe seleccionar un Autor."))
        elif not self.sd_autor_id.with_company(self.env.company).sd_es_autor:
            errors.append(_("El contacto seleccionado no está marcado como Autor."))
        if self.sd_amount_impuesto <= 0:
            errors.append(_("El Importe / Porcentaje debe ser mayor a 0."))
        if self.sd_tipo_importe == "group":
            errors.append(_("El tipo 'Grupo de impuestos' se conserva solo para migración. Use Fijo, Porcentaje o División."))
        for account, account_label in accounts:
            if not account:
                errors.append(_("Falta la cuenta %s.", account_label))
            elif self.env.company not in account.company_ids:
                errors.append(_("La cuenta %s no pertenece a la compañía activa.", account_label))
        if errors and validate:
            raise UserError(_("No se puede generar %s para '%s':\n- %s", label, self.display_name, "\n- ".join(errors)))
        return not errors

    def _odoobo_sync_pair(self, enabled, kinds, accounts, validate=False):
        self.ensure_one()
        if not enabled:
            self._odoobo_unlink_generated(kinds)
            return
        if not self._odoobo_validate_pair(" / ".join(kinds).upper(), accounts, validate):
            self._odoobo_unlink_generated(kinds)
            return
        group = self._odoobo_get_tax_group(self.env.company)
        amount = abs(self.sd_amount_impuesto)
        account_map = {label: account for account, label in accounts}
        specs = []
        if kinds == ("pro", "reg"):
            specs = [("pro", amount, account_map["PRO"]), ("reg", -amount, account_map["REG"])]
        else:
            specs = [("coe_pro", amount, account_map["COE PRO"]), ("coe_reg", -amount, account_map["COE REG"])]
        taxes_to_link = self.env["account.tax"]
        for kind, tax_amount, account in specs:
            taxes_to_link |= self._odoobo_ensure_tax(self.env.company, kind, tax_amount, account, group)
        missing = taxes_to_link - self.taxes_id
        if missing:
            self.with_context(odoobo_skip_tax_sync=True).write({
                "taxes_id": [Command.link(tax.id) for tax in missing],
            })

    def _sync_odoobo_taxes(self, validate=False):
        for product in self:
            product = product.with_company(self.env.company)
            product._odoobo_sync_pair(
                product.sd_pro_reg_enabled,
                ("pro", "reg"),
                ((product.sd_cuenta_pro, "PRO"), (product.sd_cuenta_reg, "REG")),
                validate=validate,
            )
            product._odoobo_sync_pair(
                product.sd_coe_enabled,
                ("coe_pro", "coe_reg"),
                ((product.sd_cuenta_coe, "COE PRO"), (product.sd_cuenta_coe_reg, "COE REG")),
                validate=validate,
            )
        return True


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends("name", "default_code", "product_tmpl_id", "sd_codigo_interno")
    @api.depends_context("display_default_code", "seller_id", "company_id", "partner_id", "lang")
    def _compute_display_name(self):
        super()._compute_display_name()
        for product in self:
            if product.sd_codigo_interno and product.display_name:
                product.display_name = f"{product.display_name} [{product.sd_codigo_interno}]"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        result = super().name_search(name=name, args=args, operator=operator, limit=limit)
        if not name or (limit and len(result) >= limit):
            return result
        existing_ids = [record_id for record_id, _display in result]
        extra_domain = list(args or []) + [("sd_codigo_interno", operator, name)]
        if existing_ids:
            extra_domain.append(("id", "not in", existing_ids))
        remaining = None if not limit else max(limit - len(result), 0)
        extras = self.search(extra_domain, limit=remaining)
        return result + [(record.id, record.display_name) for record in extras]
