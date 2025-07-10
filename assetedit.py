
import os
os.environ["FLET_SECRET_KEY"] = "mysecret123"
import flet as ft
import sqlite3
import time
from pathlib import Path
from sync_server import initialize_local_db

class AssetEditPage:
    def __init__(self, page: ft.Page, parent=None, asset_id=None, local_db=None):
        if page is None:
            raise ValueError("Page object must be provided to AssetEditPage")
        self.page = page
        self.parent = parent
        self.asset_id = asset_id

        db_path = os.path.join(str(Path.home()), "assets.db")
        self.local_db = local_db or sqlite3.connect(db_path, check_same_thread=False)
        initialize_local_db(self.local_db)

        self.error_popup = ft.AlertDialog(title=ft.Text("Error"), content=ft.Text(""), actions=[ft.TextButton("OK", on_click=self.close_error_popup)])
        self.success_popup = ft.AlertDialog(title=ft.Text("Success"), content=ft.Text(""), actions=[ft.TextButton("OK", on_click=self.close_success_popup)])

        self.asset_model = ft.TextField(label="Model", hint_text="Model", icon=ft.Icons.DEVICE_HUB, disabled=True)
        self.asset_serial_number = ft.TextField(label="Serial Number", hint_text="Serial Number", icon=ft.Icons.DEVICE_HUB, disabled=True)
        self.asset_location = ft.TextField(label="Location", hint_text="Location", icon=ft.Icons.LOCATION_ON)

        self.asset_image_button = ft.ElevatedButton("Select Image", icon=ft.Icons.IMAGE)
        self.asset_bill_button = ft.ElevatedButton("Upload Bill", icon=ft.Icons.ATTACH_FILE)
        self.warning_text = ft.Text("", color="red")
        self.bill_warning_text = ft.Text("", color="red")

        self.dialog = ft.AlertDialog(
            modal=True, bgcolor=ft.Colors.YELLOW_100, title=ft.Text("Edit Asset"),
            content=ft.Container(width=400, height=500, content=ft.Column(controls=[
                self.asset_model, self.asset_serial_number, self.asset_location,
                self.asset_image_button, self.warning_text,
                self.asset_bill_button, self.bill_warning_text
            ], spacing=15, scroll=ft.ScrollMode.AUTO), padding=20),
            actions=[ft.TextButton("Cancel", on_click=self.close_dialog), ft.TextButton("Save", on_click=self.save_asset)],
            actions_alignment=ft.MainAxisAlignment.END)

        self.page.overlay.extend([self.error_popup, self.success_popup, self.dialog])
        self.page.secret_key = "mysecret123"

        if self.asset_id:
            self.load_asset_data()

    def open_dialog(self):
        if self.asset_id:
            self.load_asset_data()
            self.dialog.open = True
            self.page.update()

    def load_asset_data(self):
        cursor = self.local_db.cursor()
        try:
            cursor.execute("SELECT model, serial_number, location FROM assets WHERE id = ?", (self.asset_id,))
            asset = cursor.fetchone()
            if asset:
                self.asset_model.value = asset[0] or ""
                self.asset_serial_number.value = asset[1] or ""
                self.asset_location.value = asset[2] or ""
            else:
                self.error_popup.content = ft.Text(f"Asset with ID {self.asset_id} not found.")
                self.error_popup.open = True
            self.page.update()
        except Exception as e:
            self.error_popup.content = ft.Text(f"Error loading asset: {e}")
            self.error_popup.open = True
        finally:
            cursor.close()

    def save_asset(self, event):
        if not self.asset_id:
            self.error_popup.content = ft.Text("No asset selected for editing.")
            self.error_popup.open = True
            self.page.update()
            return

        cursor = self.local_db.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("UPDATE assets SET location = ? WHERE id = ?", (self.asset_location.value or "", self.asset_id))
            self.local_db.commit()
            self.success_popup.content = ft.Text("Asset updated locally!")
            self.success_popup.open = True
            self.page.update()
        except Exception as e:
            self.local_db.rollback()
            self.error_popup.content = ft.Text(f"Error updating asset: {e}")
            self.error_popup.open = True
        finally:
            cursor.close()
            self.dialog.open = False
            self.page.update()

    def close_dialog(self, event):
        self.dialog.open = False
        self.asset_image_button.text = "Select Image"
        self.asset_bill_button.text = "Upload Bill"
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
        self.asset_image_button.text = "Select Image"
        self.asset_bill_button.text = "Upload Bill"
        self.warning_text.value = ""
        self.bill_warning_text.value = ""
        if self.parent and hasattr(self.parent, 'refresh_local_assets'):
            self.parent.refresh_local_assets()
        self.page.update()
