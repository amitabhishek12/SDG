"""Offline catalog of standard ERP tables (SAP + Oracle) with field definitions.

Each table carries its real-world fields (name, key flag, ERP-style data type,
length, short note). This is the primary, network-free source for ERP schemas;
the LLM is only used as a fallback when a requested table is not in the catalog.
"""

from difflib import get_close_matches

from .models import ErpField, ErpInfo, ErpTableInfo


def _f(name: str, key: bool, dtype: str, length: int, note: str = "") -> dict:
    return {"name": name, "key": key, "dtype": dtype, "length": length, "note": note}


# Structure: erp_id -> {erp_name, tables: {TABLE: {description, fields: [...]}}}
_CATALOG: dict[str, dict] = {
    "sap": {
        "erp_name": "SAP",
        "tables": {
            "MARA": {
                "description": "General Material Master Data",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("MATNR", True, "CHAR", 18, "Material number"),
                    _f("ERSDA", False, "DATS", 8, "Created on"),
                    _f("ERNAM", False, "CHAR", 12, "Created by"),
                    _f("MTART", False, "CHAR", 4, "Material type"),
                    _f("MBRSH", False, "CHAR", 1, "Industry sector"),
                    _f("MATKL", False, "CHAR", 9, "Material group"),
                    _f("MEINS", False, "UNIT", 3, "Base unit of measure"),
                    _f("BRGEW", False, "QUAN", 13, "Gross weight"),
                    _f("NTGEW", False, "QUAN", 13, "Net weight"),
                    _f("GEWEI", False, "UNIT", 3, "Weight unit"),
                    _f("VOLUM", False, "QUAN", 13, "Volume"),
                ],
            },
            "MAKT": {
                "description": "Material Descriptions",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("MATNR", True, "CHAR", 18, "Material number"),
                    _f("SPRAS", True, "LANG", 1, "Language key"),
                    _f("MAKTX", False, "CHAR", 40, "Material description"),
                    _f("MAKTG", False, "CHAR", 40, "Material description (upper)"),
                ],
            },
            "MARC": {
                "description": "Plant Data for Material",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("MATNR", True, "CHAR", 18, "Material number"),
                    _f("WERKS", True, "CHAR", 4, "Plant"),
                    _f("PSTAT", False, "CHAR", 15, "Maintenance status"),
                    _f("EKGRP", False, "CHAR", 3, "Purchasing group"),
                    _f("DISMM", False, "CHAR", 2, "MRP type"),
                    _f("DISPO", False, "CHAR", 3, "MRP controller"),
                    _f("BESKZ", False, "CHAR", 1, "Procurement type"),
                ],
            },
            "MARD": {
                "description": "Storage Location Data for Material",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("MATNR", True, "CHAR", 18, "Material number"),
                    _f("WERKS", True, "CHAR", 4, "Plant"),
                    _f("LGORT", True, "CHAR", 4, "Storage location"),
                    _f("LABST", False, "QUAN", 13, "Unrestricted stock"),
                    _f("INSME", False, "QUAN", 13, "Stock in quality inspection"),
                    _f("SPEME", False, "QUAN", 13, "Blocked stock"),
                ],
            },
            "MBEW": {
                "description": "Material Valuation",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("MATNR", True, "CHAR", 18, "Material number"),
                    _f("BWKEY", True, "CHAR", 4, "Valuation area"),
                    _f("BWTAR", True, "CHAR", 10, "Valuation type"),
                    _f("LBKUM", False, "QUAN", 13, "Total valuated stock"),
                    _f("SALK3", False, "CURR", 13, "Value of total stock"),
                    _f("VPRSV", False, "CHAR", 1, "Price control indicator"),
                    _f("VERPR", False, "CURR", 11, "Moving average price"),
                    _f("STPRS", False, "CURR", 11, "Standard price"),
                    _f("WAERS", False, "CUKY", 5, "Currency key"),
                ],
            },
            "KNA1": {
                "description": "Customer Master (General Data)",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("KUNNR", True, "CHAR", 10, "Customer number"),
                    _f("LAND1", False, "CHAR", 3, "Country key"),
                    _f("NAME1", False, "CHAR", 35, "Name"),
                    _f("ORT01", False, "CHAR", 35, "City"),
                    _f("PSTLZ", False, "CHAR", 10, "Postal code"),
                    _f("REGIO", False, "CHAR", 3, "Region"),
                    _f("STRAS", False, "CHAR", 35, "Street and house number"),
                    _f("TELF1", False, "CHAR", 16, "Telephone number"),
                    _f("SPRAS", False, "LANG", 1, "Language key"),
                ],
            },
            "LFA1": {
                "description": "Vendor Master (General Section)",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("LIFNR", True, "CHAR", 10, "Vendor number"),
                    _f("LAND1", False, "CHAR", 3, "Country key"),
                    _f("NAME1", False, "CHAR", 35, "Name"),
                    _f("ORT01", False, "CHAR", 35, "City"),
                    _f("PSTLZ", False, "CHAR", 10, "Postal code"),
                    _f("REGIO", False, "CHAR", 3, "Region"),
                    _f("STRAS", False, "CHAR", 35, "Street and house number"),
                    _f("STCD1", False, "CHAR", 16, "Tax number 1"),
                    _f("SPRAS", False, "LANG", 1, "Language key"),
                ],
            },
            "VBAK": {
                "description": "Sales Document: Header Data",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("VBELN", True, "CHAR", 10, "Sales document"),
                    _f("ERDAT", False, "DATS", 8, "Created on"),
                    _f("ERNAM", False, "CHAR", 12, "Created by"),
                    _f("AUART", False, "CHAR", 4, "Sales document type"),
                    _f("NETWR", False, "CURR", 15, "Net value of order"),
                    _f("WAERK", False, "CUKY", 5, "Document currency"),
                    _f("VKORG", False, "CHAR", 4, "Sales organization"),
                    _f("VTWEG", False, "CHAR", 2, "Distribution channel"),
                    _f("KUNNR", False, "CHAR", 10, "Sold-to party"),
                ],
            },
            "VBAP": {
                "description": "Sales Document: Item Data",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("VBELN", True, "CHAR", 10, "Sales document"),
                    _f("POSNR", True, "NUMC", 6, "Sales document item"),
                    _f("MATNR", False, "CHAR", 18, "Material number"),
                    _f("ARKTX", False, "CHAR", 40, "Item description"),
                    _f("KWMENG", False, "QUAN", 15, "Order quantity"),
                    _f("VRKME", False, "UNIT", 3, "Sales unit"),
                    _f("NETWR", False, "CURR", 15, "Net value"),
                    _f("WAERK", False, "CUKY", 5, "Document currency"),
                ],
            },
            "EKKO": {
                "description": "Purchasing Document Header",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("EBELN", True, "CHAR", 10, "Purchasing document number"),
                    _f("BUKRS", False, "CHAR", 4, "Company code"),
                    _f("BSTYP", False, "CHAR", 1, "Purchasing document category"),
                    _f("BSART", False, "CHAR", 4, "Purchasing document type"),
                    _f("AEDAT", False, "DATS", 8, "Created on"),
                    _f("ERNAM", False, "CHAR", 12, "Created by"),
                    _f("LIFNR", False, "CHAR", 10, "Vendor number"),
                    _f("WAERS", False, "CUKY", 5, "Currency key"),
                ],
            },
            "EKPO": {
                "description": "Purchasing Document Item",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("EBELN", True, "CHAR", 10, "Purchasing document number"),
                    _f("EBELP", True, "NUMC", 5, "Item number"),
                    _f("MATNR", False, "CHAR", 18, "Material number"),
                    _f("TXZ01", False, "CHAR", 40, "Short text"),
                    _f("WERKS", False, "CHAR", 4, "Plant"),
                    _f("MENGE", False, "QUAN", 13, "Quantity"),
                    _f("MEINS", False, "UNIT", 3, "Order unit"),
                    _f("NETPR", False, "CURR", 11, "Net price"),
                    _f("NETWR", False, "CURR", 15, "Net order value"),
                ],
            },
            "BKPF": {
                "description": "Accounting Document Header",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("BUKRS", True, "CHAR", 4, "Company code"),
                    _f("BELNR", True, "CHAR", 10, "Accounting document number"),
                    _f("GJAHR", True, "NUMC", 4, "Fiscal year"),
                    _f("BLART", False, "CHAR", 2, "Document type"),
                    _f("BLDAT", False, "DATS", 8, "Document date"),
                    _f("BUDAT", False, "DATS", 8, "Posting date"),
                    _f("WAERS", False, "CUKY", 5, "Currency key"),
                    _f("USNAM", False, "CHAR", 12, "User name"),
                ],
            },
            "BSEG": {
                "description": "Accounting Document Segment (Line Items)",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("BUKRS", True, "CHAR", 4, "Company code"),
                    _f("BELNR", True, "CHAR", 10, "Accounting document number"),
                    _f("GJAHR", True, "NUMC", 4, "Fiscal year"),
                    _f("BUZEI", True, "NUMC", 3, "Line item number"),
                    _f("SHKZG", False, "CHAR", 1, "Debit/credit indicator"),
                    _f("DMBTR", False, "CURR", 13, "Amount in local currency"),
                    _f("WRBTR", False, "CURR", 13, "Amount in document currency"),
                    _f("HKONT", False, "CHAR", 10, "G/L account"),
                    _f("KOSTL", False, "CHAR", 10, "Cost center"),
                ],
            },
            "T001": {
                "description": "Company Codes",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("BUKRS", True, "CHAR", 4, "Company code"),
                    _f("BUTXT", False, "CHAR", 25, "Company name"),
                    _f("ORT01", False, "CHAR", 25, "City"),
                    _f("LAND1", False, "CHAR", 3, "Country key"),
                    _f("WAERS", False, "CUKY", 5, "Currency key"),
                    _f("SPRAS", False, "LANG", 1, "Language key"),
                ],
            },
            "CEPC": {
                "description": "Profit Center Master Data",
                "fields": [
                    _f("MANDT", True, "NUMC", 3, "Client"),
                    _f("PRCTR", True, "CHAR", 10, "Profit center"),
                    _f("DATBI", True, "DATS", 8, "Valid to date"),
                    _f("KOKRS", True, "CHAR", 4, "Controlling area"),
                    _f("DATAB", False, "DATS", 8, "Valid from date"),
                    _f("VERAK", False, "CHAR", 20, "Person responsible"),
                    _f("WAERS", False, "CUKY", 5, "Currency key"),
                ],
            },
        },
    },
    "oracle": {
        "erp_name": "Oracle EBS",
        "tables": {
            "HZ_PARTIES": {
                "description": "Trading Community Parties (Customers/Orgs)",
                "fields": [
                    _f("PARTY_ID", True, "INT", 15, "Party identifier"),
                    _f("PARTY_NUMBER", False, "CHAR", 30, "Party number"),
                    _f("PARTY_NAME", False, "CHAR", 360, "Party name"),
                    _f("PARTY_TYPE", False, "CHAR", 30, "Party type"),
                    _f("ADDRESS1", False, "CHAR", 240, "Address line 1"),
                    _f("CITY", False, "CHAR", 60, "City"),
                    _f("POSTAL_CODE", False, "CHAR", 60, "Postal code"),
                    _f("COUNTRY", False, "CHAR", 60, "Country"),
                ],
            },
            "MTL_SYSTEM_ITEMS_B": {
                "description": "Inventory Item Master",
                "fields": [
                    _f("INVENTORY_ITEM_ID", True, "INT", 15, "Item identifier"),
                    _f("ORGANIZATION_ID", True, "INT", 15, "Organization id"),
                    _f("SEGMENT1", False, "CHAR", 40, "Item number"),
                    _f("DESCRIPTION", False, "CHAR", 240, "Item description"),
                    _f("PRIMARY_UOM_CODE", False, "CHAR", 3, "Primary UOM"),
                    _f("ITEM_TYPE", False, "CHAR", 30, "Item type"),
                ],
            },
            "GL_JE_HEADERS": {
                "description": "General Ledger Journal Entry Headers",
                "fields": [
                    _f("JE_HEADER_ID", True, "INT", 15, "Journal header id"),
                    _f("LEDGER_ID", False, "INT", 15, "Ledger id"),
                    _f("JE_CATEGORY", False, "CHAR", 25, "Journal category"),
                    _f("JE_SOURCE", False, "CHAR", 25, "Journal source"),
                    _f("NAME", False, "CHAR", 100, "Journal name"),
                    _f("CURRENCY_CODE", False, "CHAR", 15, "Currency code"),
                    _f("DEFAULT_EFFECTIVE_DATE", False, "DATS", 8, "Effective date"),
                ],
            },
            "AP_INVOICES_ALL": {
                "description": "Payables Invoices",
                "fields": [
                    _f("INVOICE_ID", True, "INT", 15, "Invoice identifier"),
                    _f("VENDOR_ID", False, "INT", 15, "Vendor id"),
                    _f("INVOICE_NUM", False, "CHAR", 50, "Invoice number"),
                    _f("INVOICE_AMOUNT", False, "DEC", 15, "Invoice amount"),
                    _f("INVOICE_CURRENCY_CODE", False, "CHAR", 15, "Currency code"),
                    _f("INVOICE_DATE", False, "DATS", 8, "Invoice date"),
                    _f("PAYMENT_STATUS_FLAG", False, "CHAR", 1, "Payment status"),
                ],
            },
        },
    },
}


def list_erps() -> list[ErpInfo]:
    result: list[ErpInfo] = []
    for erp_id, data in _CATALOG.items():
        tables = [
            ErpTableInfo(
                erp_id=erp_id,
                erp_name=data["erp_name"],
                table=table,
                description=meta["description"],
            )
            for table, meta in data["tables"].items()
        ]
        result.append(
            ErpInfo(erp_id=erp_id, erp_name=data["erp_name"], tables=tables)
        )
    return result


def erp_name(erp_id: str) -> str | None:
    erp = _CATALOG.get(erp_id)
    return erp["erp_name"] if erp else None


def get_table_meta(erp_id: str, table: str) -> dict | None:
    erp = _CATALOG.get(erp_id)
    if not erp:
        return None
    return erp["tables"].get(table.upper())


def get_table_description(erp_id: str, table: str) -> str | None:
    meta = get_table_meta(erp_id, table)
    return meta["description"] if meta else None


def get_catalog_fields(erp_id: str, table: str) -> list[ErpField] | None:
    """Return the field list for a catalog table, or None if not catalogued."""
    meta = get_table_meta(erp_id, table)
    if not meta:
        return None
    return [
        ErpField(
            field_name=f["name"],
            key=f["key"],
            data_type=f["dtype"],
            length=f["length"],
            notes=f["note"] or None,
        )
        for f in meta["fields"]
    ]


def search_tables(erp_id: str, query: str, limit: int = 5) -> dict:
    """Resolve a table name against the catalog.

    Returns a dict with:
      - status: "exact" | "suggestions" | "none"
      - table/description: present when status == "exact"
      - matches: list of {table, description} when status == "suggestions"
    """
    erp = _CATALOG.get(erp_id)
    if not erp:
        return {"status": "none", "matches": []}

    q = query.strip().upper()
    tables = erp["tables"]

    if q in tables:
        return {
            "status": "exact",
            "table": q,
            "description": tables[q]["description"],
            "matches": [],
        }

    # Substring matches first (e.g. "MAR" -> MARA, MARC, MARD).
    substring = [t for t in tables if q and q in t]
    # Fuzzy matches on table names.
    fuzzy = get_close_matches(q, list(tables.keys()), n=limit, cutoff=0.4)
    # Description matches for word-based searches (e.g. "customer").
    desc_hits = [
        t
        for t, meta in tables.items()
        if q and q.lower() in meta["description"].lower()
    ]

    ordered: list[str] = []
    for t in substring + fuzzy + desc_hits:
        if t not in ordered:
            ordered.append(t)
    ordered = ordered[:limit]

    if not ordered:
        return {"status": "none", "matches": []}

    return {
        "status": "suggestions",
        "matches": [
            {"table": t, "description": tables[t]["description"]} for t in ordered
        ],
    }
