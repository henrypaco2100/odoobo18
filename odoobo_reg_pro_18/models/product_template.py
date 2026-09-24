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
        help="Asigna los impuestos compartidos PRO y REG al producto.",
    )
    sd_coe_enabled = fields.Boolean(
        string="Aplicar COE PRO/REG",
        default=False,
        help="Asigna los impuestos compartidos COE PRO y COE REG al producto.",
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
        help="Importe del producto utilizado dinámicamente por los impuestos compartidos PRO/REG/COE.",
    )
    # Campo técnico numérico para que el motor de impuestos JS/POS pueda cargar
    # el modo sin depender de un Selection no soportado por el helper base.
    sd_tax_calc_mode = fields.Integer(
        string="Modo cálculo Odoobo",
        compute="_compute_sd_tax_calc_mode",
        store=True,
    )

    sd_cuenta_pro = fields.Many2one("account.account", string="Cuenta PRO", compute="_compute_sd_author_accounts", readonly=True)
    sd_cuenta_reg = fields.Many2one("account.account", string="Cuenta REG", compute="_compute_sd_author_accounts", readonly=True)
    sd_cuenta_coe = fields.Many2one("account.account", string="Cuenta COE PRO", compute="_compute_sd_author_accounts", readonly=True)
    sd_cuenta_coe_reg = fields.Many2one("account.account", string="Cuenta COE REG", compute="_compute_sd_author_accounts", readonly=True)

    # Compatibilidad de actualización desde las versiones v18 anteriores.
    # Estos campos existían en las vistas/módulos v1-v4. Se conservan para que
    # Odoo pueda validar las vistas antiguas que ya están guardadas en la BD
    # ANTES de que el XML de esta versión las reemplace durante -u.
    # En la lógica actual apuntan a los impuestos COMPARTIDOS PRO/REG/COE.
    sd_tax_pro_id = fields.Many2one(
        "account.tax", string="Impuesto PRO", company_dependent=True,
        copy=False, readonly=True, ondelete="set null",
    )
    sd_tax_reg_id = fields.Many2one(
        "account.tax", string="Impuesto REG", company_dependent=True,
        copy=False, readonly=True, ondelete="set null",
    )
    sd_tax_coe_pro_id = fields.Many2one(
        "account.tax", string="Impuesto COE PRO", company_dependent=True,
        copy=False, readonly=True, ondelete="set null",
    )
    sd_tax_coe_reg_id = fields.Many2one(
        "account.tax", string="Impuesto COE REG", company_dependent=True,
        copy=False, readonly=True, ondelete="set null",
    )

    @api.depends("sd_tipo_importe")
    def _compute_sd_tax_calc_mode(self):
        modes = {"fixed": 1, "percent": 2, "division": 3, "group": 0}
        for product in self:
            product.sd_tax_calc_mode = modes.get(product.sd_tipo_importe, 1)

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

    # Código interno editorial: sigue disponible, pero ya NO tiene secuencia en
    # este módulo. La secuencia por categoría vive en odoobo_producto_v18.
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

    @api.model
    def _odoobo_shared_tax_vals(self, company, kind, group):
        country = company.account_fiscal_country_id or company.country_id
        labels = {"pro": "PRO", "reg": "REG", "coe_pro": "COE PRO", "coe_reg": "COE REG"}
        sequences = {"pro": 90, "reg": 91, "coe_pro": 92, "coe_reg": 93}
        label = labels[kind]
        return {
            "name": label,
            "invoice_label": label,
            "type_tax_use": "sale",
            # Un único impuesto compartido. El importe real se calcula con el
            # producto en account.tax._eval_tax_amount_fixed_amount.
            "amount_type": "fixed",
            "amount": 0.0,
            "sequence": sequences[kind],
            "company_id": company.id,
            "country_id": country.id,
            "tax_group_id": group.id,
            "price_include_override": "tax_excluded",
            "include_base_amount": False,
            "is_base_affected": False,
            "sd_tipo_pro_reg": kind,
            "sd_product_tmpl_id": False,
        }

    @api.model
    def _odoobo_get_shared_tax(self, company, kind):
        Tax = self.env["account.tax"].with_company(company).sudo()
        tax = Tax.search([
            ("company_id", "=", company.id),
            ("sd_tipo_pro_reg", "=", kind),
            ("sd_product_tmpl_id", "=", False),
        ], limit=1)
        group = self._odoobo_get_tax_group(company)
        vals = self._odoobo_shared_tax_vals(company, kind, group)
        if tax:
            # No se modifica el importe por producto; siempre queda en 0 y el
            # motor dinámico toma el valor del producto de cada línea.
            tax.write(vals)
            return tax

        # Compatibilidad: si ya existía un impuesto manual PRO/REG sin marcar,
        # se reutiliza en lugar de crear un duplicado.
        label = vals["name"]
        candidate = Tax.search([
            ("company_id", "=", company.id),
            ("name", "=", label),
            ("type_tax_use", "=", "sale"),
            ("sd_product_tmpl_id", "=", False),
        ], limit=1)
        if candidate:
            candidate.write(vals)
            return candidate
        return Tax.create(vals)

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
            raise UserError(_("No se puede configurar %s para '%s':\n- %s", label, self.display_name, "\n- ".join(errors)))
        return not errors

    def _odoobo_remove_kind_taxes(self, kinds):
        self.ensure_one()
        to_unlink = self.taxes_id.filtered(lambda t: t.sd_tipo_pro_reg in kinds)
        if to_unlink:
            self.with_context(odoobo_skip_tax_sync=True).write({
                "taxes_id": [Command.unlink(tax.id) for tax in to_unlink],
            })

    def _odoobo_sync_pair(self, enabled, kinds, accounts, validate=False):
        self.ensure_one()
        # Elimina cualquier impuesto PRO/REG/COE antiguo (incluyendo los
        # impuestos por producto de versiones anteriores) antes de asignar los
        # compartidos.
        self._odoobo_remove_kind_taxes(kinds)
        if not enabled:
            return
        if not self._odoobo_validate_pair(" / ".join(kinds).upper(), accounts, validate):
            return
        shared = self.env["account.tax"]
        for kind in kinds:
            shared |= self._odoobo_get_shared_tax(self.env.company, kind)
        if shared:
            self.with_context(odoobo_skip_tax_sync=True).write({
                "taxes_id": [Command.link(tax.id) for tax in shared],
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

            # Mantiene los campos técnicos de compatibilidad apuntando a los
            # impuestos compartidos. Esto evita referencias obsoletas de las
            # versiones que creaban un impuesto por producto.
            compat_vals = {
                "sd_tax_pro_id": False,
                "sd_tax_reg_id": False,
                "sd_tax_coe_pro_id": False,
                "sd_tax_coe_reg_id": False,
            }
            if product.sd_pro_reg_enabled:
                compat_vals.update({
                    "sd_tax_pro_id": product._odoobo_get_shared_tax(self.env.company, "pro").id,
                    "sd_tax_reg_id": product._odoobo_get_shared_tax(self.env.company, "reg").id,
                })
            if product.sd_coe_enabled:
                compat_vals.update({
                    "sd_tax_coe_pro_id": product._odoobo_get_shared_tax(self.env.company, "coe_pro").id,
                    "sd_tax_coe_reg_id": product._odoobo_get_shared_tax(self.env.company, "coe_reg").id,
                })
            product.with_context(odoobo_skip_tax_sync=True).write(compat_vals)
        return True

    def action_sd_sync_pro_reg_taxes(self):
        self._sync_odoobo_taxes(validate=True)
        return True

    @api.model
    def _odoobo_migrate_legacy_product_taxes(self):
        """Actualización v5: sustituye impuestos por-producto por impuestos compartidos.

        Los impuestos históricos se archivan (no se borran) para no afectar
        asientos ya contabilizados.
        """
        Tax = self.env["account.tax"].sudo()
        legacy = Tax.search([
            ("sd_tipo_pro_reg", "!=", False),
            ("sd_product_tmpl_id", "!=", False),
        ])
        affected = self.browse(legacy.mapped("sd_product_tmpl_id").ids)
        # También toma productos que todavía tengan impuestos legados enlazados.
        if legacy:
            affected |= self.search([("taxes_id", "in", legacy.ids)])
        for product in affected:
            legacy_on_product = product.taxes_id & legacy
            if legacy_on_product:
                product.with_context(odoobo_skip_tax_sync=True).write({
                    "taxes_id": [Command.unlink(tax.id) for tax in legacy_on_product],
                })
            product._sync_odoobo_taxes(validate=False)
        if legacy:
            legacy.write({"active": False})
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
