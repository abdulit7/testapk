import os
import flet as ft
import sqlite3
import base64
import time
from sync_server import initialize_local_db

class AssetEditPage:
    def __init__(self, page: ft.Page, parent=None, asset_id=None, local_db=None):
        if page is None:
            raise ValueError("Page object must be provided to AssetEditPage")
        self.page = page
        self.parent = parent
        self.asset_id = asset_id
        self.local_db = local_db or sqlite3.connect("assets.db", check_same_thread=False)
        initialize_local_db(self.local_db)
        self.TEMP_DIR = os.path.join(os.getcwd(), "temp")
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        print(f"Initialized TEMP_DIR: {self.TEMP_DIR}, writable: {os.access(self.TEMP_DIR, os.W_OK)}")

        self.error_popup = ft.AlertDialog(title=ft.Text("Error"), content=ft.Text(""), actions=[ft.TextButton("OK", on_click=self.close_error_popup)])
        self.success_popup = ft.AlertDialog(title=ft.Text("Success"), content=ft.Text(""), actions=[ft.TextButton("OK", on_click=self.close_success_popup)])

        self.asset_model = ft.TextField(label="Model", hint_text="Model", icon=ft.Icons.DEVICE_HUB, disabled=True)
        self.asset_serial_number = ft.TextField(label="Serial Number", hint_text="Serial Number", icon=ft.Icons.DEVICE_HUB, disabled=True)
        self.asset_location = ft.TextField(label="Location", hint_text="Location", icon=ft.Icons.LOCATION_ON)
        self.asset_image = ft.FilePicker(on_result=self.handle_asset_image)
        self.asset_image_button = ft.ElevatedButton("Select Image", icon=ft.Icons.IMAGE, on_click=lambda e: self.asset_image.pick_files(allow_multiple=False))
        self.image_display = ft.Image(width=50, height=50, fit="contain")
        self.warning_text = ft.Text("", color="red")
        self.asset_bill = ft.FilePicker(on_result=self.handle_bill_image)
        self.asset_bill_button = ft.ElevatedButton("Upload Bill", icon=ft.Icons.ATTACH_FILE, on_click=lambda e: self.asset_bill.pick_files(allow_multiple=False))
        self.bill_display = ft.Image(width=50, height=50, fit="contain")
        self.bill_warning_text = ft.Text("", color="red")

        # Initialize attached_images and attached_bills as empty lists
        self.attached_images = []
        self.attached_bills = []

        self.dialog = ft.AlertDialog(
            modal=True, bgcolor=ft.Colors.YELLOW_100, title=ft.Text("Edit Asset"),
            content=ft.Container(width=400, height=500, content=ft.Column(controls=[
                self.asset_model, self.asset_serial_number, self.asset_location,
                self.asset_image_button, self.image_display, self.warning_text,
                self.asset_bill_button, self.bill_display, self.bill_warning_text
            ], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20),
            actions=[ft.TextButton("Cancel", on_click=self.close_dialog), ft.TextButton("Save", on_click=self.save_asset)],
            actions_alignment=ft.MainAxisAlignment.END)

        self.page.overlay.extend([self.error_popup, self.success_popup, self.asset_image, self.asset_bill, self.dialog])

        if self.asset_id:
            self.load_asset_data()

    def open_dialog(self):
        if self.asset_id:
            self.load_asset_data()
            self.dialog.open = True
            self.page.update()

    def load_asset_data(self):
        """Fetch and display asset details from the local database."""
        if not self.asset_id:
            self.error_popup.content = ft.Text("No asset ID provided for editing.")
            self.error_popup.open = True
            return
        cursor = self.local_db.cursor()
        try:
            cursor.execute("SELECT model, serial_number, location FROM assets WHERE id = ?", (self.asset_id,))
            asset = cursor.fetchone()
            if asset:
                self.asset_model.value = asset[0] or ""
                self.asset_serial_number.value = asset[1] or ""
                self.asset_location.value = asset[2] or ""
                print(f"Loaded asset: model={self.asset_model.value}, serial={self.asset_serial_number.value}, location={self.asset_location.value}")
            else:
                self.error_popup.content = ft.Text(f"Asset with ID {self.asset_id} not found.")
                self.error_popup.open = True
            self.page.update()
        except Exception as e:
            self.error_popup.content = ft.Text(f"Error loading asset: {e}")
            self.error_popup.open = True
        finally:
            cursor.close()

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
                    # Handle mobile case where path might not be available
                    if file and hasattr(file, 'bytes'):
                        self.attached_image_bytes = file.bytes
                        self.image_display.src_base64 = base64.b64encode(self.attached_image_bytes).decode('utf-8')
                        self.warning_text.value = "Image selected successfully (mobile)."
                    else:
                        self.warning_text.value = "Failed to load image on mobile."
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
                    if file and hasattr(file, 'bytes'):
                        self.attached_bill_bytes = file.bytes
                        self.bill_display.src_base64 = base64.b64encode(self.attached_bill_bytes).decode('utf-8')
                        self.bill_warning_text.value = "Bill selected successfully (mobile)."
                    else:
                        self.bill_warning_text.value = "Failed to load bill on mobile."
            except Exception as ex:
                self.bill_warning_text.value = f"Error reading file: {ex}"
            self.bill_display.update()
        self.bill_warning_text.update()
        self.page.update()

    def close_dialog(self, event):
        self.dialog.open = False
        self.attached_images = []
        self.attached_bills = []
        self.asset_image_button.text = "Select Image"
        self.asset_bill_button.text = "Upload Bill"
        self.image_display.src_base64 = None
        self.bill_display.src_base64 = None
        self.warning_text.value = ""
        self.bill_warning_text.value = ""
        self.close_success_popup(event)
        self.page.update()

    def close_error_popup(self, event):
        self.error_popup.open = False
        self.dialog.open = False
        self.page.update()

    def close_success_popup(self, event):
        self.success_popup.open = False
        self.dialog.open = False
        self.attached_images = []
        self.attached_bills = []
        self.asset_image_button.text = "Select Image"
        self.asset_bill_button.text = "Upload Bill"
        self.image_display.src_base64 = None
        self.bill_display.src_base64 = None
        self.warning_text.value = ""
        self.bill_warning_text.value = ""
        if self.parent and hasattr(self.parent, 'refresh_local_assets'):
            self.parent.refresh_local_assets()
        self.page.update()

    def save_asset(self, event):
        if not self.asset_id:
            self.error_popup.content = ft.Text("No asset selected for editing.")
            self.error_popup.open = True
            self.page.update()
            return

        cursor = self.local_db.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            # Update asset location
            cursor.execute("UPDATE assets SET location = ? WHERE id = ?", (self.asset_location.value or "", self.asset_id))
            print(f"Updated location for asset_id {self.asset_id} to {self.asset_location.value}")

            if self.attached_images and hasattr(self, 'attached_image_bytes'):
                # Find the existing image for this asset_id
                cursor.execute("SELECT id, image_name FROM asset_images WHERE asset_id = ? LIMIT 1", (self.asset_id,))
                existing_image = cursor.fetchone()
                img_name = os.path.basename(self.attached_images[0].name) if self.attached_images else "updated_image.jpg"
                if existing_image:
                    image_id, existing_name = existing_image
                    # Update the existing image with the new data
                    cursor.execute("""
                        UPDATE asset_images SET image_data = ?, image_name = ?, last_sync = ? WHERE id = ?
                    """, (self.attached_image_bytes, img_name, time.strftime("%Y-%m-%d %H:%M:%S"), image_id))
                    print(f"Updated existing image {img_name} for asset_id {self.asset_id} with id {image_id}")
                else:
                    # Insert new image only if no existing image found
                    cursor.execute("""
                        INSERT INTO asset_images (asset_id, image_name, image_data, last_sync)
                        VALUES (?, ?, ?, ?)
                    """, (self.asset_id, img_name, self.attached_image_bytes, time.strftime("%Y-%m-%d %H:%M:%S")))
                    print(f"Inserted new image {img_name} for asset_id {self.asset_id}")

            if self.attached_bills and hasattr(self, 'attached_bill_bytes'):
                cursor.execute("SELECT id, bill_name FROM asset_bills WHERE asset_id = ? LIMIT 1", (self.asset_id,))
                existing_bill = cursor.fetchone()
                bill_name = os.path.basename(self.attached_bills[0].name) if self.attached_bills else "updated_bill.pdf"
                if existing_bill:
                    bill_id, existing_name = existing_bill
                    cursor.execute("""
                        UPDATE asset_bills SET bill_data = ?, bill_name = ?, last_sync = ? WHERE id = ?
                    """, (self.attached_bill_bytes, bill_name, time.strftime("%Y-%m-%d %H:%M:%S"), bill_id))
                else:
                    cursor.execute("""
                        INSERT INTO asset_bills (asset_id, bill_name, bill_data, last_sync)
                        VALUES (?, ?, ?, ?)
                    """, (self.asset_id, bill_name, self.attached_bill_bytes, time.strftime("%Y-%m-%d %H:%M:%S")))

            self.local_db.commit()
            # Show success popup before closing the dialog
            self.success_popup.content = ft.Text("Asset updated locally!")
            self.success_popup.open = True
            self.page.update()
            # Ensure parent refreshes the table
            if self.parent and hasattr(self.parent, 'refresh_local_assets'):
                self.parent.refresh_local_assets()
        except Exception as e:
            self.local_db.rollback()
            self.error_popup.content = ft.Text(f"Error updating asset: {e}")
            self.error_popup.open = True
            print(f"Save failed: {e}")
        finally:
            cursor.close()
            # Close the dialog after the popup is shown
            self.dialog.open = False
            self.page.update()
