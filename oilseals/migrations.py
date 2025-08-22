import sqlite3
from .database import DB_PATH


def _column_exists(cur: sqlite3.Cursor, table: str, column: str) -> bool:
	cur.execute(f"PRAGMA table_info({table})")
	return any(row[1] == column for row in cur.fetchall())


def _get_create_sql(cur: sqlite3.Cursor, table: str) -> str:
	cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
	row = cur.fetchone()
	return row[0] if row and row[0] else ""


def _recreate_products_with_brand_unique(cur: sqlite3.Cursor) -> None:
	create_sql = _get_create_sql(cur, 'products')
	# If current definition already mentions unique on brand, skip
	if 'brand' in create_sql and 'part_no' in create_sql:
		# Check for old unique pattern including part_no
		old_uniq_on_part = ('UNIQUE' in create_sql and 'part_no' in create_sql) or ('PRIMARY KEY' in create_sql and 'part_no' in create_sql)
	else:
		old_uniq_on_part = False
	if not old_uniq_on_part:
		return

	# Create new table with desired UNIQUE constraint
	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS products_new (
			type TEXT,
			id INTEGER,
			od INTEGER,
			th INTEGER,
			brand TEXT,
			part_no TEXT,
			country_of_origin TEXT,
			notes TEXT,
			quantity INTEGER,
			price REAL,
			location TEXT,
			low_threshold INTEGER,
			warn_threshold INTEGER,
			id_display TEXT,
			od_display TEXT,
			th_display TEXT,
			UNIQUE(type, id, od, th, brand)
		)
		"""
	)
	# Copy data, prefer first row on conflicts
	cur.execute(
		"""
		INSERT OR IGNORE INTO products_new (
			type, id, od, th, brand, part_no, country_of_origin, notes, quantity, price,
			location, low_threshold, warn_threshold, id_display, od_display, th_display
		)
		SELECT type, id, od, th, brand, part_no, country_of_origin, notes, quantity, price,
			location, low_threshold, warn_threshold, id_display, od_display, th_display
		FROM products
		"""
	)
	cur.execute("DROP TABLE products")
	cur.execute("ALTER TABLE products_new RENAME TO products")
	# Helpful index for lookups
	cur.execute("CREATE INDEX IF NOT EXISTS idx_products_type_sizes_brand ON products(type,id,od,th,brand)")


def _ensure_transactions_brand_column(cur: sqlite3.Cursor) -> None:
	if not _column_exists(cur, 'transactions', 'brand'):
		cur.execute("ALTER TABLE transactions ADD COLUMN brand TEXT")
		# Best-effort backfill from products via part_no when available
		try:
			cur.execute(
				"""
				UPDATE transactions AS t
				SET brand = (
					SELECT p.brand FROM products p
					WHERE p.type = t.type AND p.id = t.id_size AND p.od = t.od_size AND p.th = t.th_size
					  AND (t.part_no IS NOT NULL AND t.part_no != '' AND p.part_no = t.part_no)
					LIMIT 1
				)
				WHERE (brand IS NULL OR brand = '')
				"""
			)
		except Exception:
			pass


def run_migrations() -> None:
	con = sqlite3.connect(DB_PATH)
	try:
		cur = con.cursor()
		cur.execute("PRAGMA foreign_keys=OFF")
		_recreate_products_with_brand_unique(cur)
		_ensure_transactions_brand_column(cur)
		con.commit()
	finally:
		con.close()