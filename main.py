
import flet as ft
from home import Home
from assetpage import AssetFormPage
import sqlite3
from asset import AssetPage
from sync_server import initialize_local_db

# View factories dictionary
VIEW_FACTORIES = {
    "/": lambda p: Home(p),
    "/asset": lambda p: AssetPage(p),
}

def main(page: ft.Page):
    page.title = "IT Asset Manager"
    page.window.width = 365
    page.window.height = 600
    page.window.min_width = 360
    page.window.min_height = 600
    page.theme_mode = ft.ThemeMode.LIGHT

    # Top AppBar
    page.appbar = ft.AppBar(
        title=ft.Text("IT ASSET MANAGER", size=18, weight="bold"),
        bgcolor=ft.Colors.GREEN_300,
        color=ft.Colors.WHITE,
        center_title=True,
        automatically_imply_leading=False,
    )

    # Floating Action Button
    page.floating_action_button = ft.FloatingActionButton(
        content=ft.Icon(ft.Icons.ADD, color=ft.Colors.BLUE_500),
        bgcolor=ft.Colors.WHITE,
        shape=ft.CircleBorder(),
        on_click=lambda e: page.go("/asset") if hasattr(page, 'views') else None,
    )
    page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_DOCKED

    # BottomAppBar with Menu Options in Menu Button
    page.bottom_appbar = ft.BottomAppBar(
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

    def change_route(e: ft.RouteChangeEvent):
        route = e.route
        print(f"Changing route to: {route}")
        if route not in VIEW_FACTORIES:
            route = "/"
        new_content = VIEW_FACTORIES[route](page)
        page.views.clear()
        page.views.append(
            ft.View(
                route=route,
                controls=[new_content],
                appbar=page.appbar,
                bottom_appbar=page.bottom_appbar,
            )
        )
        page.update()

    def on_resize(e):
        print(f"Resized to: {page.window.width}x{page.window.height}")
        page.update()

    page.on_route_change = change_route
    page.on_view_pop = lambda e: page.go(page.views[-1].route) if len(page.views) > 1 else None
    page.on_resize = on_resize

    page.go("/")

if __name__ == "__main__":
    ft.app(target=main)
