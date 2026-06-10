from dataclasses import dataclass, field
from difflib import SequenceMatcher

# Known financial/domain column aliases — columns with different names but same meaning
_COLUMN_ALIASES: list[set[str]] = [
    {"close", "adj_close", "adjusted_close", "closing_price"},
    {"open", "open_price", "opening_price"},
    {"date", "candle_date", "trade_date", "timestamp", "record_date"},
    {"symbol", "ticker", "instrument", "security_id", "stock_symbol"},
    {"volume", "vol", "trading_volume"},
    {"high", "high_price", "day_high"},
    {"low",  "low_price",  "day_low"},
]

# Columns that carry no SQL meaning and waste tokens
_AUDIT_COLUMNS = {
    "created_at", "updated_at", "deleted_at", "modified_at",
    "created_by", "updated_by", "created_date", "modified_date",
}


@dataclass
class TableGroup:
    name: str           # group identifier (primary table name)
    primary: str        # most likely authoritative table
    variants: list[str]
    note: str


@dataclass
class ColumnEquivalence:
    table1: str
    col1: str
    table2: str
    col2: str


@dataclass
class SchemaMetadata:
    compressed: dict[str, list[str]]         # table → columns (no audit cols, no types)
    groups: list[TableGroup]                  # clusters of similar-named tables
    shared_columns: dict[str, list[str]]      # column → tables it appears in (3+ tables)
    equivalences: list[ColumnEquivalence]     # cross-table semantic aliases


# ── Helpers ──────────────────────────────────────────────────────────────────

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _find_groups(tables: list[str]) -> list[TableGroup]:
    visited: set[str] = set()
    groups: list[TableGroup] = []

    for t1 in tables:
        if t1 in visited:
            continue
        cluster = [t1]
        for t2 in tables:
            if t2 == t1 or t2 in visited:
                continue
            if _similarity(t1, t2) >= 0.70:
                cluster.append(t2)

        if len(cluster) > 1:
            visited.update(cluster)
            primary = min(cluster, key=len)   # shortest name = most likely base table
            variants = [t for t in cluster if t != primary]
            groups.append(TableGroup(
                name=primary,
                primary=primary,
                variants=variants,
                note=(
                    f"'{primary}' is likely the primary table. "
                    f"Variants ({', '.join(variants)}) may be duplicates or older versions."
                ),
            ))

    return groups


def _find_shared_columns(schema: dict[str, list[str]]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for table, cols in schema.items():
        for col in cols:
            index.setdefault(col, []).append(table)
    # Only flag columns appearing in 3+ tables — likely join keys
    return {col: tables for col, tables in index.items() if len(tables) >= 3}


def _find_equivalences(schema: dict[str, list[str]]) -> list[ColumnEquivalence]:
    equivs: list[ColumnEquivalence] = []
    for alias_set in _COLUMN_ALIASES:
        # Which table uses which alias from this set
        table_col: dict[str, str] = {}
        for table, cols in schema.items():
            for col in cols:
                if col.lower() in alias_set:
                    table_col[table] = col

        pairs = list(table_col.items())
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                t1, c1 = pairs[i]
                t2, c2 = pairs[j]
                if c1.lower() != c2.lower():   # different names = true equivalence
                    equivs.append(ColumnEquivalence(t1, c1, t2, c2))

    return equivs


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_schema(raw: dict[str, list[str]]) -> SchemaMetadata:
    """
    raw: {table_name: [column_name, ...]} from information_schema
    Returns a SchemaMetadata with compression, groups, join keys, and aliases.
    """
    compressed = {
        table: [c for c in cols if c.lower() not in _AUDIT_COLUMNS]
        for table, cols in raw.items()
    }
    return SchemaMetadata(
        compressed=compressed,
        groups=_find_groups(list(raw.keys())),
        shared_columns=_find_shared_columns(compressed),
        equivalences=_find_equivalences(compressed),
    )
