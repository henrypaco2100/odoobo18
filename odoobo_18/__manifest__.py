# -*- coding: utf-8 -*-
{
    "name": "ESI - Comprobante Contable Odoo 18",
    "version": "18.0.1.0.5",
    "category": "Accounting/Accounting",
    "summary": "Comprobante contable con vista previa y PDF para Odoo 18",
    "description": """
Comprobante Contable ESI adaptado a Odoo 18 Community.

- Vista previa HTML y PDF.
- Cabecera con logo e información de la empresa.
- Fecha, usuario, señores, glosa, tipo, número e importe.
- Nro. de cheque opcional: no se imprime cuando está vacío.
- Analítica adaptada al campo analytic_distribution de Odoo 18.
- Fecha de línea siempre visible.
- Campo Nombre completo en el encabezado de asientos; se replica por defecto en las líneas y en el reporte.
- Importes sin símbolo de moneda (sin Bs.).
- Estilo PDF alineado al comprobante histórico de Odoo 13.
- Sin dependencias de módulos de terceros.
    """,
    "author": "ESI Bolivia",
    "website": "https://esibolivia.store",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "views/account_move_views.xml",
        "report/account_preview_compat.xml",
        "report/comprobante_report.xml",
        "report/comprobante_template.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
