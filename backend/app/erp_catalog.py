"""Prebuilt catalog of sample ERP tables (SAP + Oracle)."""

from .models import ErpInfo, ErpTableInfo

_CATALOG: dict[str, dict] = {
    "sap": {
        "erp_name": "SAP",
        "tables": {
            "MARA": "General Material Master Data",
            "KNA1": "Customer Master (General Data)",
            "VBAK": "Sales Document: Header Data",
            "BKPF": "Accounting Document Header",
        },
    },
    "oracle": {
        "erp_name": "Oracle EBS",
        "tables": {
            "HZ_PARTIES": "Trading Community Parties (Customers/Orgs)",
            "MTL_SYSTEM_ITEMS_B": "Inventory Item Master",
            "GL_JE_HEADERS": "General Ledger Journal Entry Headers",
            "AP_INVOICES_ALL": "Payables Invoices",
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
                description=desc,
            )
            for table, desc in data["tables"].items()
        ]
        result.append(
            ErpInfo(erp_id=erp_id, erp_name=data["erp_name"], tables=tables)
        )
    return result


def get_table_description(erp_id: str, table: str) -> str | None:
    erp = _CATALOG.get(erp_id)
    if not erp:
        return None
    return erp["tables"].get(table)


def erp_name(erp_id: str) -> str | None:
    erp = _CATALOG.get(erp_id)
    return erp["erp_name"] if erp else None
