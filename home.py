
import flet as ft
import sqlite3
from assetpage import AssetFormPage
from sync_server import initialize_local_db, sync_from_server, sync_to_server

class Home(ft.Container):
    def __init__(self, page, **kwargs):
        super().__init__(**kwargs)
        self.page = page
        self.padding = 0

        self.local_db = sqlite3.connect("assets.db", check_same_thread=False)
        initialize_local_db(self.local_db)
        self.add_asset_dialog = AssetFormPage(self.page, self, local_db=self.local_db)

        self.asset_button = ft.ElevatedButton(
            text="Asset", icon=ft.Icons.ADD, on_click=lambda e: self.page.go("/asset"),
            bgcolor=ft.Colors.BLUE_500, color=ft.Colors.WHITE, width=300, height=50
        )
        self.component_button = ft.ElevatedButton(
            text="Add Component", icon=ft.Icons.BUILD, bgcolor=ft.Colors.GREEN_500, color=ft.Colors.WHITE,
            width=300, height=50
        )
        self.device_button = ft.ElevatedButton(
            text="Add Device", icon=ft.Icons.DEVICE_HUB, bgcolor=ft.Colors.RED_500, color=ft.Colors.WHITE,
            width=300, height=50
        )
        self.consumable_button = ft.ElevatedButton(
            text="Add Consumable", icon=ft.Icons.SHOPPING_BAG, bgcolor=ft.Colors.ORANGE_500, color=ft.Colors.WHITE,
            width=300, height=50
        )
        self.sync_from_server_button = ft.ElevatedButton(
            text="Sync from Server", icon=ft.Icons.DOWNLOAD, on_click=lambda e: self.sync_from_server(),
            bgcolor=ft.Colors.PURPLE_500, color=ft.Colors.WHITE, width=300, height=50
        )
        self.sync_upload_button = ft.ElevatedButton(
            text="Sync Upload", icon=ft.Icons.UPLOAD, on_click=lambda e: self.sync_to_server(),
            bgcolor=ft.Colors.PINK_500, color=ft.Colors.WHITE, width=300, height=50
        )

        # AlertDialog for sync operations
        self.sync_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Sync Status"),
            content=ft.Text(""),
            actions=[ft.TextButton("OK", on_click=self.close_sync_dialog)],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.overlay.append(self.sync_dialog)

        self.content_area = ft.Container(
            content=ft.Column(
                controls=[
                    self.asset_button, self.component_button, self.device_button, self.consumable_button,
                    self.sync_from_server_button, self.sync_upload_button
                ],
                alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10
            ),
            border=ft.border.all(1, ft.Colors.GREY_400), border_radius=10, padding=10, bgcolor=ft.Colors.WHITE,
            width=320, height=450
        )

        self.content = ft.Column(controls=[self.content_area], expand=True, spacing=0)

    def sync_from_server(self, e=None):
        sync_from_server(self.local_db, self.page)
        self.sync_dialog.content = ft.Text("Sync from server completed!")
        self.sync_dialog.open = True
        self.page.update()

    def sync_to_server(self, e=None):
        sync_to_server(self.local_db, self.page)
        self.sync_dialog.content = ft.Text("Sync to server completed!")
        self.sync_dialog.open = True
        self.page.update()

    def close_sync_dialog(self, e):
        self.sync_dialog.open = False
        self.page.update()