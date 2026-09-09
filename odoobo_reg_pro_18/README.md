# odoobo_reg_pro_18

Versión Odoo 18 centrada en la lógica editorial necesaria de `sd_plural_v13`.

## Incluye

- Autor (`res.partner`) con cuentas PRO, REG, COE PRO y COE REG.
- Creación automática de cuentas compatible con `account.account` de Odoo 18.
- Impuestos dedicados por producto: PRO (+), REG (-), COE PRO (+), COE REG (-).
- Ventas / Facturación / POS usando `taxes_id` estándar; no modifica archivos nativos de `point_of_sale`.
- Datos editoriales: temática, colección, año, edición, depósito legal, páginas, formato, tapa, FOB, tiraje, reseña, observaciones, Libro LCV e información adicional.
- Código Interno visible en listas, buscable y añadido al nombre mostrado del producto.
- Kardex / Informe por Venta de Publicaciones por Autor en Excel desde **Inventario > Reportes > Kardex por Autor**.

## No incluye

MRP, personalizaciones de picking, multi-store, reportes de producción ni otras funciones del antiguo `sd_plural_v13`.

## COE

Se conserva la lógica original: el valor `sd_amount_impuesto` del producto se usa para los pares PRO/REG y COE PRO/COE REG. El campo `% COE` del autor se conserva como identificador para la creación/nombre de las cuentas COE.
