import flet as ft
import os
from shopping_list import build_view

def main(page: ft.Page):
    page.title = "Task Management App"
    page.scroll = ft.ScrollMode.AUTO
    build_view(page)

ft.app(
    target=main,
    view=ft.AppView.WEB_BROWSER,
    port=int(os.environ.get("PORT", 8080))
)