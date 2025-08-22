from ..database import connect_db
import ast
import sqlite3


def parse_measurement(value):
	"""
	Accept decimal numbers or multiple slash-separated numbers (e.g. '5/8.5').
	Returns list of floats for validation.
	"""
	try:
		parts = value.split("/")
		return [float(p) for p in parts if p.strip() != ""]
	except ValueError:
		raise ValueError(f"Invalid measurement: {value}")


def safe_str_extract(value):
	"""Safely extract string from various data types."""
	if isinstance(value, list):
		return ", ".join(str(v) for v in value)
	try:
		parsed = ast.literal_eval(value)
		if isinstance(parsed, list):
			return ", ".join(str(v) for v in parsed)
	except Exception:
		pass
	return str(value)


class ProductFormLogic:
	"""Handles all product form-related business logic and database operations."""
	
	FIELDS = ["TYPE", "ID", "OD", "TH", "BRAND", "PART_NO", "ORIGIN", "NOTES", "PRICE"]
	
	def __init__(self):
		pass
	
	def validate_required_fields(self, data):
		"""Validate that required fields are filled."""
		if not all(data[i] for i in range(5)):  # TYPE, ID, OD, TH, BRAND
			return False, "Please fill all required fields (TYPE, ID, OD, TH, BRAND)"
		return True, ""
	
	def validate_measurements(self, data):
		"""Validate ID, OD, TH measurements."""
		try:
			for field in ["ID", "OD", "TH"]:
				field_idx = self.FIELDS.index(field)
				parse_measurement(data[field_idx])  # will raise if invalid
			return True, ""
		except ValueError as e:
			return False, str(e)
	
	def validate_price(self, price_str):
		"""Validate price field."""
		try:
			price = float(price_str)
			return True, price, ""
		except ValueError:
			return False, 0, "Please enter a valid price"
	
	def parse_item_string(self, item_str):
		"""Parse item string into components."""
		try:
			type_, size = item_str.split(" ", 1)
			id_str, od_str, th_str = size.split("-")
			return type_, id_str, od_str, th_str
		except ValueError:
			return "", "", "", ""
	
	def format_text_fields(self, data):
		"""Apply formatting rules to text fields."""
		formatted_data = data.copy()
		
		# TYPE and BRAND: uppercase letters only
		type_idx = self.FIELDS.index("TYPE")
		brand_idx = self.FIELDS.index("BRAND")
		formatted_data[type_idx] = ''.join(filter(str.isalpha, data[type_idx])).upper()
		formatted_data[brand_idx] = ''.join(filter(str.isalpha, data[brand_idx])).upper()
		
		# ORIGIN: capitalize
		origin_idx = self.FIELDS.index("ORIGIN")
		formatted_data[origin_idx] = data[origin_idx].capitalize()
		
		return formatted_data
	
	def format_number_fields(self, data):
		"""Apply formatting rules to number fields."""
		formatted_data = data.copy()
		
		# ID, OD, TH: numbers, decimals, slashes only
		for field in ["ID", "OD", "TH"]:
			field_idx = self.FIELDS.index(field)
			allowed_chars = "0123456789./"
			formatted_data[field_idx] = ''.join(c for c in data[field_idx] if c in allowed_chars)
		
		# PRICE: numbers and decimals only
		price_idx = self.FIELDS.index("PRICE")
		price_val = ''.join(c for c in data[price_idx] if c in '0123456789.')
		formatted_data[price_idx] = price_val
		
		return formatted_data
	
	def _generate_fallback_part_no(self, data):
		"""Generate a user-transparent reference if PART_NO is empty and a duplicate needs uniqueness."""
		type_, id_, od, th, brand, part_no, origin, notes, price = data
		base = f"{brand}-{type_}-{id_}-{od}-{th}"
		return base
	
	def add_product(self, data):
		"""Add a new product to the database."""
		# Validate data
		is_valid, error_msg = self.validate_required_fields(data)
		if not is_valid:
			return False, error_msg
		
		is_valid, error_msg = self.validate_measurements(data)
		if not is_valid:
			return False, error_msg
		
		price_idx = self.FIELDS.index("PRICE")
		is_valid, price, error_msg = self.validate_price(data[price_idx])
		if not is_valid:
			return False, error_msg
		
		# Update price in data
		validated_data = data.copy()
		validated_data[price_idx] = price
		
		try:
			conn = connect_db()
			cur = conn.cursor()
			cur.execute(
				"""
				INSERT INTO products (type, id, od, th, brand, part_no, country_of_origin, notes, price)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",
				(
					validated_data[0], validated_data[1], validated_data[2], validated_data[3],
					validated_data[4], validated_data[5], validated_data[6], validated_data[7], validated_data[8]
				)
			)
			conn.commit()
			conn.close()
			return True, "Product saved."
		except sqlite3.IntegrityError:
			# Likely duplicate on (type,id,od,th,part_no)
			if not validated_data[5]:  # PART_NO empty -> assign a reference and retry
				try:
					fallback = self._generate_fallback_part_no(validated_data)
					conn = connect_db()
					cur = conn.cursor()
					cur.execute(
						"""
						INSERT INTO products (type, id, od, th, brand, part_no, country_of_origin, notes, price)
						VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
						""",
						(
							validated_data[0], validated_data[1], validated_data[2], validated_data[3],
							validated_data[4], fallback, validated_data[6], validated_data[7], validated_data[8]
						)
					)
					conn.commit()
					conn.close()
					return True, "Product saved. We've added a reference number for this item."
				except Exception:
					return False, "This product already exists. Please change either Brand or details to make it unique."
			return False, "This product already exists. Please change either Part No. or Brand to make it unique."
		except Exception:
			return False, "We couldn't save this product. Please check your entries and try again."
	
	def update_product(self, product_id, product_data):
		"""Update an existing product in the database."""
		conn = connect_db()
		cur = conn.cursor()
		try:
			cur.execute(
				"""
				UPDATE products 
				SET type=?, id=?, od=?, th=?, brand=?, part_no=?, country_of_origin=?, notes=?, price=?
				WHERE rowid=?
				""",
				(
					product_data['type'], product_data['id'], product_data['od'], product_data['th'], product_data['brand'],
					product_data['part_no'], product_data['origin'], product_data['notes'], product_data['price'], product_id
				)
			)
			conn.commit()
			conn.close()
			return True, "Product updated."
		except sqlite3.IntegrityError:
			conn.close()
			return False, "Another product with these details already exists. Please adjust the reference (Part No.) or brand."
		except Exception:
			conn.close()
			return False, "We couldn't update this product. Please check your entries and try again."
	
	def delete_product(self, type_, id_str, od_str, th_str, brand):
		"""Delete a product from the database."""
		try:
			conn = connect_db()
			cur = conn.cursor()
			cur.execute(
				"DELETE FROM products WHERE type=? AND id=? AND od=? AND th=? AND brand=?",
				(type_, id_str, od_str, th_str, brand)
			)
			conn.commit()
			conn.close()
			return True, "Product deleted successfully"
		except Exception as e:
			return False, f"We couldn't delete this product. Please try again."
	
	def extract_values_from_tree_selection(self, values):
		"""Extract and format values from treeview selection."""
		try:
			item_str = values[0]
			type_, id_str, od_str, th_str = self.parse_item_string(item_str)
			
			brand = values[1] if len(values) > 1 else ""
			part_no = values[2] if len(values) > 2 else ""
			origin = safe_str_extract(values[3]) if len(values) > 3 else ""
			notes = safe_str_extract(values[4]) if len(values) > 4 else ""
			price = values[5] if len(values) > 5 else "0"
			
			# Clean price
			price = price.replace("₱", "").replace(",", "")
			
			return (type_, id_str, od_str, th_str, brand, part_no, origin, notes, price)
		except (IndexError, ValueError):
			return ("", "", "", "", "", "", "", "", "0")
