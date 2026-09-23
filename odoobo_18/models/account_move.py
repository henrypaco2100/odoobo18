# -*- coding: utf-8 -*-
import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    # Compatibilidad con versiones anteriores del módulo.
    # La fecha SOLO se imprime en el encabezado; nunca se imprime por línea.
    esi_show_line_date = fields.Boolean(string="Mostrar fecha", default=False)
    esi_show_analytic = fields.Boolean(string="Mostrar analítica", default=True)
    esi_check_number = fields.Char(string="Nro. de cheque")

    def _esi_fix_mojibake(self, value):
        """Corrige mojibake frecuente UTF-8/Windows-1252 antes de imprimir."""
        if value in (False, None):
            return ""
        text = str(value)
        markers = ("Ã", "Â", "â€", "â€™", "â€œ", "â€\x9d", "ð")
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
        return text

    def esi_report_text(self, value, output_type=None):
        """Texto estable para Vista HTML y PDF.

        ESI corrección: la vista HTML de Odoo interpreta UTF-8 correctamente, pero
        el wkhtmltopdf del servidor estaba produciendo mojibake (MueblerÃ­a,
        DESCRIPCIÃ“N, etc.). En PDF se translitera únicamente el texto dinámico a
        ASCII para garantizar que no aparezcan caracteres raros; en HTML se conserva
        el texto Unicode corregido.
        """
        text = self._esi_fix_mojibake(value)
        if output_type == "pdf":
            return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return text

    def esi_format_amount(self, value):
        """Importes sin símbolo de moneda, con 2 decimales."""
        try:
            amount = float(value or 0.0)
        except (TypeError, ValueError):
            amount = 0.0
        # Formato hispano estable para PDF: 1.234,56 (sin Bs., $, etc.).
        raw = f"{amount:,.2f}"
        return raw.replace(",", "X").replace(".", ",").replace("X", ".")

    def esi_report_filename(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(_("El asiento debe estar publicado para imprimir el comprobante."))
        return "Comprobante Contable - %s" % (self.name or "Borrador")

    def esi_date_in_words(self):
        self.ensure_one()
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
            text = currency.amount_to_text(amount).upper()
            # ESI: por solicitud del cliente, usar BOLIVIANO en singular en todos los importes en letras.
            text = text.replace("BOLIVIANOS", "BOLIVIANO")
            return text
        except Exception:
            integer = int(amount)
            cents = int(round((amount - integer) * 100))
            return "%s %02d/100 BOLIVIANO" % (integer, cents)

    def esi_line_analytic_label(self, line):
        """Convierte analytic_distribution de Odoo 18 en nombres legibles."""
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

    def esi_report_partner_name(self):
        """Nombre completo del encabezado con fallback a los apuntes.

        ESI: en asientos generados por POS u otros procesos partner_id del asiento
        puede venir vacío aunque alguna línea tenga empresa/contacto.
        """
        self.ensure_one()
        if self.partner_id:
            return self.partner_id.name or self.partner_id.display_name or ""
        partners = self.line_ids.mapped("partner_id").filtered(lambda p: p)
        return partners[:1].name if partners else ""

    @api.onchange("partner_id")
    def _onchange_esi_partner_to_lines(self):
        """Al elegir Nombre completo, lo coloca por defecto en todas las líneas."""
        for move in self:
            if move.move_type == "entry" and move.partner_id and move.state == "draft":
                for line in move.line_ids:
                    line.partner_id = move.partner_id

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        # ESI: asegura consistencia también cuando el asiento se crea por código.
        for move in moves.filtered(lambda m: m.move_type == "entry" and m.state == "draft" and m.partner_id):
            lines = move.line_ids.filtered(lambda l: l.partner_id != move.partner_id)
            if lines:
                lines.write({"partner_id": move.partner_id.id})
        return moves

    def write(self, vals):
        res = super().write(vals)
        if "partner_id" in vals:
            for move in self.filtered(lambda m: m.move_type == "entry" and m.state == "draft" and m.partner_id):
                lines = move.line_ids.filtered(lambda l: l.partner_id != move.partner_id)
                if lines:
                    lines.write({"partner_id": move.partner_id.id})
        return res

    def action_esi_comprobante_preview(self):
        self.ensure_one()
        return self.env.ref("odoobo_18.action_comprobante_contable_html").report_action(self)

    def action_esi_comprobante_pdf(self):
        self.ensure_one()
        return self.env.ref("odoobo_18.action_comprobante_contable_pdf").report_action(self)
