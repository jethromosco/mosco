from datetime import datetime
from ..database import connect_db
import re
from fractions import Fraction


def center_window(win, width, height):
	"""Center a window on the screen"""
	win.update_idletasks()
	x = (win.winfo_screenwidth() // 2) - (width // 2)
	y = (win.winfo_screenheight() // 2) - (height // 2)
	win.geometry(f"{width}x{height}+{x}+{y}")


def format_currency(val):
	"""Format a value as currency with peso symbol"""
	return f"\u20B1{val:.2f}"


def parse_date(text):
	"""Parse date string in MM/DD/YY format"""
	return datetime.strptime(text, "%m/%d/%y")


def _parse_size_component(value):
	"""Parse a size string that may contain fractions into a float."""
	if value is None:
		return None
	text = str(value).strip()
	if text == "":
		return None
	# e.g., "1 1/2" or "1/2" or "1.5"
	try:
		if ' ' in text and '/' in text:
			parts = text.split()
			if len(parts) == 2:
				whole, frac = parts
				return float(int(whole) + float(Fraction(frac)))
			else:
				return float(Fraction(text.replace(' ', '')))
		if '/' in text:
			return float(Fraction(text))
		return float(text)
	except Exception:
		# Fall back to original text if parsing fails
		return None


def _normalize_number_for_db(value_str):
	"""Convert an input size string to a number suitable for DB comparison (int if near int)."""
	val = _parse_size_component(value_str)
	if val is None:
		return None
	if abs(val - round(val)) < 1e-9:
		return int(round(val))
	return float(val)


def _resolve_part_no(item_type, id_size, od_size, th_size, brand):
	"""Find part number for the given product selection. Returns empty string if not found."""
	try:
		item_type = (item_type or "").strip().upper()
		brand = (brand or "").strip().upper()
		id_val = _normalize_number_for_db(id_size)
		od_val = _normalize_number_for_db(od_size)
		th_val = _normalize_number_for_db(th_size)
		if None in (id_val, od_val, th_val):
			return ""
		conn = connect_db()
		cur = conn.cursor()
		cur.execute(
			"""
			SELECT part_no FROM products
			WHERE type = ? AND id = ? AND od = ? AND th = ? AND brand = ?
			LIMIT 1
			""",
			(item_type, id_val, od_val, th_val, brand),
		)
		row = cur.fetchone()
		conn.close()
		return row[0] if row and row[0] is not None else ""
	except Exception:
		return ""


class TransactionLogic:
	"""Handles all transaction-related business logic"""
	
	FIELDS = ["Type", "ID", "OD", "TH", "Brand", "Name", "Quantity", "Price", "Stock"]
	
	@staticmethod
	def get_record_by_id(rowid):
		"""Retrieve a transaction record by its row ID, attaching brand via products."""
		try:
			conn = connect_db()
			cur = conn.cursor()
			cur.execute(
				"""
				SELECT t.rowid, t.date, t.type, t.id_size, t.od_size, t.th_size,
				       COALESCE(t.brand, COALESCE(p.brand, '')) AS brand, t.name, t.quantity, t.price, t.is_restock
				FROM transactions t
				LEFT JOIN products p ON t.type = p.type AND t.id_size = p.id AND t.od_size = p.od AND t.th_size = p.th
				WHERE t.rowid = ?
				""",
				(rowid,)
			)
			record = cur.fetchone()
			conn.close()
			
			if record:
				# Convert to object-like structure to match old code expectations
				class RecordObj:
					def __init__(self, data):
						self.rowid = data[0]
						self.date = data[1]
						self.type = data[2]
						self.id_size = data[3]
						self.od_size = data[4]
						self.th_size = data[5]
						self.brand = data[6] or ""
						self.name = data[7]
						self.quantity = data[8]
						self.price = data[9]
						self.is_restock = data[10]
				
				return RecordObj(record)
			return None
		except Exception:
			return None
	
	@staticmethod
	def delete_transactions(item_ids):
		"""Delete multiple transactions by their IDs"""
		try:
			conn = connect_db()
			cur = conn.cursor()
			for item_id in item_ids:
				cur.execute("DELETE FROM transactions WHERE rowid=?", (item_id,))
			conn.commit()
			conn.close()
			return True
		except Exception:
			return False
	
	@staticmethod
	def validate_product_exists(item_type, id_size, od_size, th_size, brand):
		"""Check if a product exists in the products table, matching brand and sizes."""
		try:
			item_type = (item_type or "").strip().upper()
			brand = (brand or "").strip().upper()
			id_val = _normalize_number_for_db(id_size)
			od_val = _normalize_number_for_db(od_size)
			th_val = _normalize_number_for_db(th_size)
			if None in (id_val, od_val, th_val):
				return False
			conn = connect_db()
			cur = conn.cursor()
			cur.execute(
				"""
				SELECT 1 FROM products
				WHERE type = ? AND id = ? AND od = ? AND th = ? AND brand = ?
				LIMIT 1
				""",
				(item_type, id_val, od_val, th_val, brand),
			)
			res = cur.fetchone()
			conn.close()
			return res is not None
		except Exception:
			return False
	
	@staticmethod
	def save_transaction(mode, data, rowid=None):
		"""Save a transaction (add or edit)"""
		try:
			conn = connect_db()
			cur = conn.cursor()
			
			if mode == "Add":
				cur.execute(
					"""
					INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, part_no, name, quantity, price, is_restock)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
					""",
					(
						data['date'], data['item_type'], data['id_size'], data['od_size'],
						data['th_size'], data['brand'], data['part_no'], data['name'], data['quantity'], data['price'], data['is_restock']
					),
				)
			else:  # Edit
				cur.execute(
					"""
					UPDATE transactions SET date=?, type=?, id_size=?, od_size=?, th_size=?, brand=?, part_no=?, name=?, quantity=?, price=?, is_restock=?
					WHERE rowid=?
					""",
					(
						data['date'], data['item_type'], data['id_size'], data['od_size'],
						data['th_size'], data['brand'], data['part_no'], data['name'], data['quantity'], data['price'], data['is_restock'], rowid
					),
				)
			
			conn.commit()
			conn.close()
			return True
		except Exception:
			return False
	
	@staticmethod
	def save_fabrication_transaction(data):
		"""Save a fabrication transaction (creates two records)"""
		try:
			conn = connect_db()
			cur = conn.cursor()
			
			# Insert restock record
			cur.execute(
				"""
				INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, part_no, name, quantity, price, is_restock)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					data['date'], data['item_type'], data['id_size'], data['od_size'],
					data['th_size'], data['brand'], data['part_no'], data['name'], data['qty_restock'], 0, 1
				),
			)
			
			# Insert sale record
			cur.execute(
				"""
				INSERT INTO transactions (date, type, id_size, od_size, th_size, brand, part_no, name, quantity, price, is_restock)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					data['date'], data['item_type'], data['id_size'], data['od_size'],
					data['th_size'], data['brand'], data['part_no'], data['name'], -data['qty_customer'], data['price'], 0
				),
			)
			
			conn.commit()
			conn.close()
			return True
		except Exception:
			return False
	
	@staticmethod
	def validate_transaction_data(trans_type, form_data):
		"""Validate transaction data based on transaction type"""
		errors = []
		
		# Common validation for required fields
		if not all([form_data.get('item_type'), form_data.get('id_size'), form_data.get('od_size'), 
				  form_data.get('th_size'), form_data.get('brand'), form_data.get('name')]):
			errors.append("Type, ID, OD, TH, Brand, and Name must be filled.")
		
		if trans_type in ["Restock", "Sale"]:
			if not form_data.get('quantity') or not form_data.get('price'):
				errors.append("Quantity and Price must be filled.")
			else:
				try:
					qty = int(form_data['quantity'])
					price = float(form_data['price'])
					if qty <= 0 or price <= 0:
						errors.append("Quantity and Price must be greater than 0.")
				except (ValueError, TypeError):
					errors.append("Quantity must be a valid integer and Price must be a valid number.")
		
		elif trans_type == "Actual":
			if not form_data.get('stock'):
				errors.append("Stock must be filled.")
			else:
				try:
					int(form_data['stock'])
				except (ValueError, TypeError):
					errors.append("Stock must be a valid integer.")
		
		elif trans_type == "Fabrication":
			if not all([form_data.get('qty_restock'), form_data.get('qty_customer'), form_data.get('price')]):
				errors.append("All Fabrication fields must be filled.")
			else:
				try:
					qty_restock = int(form_data['qty_restock'])
					qty_customer = int(form_data['qty_customer'])
					price = float(form_data['price'])
					if qty_customer > qty_restock:
						errors.append("Qty Sold cannot exceed Qty Restock.")
				except (ValueError, TypeError):
					errors.append("Fabrication quantities must be valid integers and price must be a valid number.")
		
		return errors
	
	@staticmethod
	def prepare_transaction_data(trans_type, form_data):
		"""Prepare transaction data for saving"""
		try:
			date = parse_date(form_data['date']).strftime("%Y-%m-%d")
			item_type = form_data['item_type'].strip().upper()
			id_size = form_data['id_size'].strip()
			od_size = form_data['od_size'].strip()
			th_size = form_data['th_size'].strip()
			brand = form_data['brand'].strip().upper()
			name = form_data['name'].strip().upper()
			
			data = {
				'date': date,
				'trans_type': trans_type,
				'item_type': item_type,
				'id_size': id_size,
				'od_size': od_size,
				'th_size': th_size,
				'brand': brand,
				'part_no': _resolve_part_no(item_type, id_size, od_size, th_size, brand),
				'name': name
			}
			
			if trans_type in ["Restock", "Sale"]:
				qty = abs(int(form_data['quantity']))
				price = float(form_data['price'])
				is_restock = 1 if trans_type == "Restock" else 0
				if is_restock == 0:
					qty = -qty
				
				data.update({
					'quantity': qty,
					'price': price,
					'is_restock': is_restock
				})
			
			elif trans_type == "Actual":
				qty = int(form_data['stock'])
				data.update({
					'quantity': qty,
					'price': 0,
					'is_restock': 2
				})
			
			elif trans_type == "Fabrication":
				qty_restock = int(form_data['qty_restock'])
				qty_customer = int(form_data['qty_customer'])
				price = float(form_data['price'])
				
				data.update({
					'qty_restock': qty_restock,
					'qty_customer': qty_customer,
					'price': price
				})
			
			return data
		except Exception:
			return None