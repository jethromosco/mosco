from ..database import connect_db
import ast


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
            cur.execute("""
                INSERT INTO products (type, id, od, th, brand, part_no, country_of_origin, notes, price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, validated_data)
            conn.commit()
            conn.close()
            return True, "Product added successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def update_product(self, data, original_values):
        """Update an existing product in the database."""
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
            cur.execute("""
                UPDATE products
                SET type=?, id=?, od=?, th=?, brand=?, part_no=?, country_of_origin=?, notes=?, price=?
                WHERE type=? AND id=? AND od=? AND th=? AND brand=?
            """, validated_data + [original_values[0], original_values[1], original_values[2], original_values[3], original_values[4]])
            conn.commit()
            conn.close()
            return True, "Product updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
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
            return False, f"Database error: {str(e)}"
    
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
