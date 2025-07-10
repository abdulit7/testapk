
import os
import flet as ft
import sqlite3
import base64
import time
from datetime import datetime
from sync_server import initialize_local_db, sync_from_server, sync_to_server

class AssetFormPage:
    def __init__(self, page: ft.Page, parent=None, local_db=None):
        if page is None:
            raise ValueError("Page object must be provided to AssetFormPage")
        self.page = page
        self.parent = parent
        self.local_db = local_db or sqlite3.connect("assets.db", check_same_thread=False)
        initialize_local_db(self.local_db)
        self.attached_images = []
        self.attached_bills = []
        self.TEMP_DIR = os.path.join(os.getcwd(), "temp")
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        print(f"Initialized TEMP_DIR: {self.TEMP_DIR}, writable: {os.access(self.TEMP_DIR, os.W_OK)}")

        # Register custom date adapter for SQLite3 compatibility with Python 3.12+
        sqlite3.register_adapter(datetime, lambda d: d.strftime("%Y-%m-%d %H:%M:%S"))
        sqlite3.register_converter("DATETIME", lambda s: datetime.strptime(s.decode(), "%Y-%m-%d %H:%M:%S"))

        self.error_popup = ft.AlertDialog(title=ft.Text("Error"), content=ft.Text(""), actions=[ft.TextButton("OK", on_click=self.close_error_popup)])
        self.success_popup = ft.AlertDialog(title=ft.Text("Success"), content=ft.Text(""), actions=[ft.TextButton("OK", on_click=self.close_success_popup)])
        self.sync_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Sync Status"),
            content=ft.Text(""),
            actions=[ft.TextButton("OK", on_click=self.close_sync_dialog)],
            actions_alignment=ft.MainAxisAlignment.END
        )

        self.asset_model = ft.TextField(label="Model", hint_text="Model", icon=ft.Icons.DEVICE_HUB)
        self.asset_serial_number = ft.TextField(label="Serial Number", hint_text="Enter Serial Number", icon=ft.Icons.DEVICE_HUB)
        self.asset_company = ft.TextField(label="Company Name", hint_text="Enter Company Name", icon=ft.Icons.BUSINESS)
        self.asset_location = ft.TextField(label="Location", hint_text="Enter Location", icon=ft.Icons.LOCATION_ON)
        self.asset_image = ft.FilePicker(on_result=self.handle_asset_image)
        self.asset_image_button = ft.ElevatedButton("Select Image", icon=ft.Icons.IMAGE, on_click=lambda e: self.asset_image.pick_files(allow_multiple=True))
        self.image_display = ft.Image(width=50, height=50, fit="contain")
        self.warning_text = ft.Text("", color="red")
        self.bill_image = ft.FilePicker(on_result=self.handle_bill_image)
        self.asset_bill_button = ft.ElevatedButton("Upload Bill", icon=ft.Icons.ATTACH_FILE, on_click=lambda e: self.bill_image.pick_files(allow_multiple=True))
        self.bill_display = ft.Image(width=50, height=50, fit="contain")
        self.bill_warning_text = ft.Text("", color="red")
        self.purchase_date_button = ft.ElevatedButton("Purchase Date", icon=ft.Icons.DATE_RANGE, on_click=self.open_date_picker)
        self.purchase_date = ft.DatePicker(on_change=self.update_purchase_date)
        self.asset_status = ft.Dropdown(label="Asset Status", border=ft.InputBorder.UNDERLINE, enable_filter=True, editable=True, leading_icon=ft.Icons.SEARCH,
                                       options=[ft.dropdown.Option("Available"), ft.dropdown.Option("Deployed"), ft.dropdown.Option("Disposed/Sold")])

        self.dialog = ft.AlertDialog(modal=True, bgcolor=ft.Colors.RED_100, title=ft.Text("Add/Edit Asset"),
                                    content=ft.Container(width=400, height=600, content=ft.Column(controls=[
                                        self.asset_model, self.asset_serial_number, self.asset_company, self.asset_location,
                                        self.asset_image_button, self.image_display, self.warning_text,
                                        self.asset_bill_button, self.bill_display, self.bill_warning_text,
                                        self.purchase_date_button, self.asset_status
                                    ], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20),
                                    actions=[ft.TextButton("Cancel", on_click=self.close_dialog), ft.TextButton("Save", on_click=self.save_asset)],
                                    actions_alignment=ft.MainAxisAlignment.END)

        self.page.overlay.extend([self.error_popup, self.success_popup, self.sync_dialog, self.asset_image, self.bill_image, self.purchase_date, self.dialog])

    def open_dialog(self):
        self.dialog.open = True
        self.page.update()

    def handle_asset_image(self, e: ft.FilePickerResultEvent):
        self.attached_images = e.files if e.files else []
        self.asset_image_button.text = f"{len(self.attached_images)} image(s) selected."
        self.image_display.src_base64 = None
        self.warning_text.value = ""
        if self.attached_images:
            file = self.attached_images[0]
            try:
                if not self.page.web and hasattr(file, 'path'):
                    with open(file.path, "rb") as f:
                        self.attached_image_bytes = f.read()
                    self.image_display.src_base64 = base64.b64encode(self.attached_image_bytes).decode('utf-8')
                    self.warning_text.value = "Image selected successfully."
                else:
                    self.warning_text.value = "File upload not supported in local mode."
            except Exception as ex:
                self.warning_text.value = f"Error reading file: {ex}"
            self.image_display.update()
        self.warning_text.update()
        self.page.update()

    def handle_bill_image(self, e: ft.FilePickerResultEvent):
        self.attached_bills = e.files if e.files else []
        self.asset_bill_button.text = f"{len(self.attached_bills)} bill(s) selected."
        self.bill_display.src_base64 = None
        self.bill_warning_text.value = ""
        if self.attached_bills:
            file = self.attached_bills[0]
            try:
                if not self.page.web and hasattr(file, 'path'):
                    with open(file.path, "rb") as f:
                        self.attached_bill_bytes = f.read()
                    self.bill_display.src_base64 = base64.b64encode(self.attached_bill_bytes).decode('utf-8')
                    self.bill_warning_text.value = "Bill selected successfully."
                else:
                    self.bill_warning_text.value = "File upload not supported in local mode."
            except Exception as ex:
                self.bill_warning_text.value = f"Error reading file: {ex}"
            self.bill_display.update()
        self.bill_warning_text.update()
        self.page.update()

    def open_date_picker(self, event):
        self.purchase_date.open = True
        self.page.update()

    def update_purchase_date(self, event):
        if event.control.value:
            self.purchase_date_button.text = f"Purchase Date: {event.control.value.strftime('%Y-%m-%d')}"
        else:
            self.purchase_date_button.text = "Purchase Date"
        self.page.update()

    def close_dialog(self, event):
        self.dialog.open = False
        self.reset_fields()
        self.page.update()

    def close_error_popup(self, event):
        self.error_popup.open = False
        self.page.update()

    def close_success_popup(self, event):
        self.success_popup.open = False
        self.dialog.open = False
        self.reset_fields()
        if self.parent and hasattr(self.parent, 'refresh_local_assets'):
            self.parent.refresh_local_assets()
        self.page.update()

    def close_sync_dialog(self, event):
        self.sync_dialog.open = False
        self.page.update()

    def reset_fields(self):
        self.asset_model.value = ""
        self.asset_serial_number.value = ""
        self.asset_company.value = ""
        self.asset_location.value = ""
        self.attached_images = []
        self.attached_bills = []
        self.asset_image_button.text = "Select Image"
        self.asset_bill_button.text = "Upload Bill"
        self.purchase_date_button.text = "Purchase Date"
        self.asset_status.value = "Available"
        self.image_display.src_base64 = None
        self.bill_display.src_base64 = None
        self.warning_text.value = ""
        self.bill_warning_text.value = ""

    def save_asset(self, event):
        model = self.asset_model.value
        serial_number = self.asset_serial_number.value
        company = self.asset_company.value
        location = self.asset_location.value
        status = self.asset_status.value
        purchase_date = self.purchase_date_button.text.replace("Purchase Date: ", "")

        if not all([model, serial_number, company, location, purchase_date]) or purchase_date == "Purchase Date":
            self.error_popup.content = ft.Text("All fields are required.")
            self.error_popup.open = True
            return

        cursor = self.local_db.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("SELECT id FROM assets WHERE serial_number = ?", (serial_number,))
            existing_asset = cursor.fetchone()

            if existing_asset:
                asset_id = existing_asset[0]
                cursor.execute("""
                    UPDATE assets SET model = ?, company = ?, location = ?, purchase_date = ?, status = ?, last_sync = ?
                    WHERE id = ?
                """, (model, company, location, purchase_date, status, time.strftime("%Y-%m-%d %H:%M:%S"), asset_id))
            else:
                cursor.execute("""
                    INSERT INTO assets (model, serial_number, company, location, purchase_date, status, last_sync)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (model, serial_number, company, location, purchase_date, status, time.strftime("%Y-%m-%d %H:%M:%S")))
                asset_id = cursor.lastrowid

            if self.attached_images and hasattr(self, 'attached_image_bytes'):
                cursor.execute("SELECT id, image_name FROM asset_images WHERE asset_id = ?", (asset_id,))
                existing_images = {row[1]: row[0] for row in cursor.fetchall()}
                for img in self.attached_images:
                    if img.name in existing_images:
                        cursor.execute("""
                            UPDATE asset_images SET image_data = ?, last_sync = ? WHERE id = ?
                        """, (self.attached_image_bytes, time.strftime("%Y-%m-%d %H:%M:%S"), existing_images[img.name]))
                    else:
                        cursor.execute("""
                            INSERT INTO asset_images (asset_id, image_name, image_data, last_sync)
                            VALUES (?, ?, ?, ?)
                        """, (asset_id, img.name, self.attached_image_bytes, time.strftime("%Y-%m-%d %H:%M:%S")))

            if self.attached_bills and hasattr(self, 'attached_bill_bytes'):
                cursor.execute("SELECT id, bill_name FROM asset_bills WHERE asset_id = ?", (asset_id,))
                existing_bills = {row[1]: row[0] for row in cursor.fetchall()}
                for bill in self.attached_bills:
                    if bill.name in existing_bills:
                        cursor.execute("""
                            UPDATE asset_bills SET bill_data = ?, last_sync = ? WHERE id = ?
                        """, (self.attached_bill_bytes, time.strftime("%Y-%m-%d %H:%M:%S"), existing_bills[bill.name]))
                    else:
                        cursor.execute("""
                            INSERT INTO asset_bills (asset_id, bill_name, bill_data, last_sync)
                            VALUES (?, ?, ?, ?)
                        """, (asset_id, bill.name, self.attached_bill_bytes, time.strftime("%Y-%m-%d %H:%M:%S")))

            self.local_db.commit()
            self.success_popup.content = ft.Text("Asset saved locally!")
            self.success_popup.open = True
            if self.parent and hasattr(self.parent, 'refresh_local_assets'):
                self.parent.refresh_local_assets()
        except Exception as e:
            self.local_db.rollback()
            self.error_popup.content = ft.Text(f"Error saving locally: {e}")
            self.error_popup.open = True
        finally:
            cursor.close()

    def sync_from_server(self, e):
        sync_from_server(self.local_db, self.page)
        self.sync_dialog.content = ft.Text("Sync from server completed!")
        self.sync_dialog.open = True
        self.page.update()

    def sync_to_server(self, e):
        sync_to_server(self.local_db, self.page)
        self.sync_dialog.content = ft.Text("Sync to server completed!")
        self.sync_dialog.open = True
        self.page.update()