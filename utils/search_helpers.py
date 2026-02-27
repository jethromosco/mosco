"""
Shared search logic for all MM categories.

This module provides reusable search functions that work across all categories
(oilseals, monoseals, wiperseals, wipermono, etc.) without duplicating logic.

Key functions:
- search_products_with_closest() - Main search function that handles exact + closest size fallback
"""

import sqlite3
from typing import Dict, List, Tuple, Any, Optional


def _is_size_only_search(search_filters: Dict[str, str]) -> bool:
    """
    Check if search contains ONLY size fields (id, od, th).
    
    Returns True if search is limited to size dimensions only,
    False if other filters (type, brand, part_no) are active.
    
    Args:
        search_filters: Dict with keys like 'type', 'id', 'od', 'th', 'brand', 'part_no'
    
    Returns:
        True if ONLY id/od/th have values (and they're all numeric or empty)
    """
    # Get values for each filter type
    type_val = (search_filters.get("type") or "").strip()
    brand_val = (search_filters.get("brand") or "").strip()
    part_no_val = (search_filters.get("part_no") or "").strip()
    id_val = (search_filters.get("id") or "").strip()
    od_val = (search_filters.get("od") or "").strip()
    th_val = (search_filters.get("th") or "").strip()
    
    # Must NOT have type, brand, or part_no searches
    if type_val or brand_val or part_no_val:
        return False
    
    # Must have at least some size search active
    # (if all empty, this should not be treated as size-only search)
    has_size_search = bool(id_val or od_val or th_val)
    
    return has_size_search


def _try_parse_numeric(val: str) -> Optional[float]:
    """
    Try to parse a numeric value from size field.
    
    Handles formats like:
    - "30" -> 30.0
    - "30.5" -> 30.5
    - "30/2" -> 30.0 (takes first part)
    
    Args:
        val: String value from size field
    
    Returns:
        Float value if parseable, None otherwise
    """
    if not val or not isinstance(val, str):
        return None
    
    val = val.strip()
    if not val:
        return None
    
    # Handle slash notation (e.g., "30/2" -> use 30)
    if "/" in val:
        try:
            return float(val.split("/")[0].strip())
        except (ValueError, IndexError):
            return None
    
    # Try direct float conversion
    try:
        return float(val)
    except ValueError:
        return None


def _get_closest_size_products(
    conn: sqlite3.Connection,
    id_search: Optional[float],
    od_search: Optional[float],
    th_search: Optional[float],
    brand_filter: Optional[str] = None
) -> List[Tuple[Any, ...]]:
    """
    Get products within ±1 margin of requested sizes, excluding exact matches.
    
    Margin is STRICTLY ±1 only. Query matches products where:
    - ABS(id - id_search) <= 1 (if id_search provided)
    - ABS(od - od_search) <= 1 (if od_search provided)
    - ABS(th - th_search) <= 1 (if th_search provided)
    - NOT exact match on all provided dimensions
    
    Results sorted by total difference (ascending).
    
    Args:
        conn: SQLite database connection
        id_search: Requested ID value (or None if not searched)
        od_search: Requested OD value (or None if not searched)
        th_search: Requested TH value (or None if not searched)
        brand_filter: Optional brand filter (if originally searched with brand)
    
    Returns:
        List of product tuples: (type, id, od, th, brand, part_no, origin, notes, price)
    """
    if conn is None:
        return []
    
    # At least one size must be specified
    if id_search is None and od_search is None and th_search is None:
        return []
    
    print(f"[SEARCH] Querying closest sizes: ID~{id_search}, OD~{od_search}, TH~{th_search}")
    
    # Build WHERE clause based on what's being searched
    where_parts = []
    params: List[Any] = []
    
    if id_search is not None:
        # Match within ±1 margin
        where_parts.append(f"(CAST(id AS REAL) >= ? AND CAST(id AS REAL) <= ?)")
        params.extend([id_search - 1.0, id_search + 1.0])
    
    if od_search is not None:
        where_parts.append(f"(CAST(od AS REAL) >= ? AND CAST(od AS REAL) <= ?)")
        params.extend([od_search - 1.0, od_search + 1.0])
    
    if th_search is not None:
        where_parts.append(f"(CAST(th AS REAL) >= ? AND CAST(th AS REAL) <= ?)")
        params.extend([th_search - 1.0, th_search + 1.0])
    
    # Add brand filter if specified
    if brand_filter:
        where_parts.append(f"(UPPER(brand) = UPPER(?) OR UPPER(brand) LIKE UPPER(?))")
        params.extend([brand_filter, f"{brand_filter}%"])
    
    # Exclude exact matches
    exclude_parts = []
    if id_search is not None:
        exclude_parts.append(f"CAST(id AS REAL) = ?")
    if od_search is not None:
        exclude_parts.append(f"CAST(od AS REAL) = ?")
    if th_search is not None:
        exclude_parts.append(f"CAST(th AS REAL) = ?")
    
    # Exact match means ALL dimensions match exactly
    exact_match_clause = f"NOT ({' AND '.join(exclude_parts)})" if exclude_parts else "1=1"
    if exclude_parts:
        # Add the values for the NOT() clause
        exact_params = []
        if id_search is not None:
            exact_params.append(id_search)
        if od_search is not None:
            exact_params.append(od_search)
        if th_search is not None:
            exact_params.append(th_search)
        params.extend(exact_params)
    
    where_clause = " AND ".join(where_parts)
    query = f"""
        SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price 
        FROM products 
        WHERE {where_clause} AND {exact_match_clause}
        ORDER BY 
            ABS(CAST(id AS REAL) - ?) + 
            ABS(CAST(od AS REAL) - ?) + 
            ABS(CAST(th AS REAL) - ?)
        ASC
    """
    
    # Add values for ORDER BY calculation
    sort_params = [
        id_search if id_search is not None else 0.0,
        od_search if od_search is not None else 0.0,
        th_search if th_search is not None else 0.0
    ]
    
    try:
        cur = conn.cursor()
        cur.execute(query, params + sort_params)
        rows = cur.fetchall()
        print(f"[SEARCH] Closest results found: {len(rows)}")
        return rows
    except Exception as e:
        print(f"[SEARCH] Error querying closest sizes: {e}")
        return []


def search_products_with_closest(
    conn: sqlite3.Connection,
    search_filters: Dict[str, str],
    exact_results: List[Tuple[Any, ...]],
    brand_filter: Optional[str] = None
) -> Tuple[List[Tuple[Any, ...]], bool, Optional[str]]:
    """
    Unified search that returns exact results or closest alternatives.
    
    Flow:
    1. If exact_results has items -> return exact results, is_closest=False
    2. If exact_results is empty AND search is size-only:
       a. Parse the size values
       b. Call _get_closest_size_products()
       c. If products found -> return them, is_closest=True, label="Exact size not available – CLOSEST SIZE OFFER/S"
    3. If no closest products -> return empty, is_closest=False, label=None
    
    Args:
        conn: SQLite database connection
        search_filters: Dict with 'id', 'od', 'th', 'brand', etc.
        exact_results: Already-fetched exact match results
        brand_filter: Optional brand value (used when querying closest alternatives)
    
    Returns:
        Tuple of (products, is_closest_search, custom_label)
        - products: List of product tuples
        - is_closest_search: True if showing closest alternatives, False if exact/no results
        - custom_label: Custom message for status ("Exact size not available...") or None
    """
    print(f"[SEARCH] Exact results: {len(exact_results)}")
    
    # If we have exact results, return them
    if exact_results:
        return exact_results, False, None
    
    # If no exact results, check if this is a size-only search
    if not _is_size_only_search(search_filters):
        print(f"[SEARCH] Not a size-only search, no fallback to closest")
        return [], False, None
    
    print(f"[SEARCH] Size-only search with no exact matches, checking closest alternatives")
    
    # Parse size values
    id_val = (search_filters.get("id") or "").strip()
    od_val = (search_filters.get("od") or "").strip()
    th_val = (search_filters.get("th") or "").strip()
    
    id_search = _try_parse_numeric(id_val) if id_val else None
    od_search = _try_parse_numeric(od_val) if od_val else None
    th_search = _try_parse_numeric(th_val) if th_val else None
    
    print(f"[SEARCH] Parsed sizes: ID={id_search}, OD={od_search}, TH={th_search}")
    
    # Query closest alternatives
    closest_products = _get_closest_size_products(
        conn,
        id_search,
        od_search,
        th_search,
        brand_filter
    )
    
    if closest_products:
        label = "Exact size not available – CLOSEST SIZE OFFER/S"
        return closest_products, True, label
    
    print(f"[SEARCH] No close offers found")
    return [], False, None

