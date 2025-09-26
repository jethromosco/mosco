from ..database import connect_db
from fractions import Fraction


def parse_measurement(value):
    """Convert a string (fraction or decimal) to float for sorting."""
    try:
        s = str(value)
        if "/" in s:
            return float(Fraction(s))
        return float(s)
    except ValueError:
        raise ValueError(f"Invalid measurement: {value}")


class ProductsLogic:
    """Handles all product-related business logic and database operations."""
    
    def __init__(self):
        pass
    
    def get_all_products(self):
        """Retrieve all products from database."""
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT type, id, od, th, brand, part_no, country_of_origin, notes, price
            FROM products
            ORDER BY id ASC, od ASC, th ASC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows
    
    def search_products(self, keyword):
        """Search products based on keyword."""
        all_products = self.get_all_products()
        filtered_products = []
        
        keyword_lower = keyword.lower() if keyword else ""
        
        for row in all_products:
            type_, id_, od, th, brand, part_no, origin, notes, price = row
            
            # Format values for display
            id_str = self.format_value(id_)
            od_str = self.format_value(od)
            th_str = self.format_value(th)
            
            # Create search string (include brand so brand searches match)
            combined = f"{type_} {id_str} {od_str} {th_str} {brand}".lower()

            if keyword_lower in combined:
                # Items display should include brand at the end: TYPE id-od-th BRAND
                item_str = f"{type_.upper()} {id_str}-{od_str}-{th_str} {brand}".strip()
                filtered_products.append({
                    'item': item_str,
                    'brand': brand,
                    'part_no': part_no,
                    'origin': origin,
                    'notes': notes,
                    'price': f"₱{price:.2f}",
                    'raw_data': row
                })
        
        return filtered_products
    
    def format_value(self, val):
        """Format numerical values for display."""
        if isinstance(val, str):
            return val
        return str(int(val)) if float(val).is_integer() else str(val)
    
    def sort_products_data(self, products_data, sort_column, ascending=True):
        """Sort product data by specified column."""
        if sort_column in ("part_no", "notes"):
            return products_data  # Don't sort these columns
        
        def get_sort_key(product):
            if sort_column == "item":
                try:
                    size_str = product['item'].split(" ")[1]
                    parts = size_str.split("-")
                    return tuple(parse_measurement(p) for p in parts)
                except:
                    return (0, 0, 0)
            elif sort_column == "price":
                try:
                    return float(product['price'].replace("₱", "").replace(",", ""))
                except:
                    return 0
            else:
                return product[sort_column].lower() if product[sort_column] else ""
        
        return sorted(products_data, key=get_sort_key, reverse=not ascending)
    
    def get_product_by_selection(self, selected_item_text):
        """Get product data based on selected item text."""
        # This would be used by the form handler to get full product data
        # based on what's selected in the tree
        all_products = self.get_all_products()
        
        for row in all_products:
            type_, id_, od, th, brand, part_no, origin, notes, price = row
            
            id_str = self.format_value(id_)
            od_str = self.format_value(od)
            th_str = self.format_value(th)
            # Match the same Items display format used in search_products
            item_str = f"{type_.upper()} {id_str}-{od_str}-{th_str} {brand}".strip()

            if item_str == selected_item_text:
                return {
                    'type': type_,
                    'id': id_,
                    'od': od,
                    'th': th,
                    'brand': brand,
                    'part_no': part_no,
                    'origin': origin,
                    'notes': notes,
                    'price': price
                }
        
        return None
    
    def add_product(self, product_data):
        """Add a new product to the database."""
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO products (type, id, od, th, brand, part_no, country_of_origin, notes, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_data['type'],
            product_data['id'],
            product_data['od'],
            product_data['th'],
            product_data['brand'],
            product_data['part_no'],
            product_data['origin'],
            product_data['notes'],
            product_data['price']
        ))
        conn.commit()
        conn.close()
    
    def update_product(self, product_id, product_data):
        """Update an existing product in the database."""
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE products 
            SET type=?, id=?, od=?, th=?, brand=?, part_no=?, country_of_origin=?, notes=?, price=?
            WHERE rowid=?
        """, (
            product_data['type'],
            product_data['id'],
            product_data['od'],
            product_data['th'],
            product_data['brand'],
            product_data['part_no'],
            product_data['origin'],
            product_data['notes'],
            product_data['price'],
            product_id
        ))
        conn.commit()
        conn.close()
    
    def delete_product(self, product_id):
        """Delete a product from the database."""
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE rowid=?", (product_id,))
        conn.commit()
        conn.close()
    
    def get_product_by_rowid(self, rowid):
        """Get product by database rowid."""
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT rowid, type, id, od, th, brand, part_no, country_of_origin, notes, price
            FROM products
            WHERE rowid=?
        """, (rowid,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return {
                'rowid': row[0],
                'type': row[1],
                'id': row[2],
                'od': row[3],
                'th': row[4],
                'brand': row[5],
                'part_no': row[6],
                'origin': row[7],
                'notes': row[8],
                'price': row[9]
            }
        return None