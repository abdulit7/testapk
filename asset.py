import os
import flet as ft
import sqlite3
from assetpage import AssetFormPage
from assetedit import AssetEditPage
from sync_server import initialize_local_db, sync_from_server, sync_to_server

class AssetPage(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()

        self.page = page
        self.page.title = "Asset Management"
    
        self.page.window.width = 365
        self.page.window.height = 600
        self.page.window.min_width = 360
        self.page.window.min_height = 600
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.WHITE

        self.local_db = sqlite3.connect(os.path.join(os.getcwd(), "assets.db"), check_same_thread=False)
        initialize_local_db(self.local_db)
        
        self.add_asset_dialog = AssetFormPage(self.page, self, local_db=self.local_db)
        
        self.page.appbar = ft.AppBar(
            title=ft.Text("Asset Management", size=15, weight="bold"),
            bgcolor=ft.Colors.GREEN_300,
            color=ft.Colors.WHITE,
            center_title=True,
            automatically_imply_leading=False,
        )

        self.page.bottom_appbar = ft.BottomAppBar(
            bgcolor=ft.Colors.BLUE,
            shape=ft.NotchShape.CIRCULAR,
            content=ft.Row(
                controls=[
                    ft.PopupMenuButton(
                        items=[
                            ft.PopupMenuItem(text="Option 1"),
                            ft.PopupMenuItem(text="Option 2"),
                            ft.PopupMenuItem(text="Option 3"),
                            ft.PopupMenuItem(text="Option 4"),
                        ],
                        icon=ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.WHITE),
                        tooltip="Menu Options",
                    ),
                    ft.IconButton(icon=ft.Icons.SEARCH, icon_color=ft.Colors.WHITE, tooltip="Search"),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.Icons.FAVORITE, icon_color=ft.Colors.WHITE, tooltip="Favorites"),
                ],
            ),
        )

        self.expand = True
        self.asset_add = []

        self.add_asset_button = ft.ElevatedButton(
            text="Add Asset",
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.TEAL_600,
            color=ft.Colors.WHITE,
            elevation=4,
            on_click=lambda e: self.add_asset_dialog.open_dialog(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                overlay_color=ft.Colors.TEAL_700
            ),
            width=120,
            height=40,
        )

        self.Home_button = ft.ElevatedButton(
            text="HOME",
            icon=ft.Icons.HOME,
            bgcolor=ft.Colors.GREEN_400,
            color=ft.Colors.WHITE,
            elevation=4,
            on_click=lambda e: self.page.go("/"),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                overlay_color=ft.Colors.TEAL_700
            ),
            width=120,
            height=40,
        )

        # Initialize local asset table with selected columns
        self.local_asset_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Model", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)),
                ft.DataColumn(ft.Text("Serial Number", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)),
                ft.DataColumn(ft.Text("Location", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)),
                ft.DataColumn(ft.Text("Edit", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.BLUE_GREY_300),
            vertical_lines=ft.border.BorderSide(1, ft.Colors.BLUE_GREY_300),
            column_spacing=5,
        )

        self.sync_from_server_button = ft.ElevatedButton(
            text="Sync from Server",
            icon=ft.Icons.DOWNLOAD,
            bgcolor=ft.Colors.PURPLE_500,
            color=ft.Colors.WHITE,
            on_click=lambda e: self.sync_from_server(),
            width=150,
            height=40,
        )

        self.sync_to_server_button = ft.ElevatedButton(
            text="Sync to Server",
            icon=ft.Icons.UPLOAD,
            bgcolor=ft.Colors.PINK_500,
            color=ft.Colors.WHITE,
            on_click=lambda e: self.sync_to_server(),
            width=150,
            height=40,
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

        self.content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.Home_button, self.add_asset_button],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=10,
                    ),
                    ft.Text("Local Assets", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.local_asset_table,
                        expand=True,
                        width=self.page.window.width - 20,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                        padding=5,
                        border_radius=10,
                        bgcolor=ft.Colors.LIGHT_BLUE_100,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_300),
                    ),
                    ft.Row(
                        controls=[self.sync_from_server_button, self.sync_to_server_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                ],
                expand=True,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=10,
        )

        # Load initial local assets
        self.refresh_local_assets()
        self.page.add(self)
        self.page.update()

    def refresh_local_assets(self):
        cursor = self.local_db.cursor()
        try:
            cursor.execute("SELECT id, model, serial_number, company, location, purchase_date, status, last_sync FROM assets")
            assets = cursor.fetchall()
            print(f"SQLite3 query returned {len(assets)} assets: {[row[2] for row in assets]}")

            self.local_asset_table.rows.clear()

            if not assets:
                self.local_asset_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("No local assets found in SQLite3.")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                            ft.DataCell(ft.Text("")),
                        ]
                    )
                )
            else:
                for i, asset in enumerate(assets):
                    asset_id, model, serial_number, company, location, purchase_date, status, last_sync = asset
                    edit_button = ft.IconButton(
                        icon=ft.Icons.EDIT,
                        icon_color=ft.Colors.BLUE,
                        bgcolor=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.Colors.BLUE_500, ft.Colors.BLUE_700]
                        ),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            overlay_color=ft.Colors.BLUE_400
                        ),
                        tooltip="Edit Asset",
                        on_click=lambda e, aid=asset_id: self.open_edit_dialog(aid)
                    )
                    self.local_asset_table.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(model or "N/A", color=ft.Colors.BLUE_GREY_800, size=12)),
                                ft.DataCell(ft.Text(serial_number or "N/A", color=ft.Colors.BLUE_GREY_800, size=12)),
                                ft.DataCell(ft.Text(location or "N/A", color=ft.Colors.BLUE_GREY_800, size=12)),
                                ft.DataCell(ft.Container(content=edit_button, alignment=ft.alignment.center)),
                            ],
                            color=ft.Colors.WHITE if i % 2 == 0 else ft.Colors.BLUE_GREY_50
                        )
                    )

            self.page.update()
            print(f"Refreshed asset table with {len(self.local_asset_table.rows)} rows")
        except Exception as e:
            print(f"Error fetching local asset data from SQLite3: {e}")
            self.local_asset_table.rows.clear()
            self.local_asset_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"Error: {e}")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                    ]
                )
            )
            self.page.update()
        finally:
            cursor.close()

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

    def load_assets(self):
        pass

    def update_table(self):
        pass

    def open_edit_dialog(self, asset_id):
        self.edit_dialog = AssetEditPage(self.page, self, asset_id=asset_id, local_db=self.local_db)
        self.edit_dialog.open_dialog()