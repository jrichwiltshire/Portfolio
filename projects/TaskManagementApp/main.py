import flet as ft
from firebase_config import firestore_db
from calendar import get_calendar_service, create_event


def main(page: ft.Page):
    page.title = "Unified Task & Notes App"

    # Markdown Editor
    markdown_editor = ft.TextField(multiline=True, height=300)

    preview_pane = ft.Markdown()

    # Shopping List View
    shopping_list = ft.ListView(expand=True)

    def update_preview():
        preview_pane.markdown = markdown_editor.value

    markdown_editor.on_change = update_preview

    def add_item(e):
        item_text = item_input.value.strip()
        if item_text:
            shopping_list.controls.append(ft.Checkbox(label=item_text))
            item_input.value = ""
            page.update()

    item_input = ft.TextField(hint_text="Add new item")
    add_button = ft.ElevatedButton("Add", on_click=add_item)

    shopping_list.add(ft.Row([item_input, add_button]))

    def create_calendar_event(e):
        event = {
            "summary": "New Event",
            "location": "",
            "description": markdown_editor.value,
            "start": {
                "dateTime": "2026-03-01T09:00:00-07:00",
                "timeZone": "America/Chicago",
            },
            "end": {
                "dateTime": "2026-03-01T10:00:00-07:00",
                "timeZone": "America/Chicago",
            },
        }
        service = get_calendar_service()
        create_event(service, event)

    calendar_button = ft.ElevatedButton(
        "Create Calendar Event", on_click=create_calendar_event
    )

    page.add(ft.Column([markdown_editor, preview_pane, shopping_list, calendar_button]))


ft.app(target=main)
