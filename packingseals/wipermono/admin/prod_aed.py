import ast
import os
import sqlite3

from ..database import connect_db
from .brand_utils import canonicalize_brand


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


def sanitize_dimension_for_filename(value):
	"""Convert dimension values to filesystem-safe format (e.g. '5/8' -> '5x8')."""
	return str(value).replace('/', 'x').replace(' ', '_')


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
	
	def format_text_fields(self, data):
		"""Apply formatting rules to text fields."""
		formatted_data = data.copy()
		
		# TYPE: no spaces, uppercase
		type_idx = self.FIELDS.index("TYPE")
		formatted_data[type_idx] = data[type_idx].replace(' ', '').upper()

		# BRAND: no spaces, letters and numbers allowed, uppercase
		brand_idx = self.FIELDS.index("BRAND")
		# Keep alphanumeric characters only, remove spaces
		formatted_data[brand_idx] = ''.join(c for c in data[brand_idx] if c.isalnum()).upper()
		
		# Part Num and Notes: all caps
		part_no_idx = self.FIELDS.index("PART_NO")
		notes_idx = self.FIELDS.index("NOTES")
		formatted_data[part_no_idx] = data[part_no_idx].upper()
		formatted_data[notes_idx] = data[notes_idx].upper()

		# ORIGIN: capitalize
		origin_idx = self.FIELDS.index("ORIGIN")
		formatted_data[origin_idx] = data[origin_idx].capitalize()
		
		return formatted_data
	
	def format_number_fields(self, data):
		"""Apply formatting rules to number fields."""
		formatted_data = data.copy()
		
		# ID, OD, TH: numbers, decimals, slashes only (no letters, no spaces)
		for field in ["ID", "OD", "TH"]:
			field_idx = self.FIELDS.index(field)
			value = data[field_idx]
			# Filter out any invalid characters (only allow digits, dots, slashes)
			value = ''.join(c for c in value if c in '0123456789./')
			# Then, validate the structure
			parts = value.split('/')
			for i, part in enumerate(parts):
				if part.count('.') > 1:
					first_dot = part.find('.')
					parts[i] = part[:first_dot+1] + part[first_dot+1:].replace('.', '')
			formatted_data[field_idx] = '/'.join(parts)

		# PRICE: numbers and decimals only (no letters, no spaces)
		price_idx = self.FIELDS.index("PRICE")
		price_val = data[price_idx]
		price_val = ''.join(c for c in price_val if c in '0123456789.')
		if price_val.count('.') > 1:
			first_dot = price_val.find('.')
			price_val = price_val[:first_dot+1] + price_val[first_dot+1:].replace('.', '')
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

		# Canonicalize brand and set origin automatically
		brand_idx = self.FIELDS.index("BRAND")
		origin_idx = self.FIELDS.index("ORIGIN")
		canonical_brand, mapped_origin = canonicalize_brand(validated_data[brand_idx])
		validated_data[brand_idx] = canonical_brand
		if mapped_origin is not None:
			validated_data[origin_idx] = mapped_origin

		# Enforce uniqueness on canonical brand for the same TYPE/ID/OD/TH
		try:
			conn = connect_db()
			cur = conn.cursor()
			cur.execute(
				"""
				SELECT 1 FROM products
				WHERE type=? AND id=? AND od=? AND th=? AND brand=?
				LIMIT 1
				""",
				(
					validated_data[0], validated_data[1], validated_data[2], validated_data[3],
					validated_data[brand_idx]
				),
			)
			dup = cur.fetchone()
			conn.close()
			if dup:
				return False, "This product already exists under the canonical brand."
		except Exception:
			pass
		
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
	
	def update_product(self, data, original_values):
		"""Update an existing product in the database."""
		# Validate data first
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

		# Canonicalize brand and set origin automatically
		brand_idx = self.FIELDS.index("BRAND")
		origin_idx = self.FIELDS.index("ORIGIN")
		canonical_brand, mapped_origin = canonicalize_brand(validated_data[brand_idx])
		validated_data[brand_idx] = canonical_brand
		if mapped_origin is not None:
			validated_data[origin_idx] = mapped_origin

		# Extract original values for record identification
		original_type = str(original_values[0])
		original_id = str(original_values[1])
		original_od = str(original_values[2])
		original_th = str(original_values[3])
		original_brand = str(original_values[4])

		try:
			conn = connect_db()
			cur = conn.cursor()
			
			# First, find the record using the original values
			# Try exact match first
			cur.execute(
				"""
				SELECT rowid FROM products
				WHERE type=? AND id=? AND od=? AND th=? AND brand=?
				""",
				(original_type, original_id, original_od, original_th, original_brand)
			)
			record = cur.fetchone()
			
			# If not found, try with canonicalized original brand
			if not record:
				try:
					canonical_original_brand, _ = canonicalize_brand(original_brand)
					cur.execute(
						"""
						SELECT rowid FROM products
						WHERE type=? AND id=? AND od=? AND th=? AND brand=?
						""",
						(original_type, original_id, original_od, original_th, canonical_original_brand)
					)
					record = cur.fetchone()
				except Exception:
					pass
			
			if not record:
				conn.close()
				return False, f"Product not found: {original_type} {original_id}-{original_od}-{original_th} {original_brand}"
			
			record_id = record[0]
			
			# Check for duplicates (excluding current record)
			# Only check if the key fields have actually changed
			key_changed = (
				validated_data[0] != original_type or
				validated_data[1] != original_id or 
				validated_data[2] != original_od or
				validated_data[3] != original_th or
				validated_data[4] != original_brand
			)
			
			if key_changed:
				cur.execute(
					"""
					SELECT 1 FROM products
					WHERE type=? AND id=? AND od=? AND th=? AND brand=? AND rowid != ?
					LIMIT 1
					""",
					(validated_data[0], validated_data[1], validated_data[2], validated_data[3], validated_data[4], record_id)
				)
				dup = cur.fetchone()
				if dup:
					conn.close()
					return False, "Another product with these details already exists."
			
			# Perform the update
			cur.execute(
				"""
				UPDATE products 
				SET type=?, id=?, od=?, th=?, brand=?, part_no=?, country_of_origin=?, notes=?, price=?
				WHERE rowid=?
				""",
				(
					validated_data[0], validated_data[1], validated_data[2], validated_data[3],
					validated_data[4], validated_data[5], validated_data[6], validated_data[7], 
					validated_data[8], record_id
				)
			)
			
			if cur.rowcount == 0:
				conn.close()
				return False, "No rows were updated. Product may have been deleted."
			
			conn.commit()
			# If key fields changed, update transactions referencing this product
			if key_changed:
				try:
					from .transactions import TransactionsLogic
					trans_logic = TransactionsLogic()
					orig_keys = (original_type, original_id, original_od, original_th, original_brand)
					new_keys = (validated_data[0], validated_data[1], validated_data[2], validated_data[3], validated_data[4])
					# Also pass canonicalized original brand as alt if available
					alt_brand = None
					try:
						canon_orig, _ = canonicalize_brand(original_brand)
						if canon_orig != original_brand:
							alt_brand = canon_orig
					except Exception:
						pass
					trans_logic.update_transactions_for_product(orig_keys, new_keys, alt_original_brand=alt_brand)
					# Also attempt to reliably rename associated product photo files so they remain linked after key change
					try:
						# Import helpers from UI to locate existing photo paths and build safe filenames
						from ..ui.transaction_window import get_photo_path_by_type, create_safe_filename, get_photos_directory
						# Build an original details dict and new details dict
						orig_details = {
							'type': original_type,
							'id': original_id,
							'od': original_od,
							'th': original_th,
							'brand': original_brand
						}
						new_details = {
							'type': validated_data[0],
							'id': validated_data[1],
							'od': validated_data[2],
							'th': validated_data[3],
							'brand': validated_data[4]
						}
						photos_dir = get_photos_directory()
						# Try to find an existing photo for the original details
						src_path = get_photo_path_by_type(orig_details)
						if not src_path:
							# fallback: glob-match any file that begins with the original base
							old_base = f"{original_type}-{sanitize_dimension_for_filename(original_id)}-{sanitize_dimension_for_filename(original_od)}-{sanitize_dimension_for_filename(original_th)}-{original_brand.replace('/', 'x').replace(' ', '_')}"
							for ext in ('.jpg', '.jpeg', '.png'):
								candidate = os.path.join(photos_dir, old_base + ext)
								if os.path.exists(candidate):
									src_path = candidate
									break
						# If we found a source, compute a new safe filename and move it
						if src_path and os.path.exists(src_path):
							# Determine extension
							_, ext = os.path.splitext(src_path)
							new_filename = create_safe_filename(new_details, ext)
							target_path = os.path.join(photos_dir, new_filename)
							try:
								os.replace(src_path, target_path)
							except Exception:
								# If replace fails, attempt copy+remove as fallback
								try:
									import shutil
									shutil.copy2(src_path, target_path)
									os.remove(src_path)
								except Exception:
									pass
					except Exception:
						# non-fatal
							pass
				except Exception:
					# non-fatal: continue
					pass
			
			conn.close()
			return True, "Product updated successfully."
			
		except Exception as e:
			if 'conn' in locals():
				conn.close()
			return False, f"Update failed: {str(e)}"
	
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
			# Initialize with safe defaults
			extracted = ["", "", "", "", "", "", "", "", "0"]
			
			if len(values) >= 1:
				# Parse the combined first field like "TC 1-2-3" into separate components
				combined_field = str(values[0]).strip()
				
				# Split by spaces first to separate TYPE from the measurements
				parts = combined_field.split()
				if len(parts) >= 2:
					# First part is TYPE
					extracted[0] = parts[0]  # TYPE = "TC"
					
					# Second part should be the measurements like "1-2-3"
					measurements = parts[1]
					measurement_parts = measurements.split("-")
					
					if len(measurement_parts) >= 3:
						extracted[1] = measurement_parts[0]  # ID = "1"
						extracted[2] = measurement_parts[1]  # OD = "2"
						extracted[3] = measurement_parts[2]  # TH = "3"
					else:
						# Try to extract what we can
						for i, part in enumerate(measurement_parts):
							if i < 3:
								extracted[1 + i] = part
				else:
					# If parsing fails, put the whole thing in TYPE
					extracted[0] = combined_field

				# If the combined field included a brand (e.g. "TYPE size BRAND"), capture it
				if len(parts) >= 3:
					# brand is the last token
					extracted[4] = parts[-1]
			
			# Handle the rest of the fields based on their expected positions
			# Now that brand is embedded in the combined field, values map as:
			# values[1] -> PART_NO, values[2] -> ORIGIN, values[3] -> NOTES, values[4] -> PRICE
			if len(values) >= 2:
				extracted[5] = str(values[1]).strip()  # PART_NO
			if len(values) >= 3:
				extracted[6] = safe_str_extract(values[2]).strip() if values[2] else ""  # ORIGIN
			if len(values) >= 4:
				extracted[7] = safe_str_extract(values[3]).strip() if values[3] else ""  # NOTES
				
			# Handle price - the products tree stores price at index 4 (0-based)
			if len(values) >= 5:
				try:
					price_str = str(values[4]).replace("₱", "").replace(",", "").strip()
					# Accept numeric strings like '123' or '123.45'
					if price_str:
						# allow leading/trailing whitespace handled above
						# If price contains a trailing '-' (some displays use '₱123-'), strip it
						if price_str.endswith('-'):
							price_str = price_str[:-1].strip()
						# Validate numeric
						try:
							float(price_str)
							extracted[8] = price_str
						except Exception:
							extracted[8] = "0"
					else:
						extracted[8] = "0"
				except Exception:
					extracted[8] = "0"
			
			return tuple(extracted)
			
		except Exception as e:
			return ("", "", "", "", "", "", "", "", "0")
