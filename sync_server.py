

import mysql.connector
import flet as ft
from mysql.connector import Error
import sqlite3
import time

def initialize_local_db(local_db):
    cursor = local_db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY,
            model TEXT,
            serial_number TEXT UNIQUE,
            company TEXT,
            location TEXT,
            purchase_date TEXT,
            status TEXT,
            last_sync TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asset_images (
            id INTEGER PRIMARY KEY,
            asset_id INTEGER,
            image_name TEXT,
            image_data BLOB,
            last_sync TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asset_bills (
            id INTEGER PRIMARY KEY,
            asset_id INTEGER,
            bill_name TEXT,
            bill_data BLOB,
            last_sync TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
        )
    """)
    local_db.commit()

def sync_from_server(local_db, page):
    db_config = {"host": "200.200.200.23", "user": "root", "password": "Pak@123", "database": "asm_sys"}
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        local_cursor = local_db.cursor()

        local_cursor.execute("BEGIN TRANSACTION")
        cursor.execute("SELECT id, model, serial_number, company, location, purchase_date, status FROM assets")
        mysql_assets = cursor.fetchall()

        for asset in mysql_assets:
            mysql_id, model, serial_number, company, location, purchase_date, status = asset
            local_cursor.execute("SELECT id FROM assets WHERE serial_number = ?", (serial_number,))
            existing_asset = local_cursor.fetchone()
            if existing_asset:
                local_id = existing_asset[0]
                local_cursor.execute("""
                    UPDATE assets SET model = ?, company = ?, location = ?, purchase_date = ?, status = ?, last_sync = ?
                    WHERE id = ?
                """, (model, company, location, purchase_date, status, time.strftime("%Y-%m-%d %H:%M:%S"), local_id))
            else:
                local_cursor.execute("""
                    INSERT INTO assets (id, model, serial_number, company, location, purchase_date, status, last_sync)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (mysql_id, model, serial_number, company, location, purchase_date, status, time.strftime("%Y-%m-%d %H:%M:%S")))

            cursor.execute("SELECT id, asset_id, image_name, image_data FROM asset_images WHERE asset_id = %s", (mysql_id,))
            mysql_images = cursor.fetchall()
            local_cursor.execute("SELECT id, image_name FROM asset_images WHERE asset_id = (SELECT id FROM assets WHERE serial_number = ?)", (serial_number,))
            existing_images = {row[1]: row[0] for row in local_cursor.fetchall()}
            for img in mysql_images:
                img_id, asset_id, image_name, image_data = img
                if image_name in existing_images:
                    local_cursor.execute("""
                        UPDATE asset_images SET image_data = ?, last_sync = ? WHERE id = ?
                    """, (image_data, time.strftime("%Y-%m-%d %H:%M:%S"), existing_images[image_name]))
                else:
                    local_cursor.execute("""
                        INSERT INTO asset_images (id, asset_id, image_name, image_data, last_sync)
                        VALUES (?, ?, ?, ?, ?)
                    """, (img_id, local_id if existing_asset else mysql_id, image_name, image_data, time.strftime("%Y-%m-%d %H:%M:%S")))

            cursor.execute("SELECT id, asset_id, bill_name, bill_data FROM asset_bills WHERE asset_id = %s", (mysql_id,))
            mysql_bills = cursor.fetchall()
            local_cursor.execute("SELECT id, bill_name FROM asset_bills WHERE asset_id = (SELECT id FROM assets WHERE serial_number = ?)", (serial_number,))
            existing_bills = {row[1]: row[0] for row in local_cursor.fetchall()}
            for bill in mysql_bills:
                bill_id, asset_id, bill_name, bill_data = bill
                if bill_name in existing_bills:
                    local_cursor.execute("""
                        UPDATE asset_bills SET bill_data = ?, last_sync = ? WHERE id = ?
                    """, (bill_data, time.strftime("%Y-%m-%d %H:%M:%S"), existing_bills[bill_name]))
                else:
                    local_cursor.execute("""
                        INSERT INTO asset_bills (id, asset_id, bill_name, bill_data, last_sync)
                        VALUES (?, ?, ?, ?, ?)
                    """, (bill_id, local_id if existing_asset else mysql_id, bill_name, bill_data, time.strftime("%Y-%m-%d %H:%M:%S")))

        local_db.commit()
        if page:
            page.snack_bar = ft.SnackBar(content=ft.Text("Sync from server completed!"), duration=4000)
            page.snack_bar.open = True
            page.update()
    except Error as e:
        local_db.rollback()
        if page:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Sync error: {e}"), duration=4000)
            page.snack_bar.open = True
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        if 'local_cursor' in locals():
            local_cursor.close()

def sync_to_server(local_db, page):
    db_config = {"host": "200.200.200.23", "user": "root", "password": "Pak@123", "database": "asm_sys"}
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        local_cursor = local_db.cursor()

        cursor.execute("BEGIN")
        local_cursor.execute("SELECT id, model, serial_number, company, location, purchase_date, status, last_sync FROM assets")
        local_assets = local_cursor.fetchall()

        for asset in local_assets:
            local_id, model, serial_number, company, location, purchase_date, status, last_sync = asset
            cursor.execute("SELECT id FROM assets WHERE serial_number = %s", (serial_number,))
            existing_asset = cursor.fetchone()
            if existing_asset:
                mysql_id = existing_asset[0]
                cursor.execute("""
                    UPDATE assets SET model = %s, company = %s, location = %s, purchase_date = %s, status = %s
                    WHERE id = %s
                """, (model, company, location, purchase_date, status, mysql_id))
            else:
                cursor.execute("""
                    INSERT INTO assets (id, model, serial_number, company, location, purchase_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (local_id, model, serial_number, company, location, purchase_date, status))
                mysql_id = local_id

            local_cursor.execute("SELECT id, asset_id, image_name, image_data, last_sync FROM asset_images WHERE asset_id = ?", (local_id,))
            images = local_cursor.fetchall()
            cursor.execute("SELECT id, image_name FROM asset_images WHERE asset_id = %s", (mysql_id,))
            existing_images = {row[0]: row[1] for row in cursor.fetchall()}
            for img in images:
                img_id, asset_id, image_name, image_data, last_sync = img
                if img_id in existing_images:
                    cursor.execute("""
                        UPDATE asset_images SET image_name = %s, image_data = %s WHERE id = %s AND asset_id = %s
                    """, (image_name, image_data, img_id, mysql_id))
                else:
                    cursor.execute("""
                        INSERT INTO asset_images (id, asset_id, image_name, image_data)
                        VALUES (%s, %s, %s, %s)
                    """, (img_id, mysql_id, image_name, image_data))

            local_cursor.execute("SELECT id, asset_id, bill_name, bill_data, last_sync FROM asset_bills WHERE asset_id = ?", (local_id,))
            bills = local_cursor.fetchall()
            cursor.execute("SELECT id, bill_name FROM asset_bills WHERE asset_id = %s", (mysql_id,))
            existing_bills = {row[0]: row[1] for row in cursor.fetchall()}
            for bill in bills:
                bill_id, asset_id, bill_name, bill_data, last_sync = bill
                if bill_id in existing_bills:
                    cursor.execute("""
                        UPDATE asset_bills SET bill_name = %s, bill_data = %s WHERE id = %s AND asset_id = %s
                    """, (bill_name, bill_data, bill_id, mysql_id))
                else:
                    cursor.execute("""
                        INSERT INTO asset_bills (id, asset_id, bill_name, bill_data)
                        VALUES (%s, %s, %s, %s)
                    """, (bill_id, mysql_id, bill_name, bill_data))

        conn.commit()
        if page:
            page.snack_bar = ft.SnackBar(content=ft.Text("Sync to server completed!"), duration=4000)
            page.snack_bar.open = True
            page.update()
    except Error as e:
        conn.rollback()
        if page:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Sync error: {e}"), duration=4000)
            page.snack_bar.open = True
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        if 'local_cursor' in locals():
            local_cursor.close()