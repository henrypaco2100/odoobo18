# -*- coding: utf-8 -*-
from html import escape

from markupsafe import Markup
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    esi_show_line_date = fields.Boolean(string="Mostrar fecha", default=False)
    esi_show_analytic = fields.Boolean(string="Mostrar analítica", default=True)
    esi_check_number = fields.Char(string="Nro. de cheque")

    # ESI corrección Odoo 18: salida HTML/PDF robusta para textos con tildes/ñ.
    # Además corrige textos que ya lleguen como mojibake (ej. "LÃ¡mpara").
    def esi_report_text(self, value):
        if value in (False, None):
            return Markup("")
        text = str(value)
        markers = ("Ã", "Â", "â€", "â€™", "â€œ", "â€", "ð")
        if any(marker in text for marker in markers):
            original_score = sum(text.count(marker) for marker in markers)
            for encoding in ("cp1252", "latin1"):
                try:
                    candidate = text.encode(encoding).decode("utf-8")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue
                candidate_score = sum(candidate.count(marker) for marker in markers)
                if candidate_score < original_score:
                    text = candidate
                    break
        # Convertimos caracteres no ASCII en entidades HTML numéricas.
        # Así wkhtmltopdf/browser no puede reinterpretar UTF-8 como Windows-1252.
        escaped = escape(text, quote=False)
        ascii_html = escaped.encode("ascii", "xmlcharrefreplace").decode("ascii")
        return Markup(ascii_html)

    def esi_report_filename(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(_("El asiento debe estar publicado para imprimir el comprobante."))
        return "Comprobante Contable - %s" % (self.name or "Borrador")

    def esi_date_in_words(self):
        self.ensure_one()
        # ESI Odoo 18: account.move.type fue reemplazado hace varias versiones por move_type.
        if self.move_type in (
            "out_invoice", "in_invoice", "out_refund", "in_refund",
            "out_receipt", "in_receipt",
        ) and self.invoice_date:
            date = self.invoice_date
        else:
            date = self.date
        months = (
            "", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
        )
        return "%02d DE %s DEL %s" % (date.day, months[date.month], date.year) if date else ""

    def esi_ordered_lines(self):
        self.ensure_one()
        return self.line_ids.sorted(key=lambda line: (line.date or self.date, line.id))

    def esi_total_debit(self):
        self.ensure_one()
        return sum(self.line_ids.mapped("debit"))

    def esi_total_credit(self):
        self.ensure_one()
        return sum(self.line_ids.mapped("credit"))

    def esi_amount_in_words(self):
        self.ensure_one()
        amount = self.esi_total_debit()
        currency = self.company_id.currency_id
        try:
            return currency.amount_to_text(amount).upper()
        except Exception:
            integer = int(amount)
            cents = int(round((amount - integer) * 100))
            return "%s %02d/100" % (integer, cents)

    def esi_line_analytic_label(self, line):
        """Convierte analytic_distribution de Odoo 18 en nombres legibles.

        Odoo 18 ya no usa analytic_account_id en account.move.line. Las claves de
        analytic_distribution pueden contener uno o varios IDs separados por coma.
        """
        self.ensure_one()
        distribution = line.analytic_distribution or {}
        if not distribution:
            return ""

        groups = []
        AnalyticAccount = self.env["account.analytic.account"]
        for raw_key in distribution.keys():
            account_ids = []
            for part in str(raw_key).split(","):
                part = part.strip()
                if part.isdigit():
                    account_ids.append(int(part))
            accounts = AnalyticAccount.browse(account_ids).exists()
            if accounts:
                groups.append(" / ".join(accounts.mapped("display_name")))
        return "; ".join(groups)

    def action_esi_comprobante_preview(self):
        self.ensure_one()
        return self.env.ref("odoobo_18.action_comprobante_contable_html").report_action(self)

    def action_esi_comprobante_pdf(self):
        self.ensure_one()
        return self.env.ref("odoobo_18.action_comprobante_contable_pdf").report_action(self)
