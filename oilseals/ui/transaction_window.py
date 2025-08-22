import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from PIL import Image
from customtkinter import CTkImage
from typing import Any, Dict, List, Tuple
import os
from ..database import connect_db


def get_existing_image_base(details: Dict[str, Any]) -> str:
	return f"{details['type']}-{details['id']}-{details['od']}-{details['th']}"


def load_transactions_records(details: Dict[str, Any]) -> List[Tuple[Any, ...]]:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				SELECT t.date, t.name, t.quantity, t.price, t.is_restock, p.brand
				FROM transactions t
				JOIN products p ON t.type = p.type AND t.id_size = p.id AND t.od_size = p.od AND t.th_size = p.th
				WHERE t.type=? AND t.id_size=? AND t.od_size=? AND t.th_size=?
				ORDER BY t.date ASC
			""",
			(details["type"], details["id"], details["od"], details["th"]),
		)
		rows = cur.fetchall()
	return rows


def get_thresholds(details: Dict[str, Any]) -> Tuple[int, int]:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""SELECT low_threshold, warn_threshold FROM products
				 WHERE type=? AND id=? AND od=? AND th=? AND brand=?""",
			(details["type"], details["id"], details["od"], details["th"], details["brand"]),
		)
		row = cur.fetchone()
	low = row[0] if row and row[0] is not None else 0
	warn = row[1] if row and row[1] is not None else 5
	return int(low), int(warn)


def get_location_and_notes(details: Dict[str, Any]) -> Tuple[str, str]:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				SELECT location, notes FROM products
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		row = cur.fetchone()
	if not row:
		return "Drawer 1", ""
	return (row[0] or "Drawer 1", row[1] or "")


def update_location(details: Dict[str, Any], new_location: str) -> None:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				UPDATE products SET location=?
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(new_location.strip(), details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		conn.commit()


def update_price(details: Dict[str, Any], new_price: float) -> None:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				UPDATE products SET price=?
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(new_price, details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		conn.commit()


def update_notes(details: Dict[str, Any], new_notes: str) -> None:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				UPDATE products SET notes=?
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(new_notes.strip(), details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		conn.commit()


def update_thresholds(details: Dict[str, Any], low: int, warn: int) -> None:
	with connect_db() as conn:
		cur = conn.cursor()
		cur.execute(
			"""
				UPDATE products SET low_threshold=?, warn_threshold=?
				WHERE type=? AND id=? AND od=? AND th=? AND part_no=?
			""",
			(low, warn, details["type"], details["id"], details["od"], details["th"], details["part_no"]),
		)
		conn.commit()


def summarize_running_stock(rows: List[Tuple[Any, ...]]) -> List[Tuple[str, Any, Any, Any, Any, Any, int]]:
	"""Return list of tuples for display, computing running stock with reset on Actual (is_restock==2)."""
	running_stock = 0
	result = []
	for row in rows:
		date, name, qty, price, is_restock, brand = row
		if is_restock == 2:
			running_stock = int(qty)
		else:
			running_stock += int(qty)
		date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d/%y")
		qty_restock = ""
		cost = ""
		price_str = ""
		display_qty = ""
		if is_restock == 1:
			qty_restock = qty
			cost = f"₱{float(price):.2f}"
		elif is_restock == 0:
			display_qty = abs(int(qty))
			price_str = f"₱{float(price):.2f}"
		result.append((date_str, qty_restock, cost, name, display_qty, price_str, running_stock))
	return list(reversed(result))
