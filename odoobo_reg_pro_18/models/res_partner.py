# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Se conservan los nombres técnicos de sd_plural_v13 para facilitar migración.
    sd_es_autor = fields.Boolean(
        string="Es Autor",
        company_dependent=True,
        help="Permite asociar este contacto como autor de publicaciones.",
    )
    sd_cuenta_pro = fields.Many2one(
        "account.account",
        string="Cuenta PRO",
        company_dependent=True,
        check_company=True,
        ondelete="restrict",
        domain="[('deprecated', '=', False)]",
    )
    sd_cuenta_reg = fields.Many2one(
        "account.account",
        string="Cuenta REG",
        company_dependent=True,
        check_company=True,
        ondelete="restrict",
        domain="[('deprecated', '=', False)]",
    )
    sd_cuenta_coe = fields.Many2one(
        "account.account",
        string="Cuenta COE PRO",
        company_dependent=True,
        check_company=True,
        ondelete="restrict",
        domain="[('deprecated', '=', False)]",
    )
    sd_cuenta_coe_reg = fields.Many2one(
        "account.account",
        string="Cuenta COE REG",
        company_dependent=True,
        check_company=True,
        ondelete="restrict",
        domain="[('deprecated', '=', False)]",
    )
    # Char a propósito: así se conserva el tipo de dato del módulo v13.
    sd_porcentaje_cuenta_coe = fields.Char(
        string="% COE",
        company_dependent=True,
        help="Porcentaje/identificador usado en el nombre de las cuentas COE, como en sd_plural_v13.",
    )

    def _odoobo_next_account_code(self, sequence_code):
        self.ensure_one()
        candidate = self.env["ir.sequence"].next_by_code(sequence_code)
        if not candidate:
            raise UserError(_("No se encontró la secuencia contable %s.", sequence_code))
        Account = self.env["account.account"].with_company(self.env.company)
        return Account._search_new_account_code(candidate)

    def _odoobo_create_liability_account(self, name, sequence_code):
        self.ensure_one()
        Account = self.env["account.account"].with_company(self.env.company)
        return Account.create({
            "name": name,
            "code": self._odoobo_next_account_code(sequence_code),
            "account_type": "liability_current",
            "reconcile": True,
            "company_ids": [Command.set(self.env.company.ids)],
        })

    def action_create_accounts_pro_reg(self):
        """Crea PRO y REG sin depender de account.account.type (eliminado en Odoo 18)."""
        for partner in self:
            partner_company = partner.with_company(self.env.company)
            if not partner_company.sd_es_autor:
                raise UserError(_("Primero marque el contacto como 'Es Autor'."))

            vals = {}
            if not partner_company.sd_cuenta_pro:
                account = partner._odoobo_create_liability_account(
                    _("PRO - %s", partner.name),
                    "odoobo.reg.pro.account.pro",
                )
                vals["sd_cuenta_pro"] = account.id
            if not partner_company.sd_cuenta_reg:
                account = partner._odoobo_create_liability_account(
                    _("REG - %s", partner.name),
                    "odoobo.reg.pro.account.reg",
                )
                vals["sd_cuenta_reg"] = account.id
            if vals:
                partner_company.with_context(odoobo_skip_author_sync=True).write(vals)
            partner._odoobo_sync_products()
        return True

    def action_create_accounts_coe(self):
        """Crea las cuentas COE PRO y COE REG conservando el esquema del módulo v13."""
        for partner in self:
            partner_company = partner.with_company(self.env.company)
            if not partner_company.sd_es_autor:
                raise UserError(_("Primero marque el contacto como 'Es Autor'."))
            if not partner_company.sd_porcentaje_cuenta_coe:
                raise UserError(_("Ingrese el campo '% COE' antes de crear las cuentas COE."))

            pct = partner_company.sd_porcentaje_cuenta_coe.strip()
            safe_name = (partner.name or "AUTOR").replace(" ", "_")
            vals = {}
            if not partner_company.sd_cuenta_coe:
                account = partner._odoobo_create_liability_account(
                    f"COE_{pct}_%_{safe_name}",
                    "odoobo.reg.pro.account.coe.pro",
                )
                vals["sd_cuenta_coe"] = account.id
            if not partner_company.sd_cuenta_coe_reg:
                account = partner._odoobo_create_liability_account(
                    f"COE_REG_{pct}_%_{safe_name}",
                    "odoobo.reg.pro.account.coe.reg",
                )
                vals["sd_cuenta_coe_reg"] = account.id
            if vals:
                partner_company.with_context(odoobo_skip_author_sync=True).write(vals)
            partner._odoobo_sync_products()
        return True

    def _odoobo_sync_products(self):
        products = self.env["product.template"].search([
            ("sd_autor_id", "in", self.ids),
            "|",
            ("sd_pro_reg_enabled", "=", True),
            ("sd_coe_enabled", "=", True),
        ])
        products._sync_odoobo_taxes(validate=False)

    def write(self, vals):
        res = super().write(vals)
        watched = {
            "sd_cuenta_pro", "sd_cuenta_reg", "sd_cuenta_coe", "sd_cuenta_coe_reg",
            "sd_porcentaje_cuenta_coe", "sd_es_autor",
        }
        if not self.env.context.get("odoobo_skip_author_sync") and watched & set(vals):
            self._odoobo_sync_products()
        return res
