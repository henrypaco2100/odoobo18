# -*- coding: utf-8 -*-
{
    "name": "ESI - Remisiones Odoo 18",
    "version": "18.0.1.0.5",
    "category": "Inventory/Inventory",
    "summary": "Reportes de remisión y consignación para Odoo 18",
    "description": """
Reportes ESI para Odoo 18 Community:
- Nota de Remisión.
- Entrega de Consignación.
- Entrega de Materiales.
- Recepción de Consignación.
- Devolución de Proveedores.
- Devolución de Librerías.

Incluye cabecera con logo e información de la compañía.
En Nota de Remisión: IMPORTE TOTAL = CANTIDAD x PVP; COSTO TOTAL = CANTIDAD x COSTO.
Las columnas COSTO, COSTO TOTAL e IMPORTE TOTAL son opcionales desde Información adicional.
Los importes se imprimen sin símbolo de moneda (sin Bs.).
Sin dependencias de módulos de terceros.
    """,
    "author": "ESI Bolivia",
    "website": "https://esibolivia.store",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "views/stock_picking_views.xml",
        "report/report_actions.xml",
        "report/report_templates.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
