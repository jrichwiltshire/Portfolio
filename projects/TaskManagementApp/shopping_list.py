from google.cloud import firestore
from firebase_config import firestore_db
import flet as ft

COLLECTION = "shopping_list"

CATEGORIES = [
    "Produce",
    "Dairy & Eggs",
    "Meat & Seafood",
    "Bakery & Bread",
    "Frozen",
    "Pantry",
    "Beverages",
    "Snacks",
    "Household",
    "Personal Care",
    "Other",
]

def add_item(text: str, category: str):
    firestore_db.collection(COLLECTION).add({
        "text": text,
        "checked": False,
        "category": category,
        "created_at": firestore.SERVER_TIMESTAMP,
    })

def set_checked(doc_id: str, checked: bool):
    firestore_db.collection(COLLECTION).document(doc_id).update({
        "checked": checked,
    })

def delete_item(doc_id: str):
    firestore_db.collection(COLLECTION).document(doc_id).delete()

def clear_checked():
    docs = firestore_db.collection(COLLECTION).where("checked","==", True).stream()
    for doc in docs:
        doc.reference.delete()

def watch(callback):
    def on_snapshot(col_snapshot, changes, read_time):
        callback(col_snapshot)

    return firestore_db.collection(COLLECTION).on_snapshot(on_snapshot)

def build_view(page: ft.Page):
    active_column = ft.Column(spacing=4)
    completed_column = ft.Column(spacing=4)
    item_input = ft.TextField(hint_text="Add item...", expand=True)
    category_dropdown = ft.Dropdown(
        value=CATEGORIES[0],
        options=[ft.dropdown.Option(c) for c in CATEGORIES],
        width=180
    )

    def render(snapshot):
        docs = sorted(snapshot, key=lambda d: d.to_dict().get("created_at") or 0)
        active = [(d.id, d.to_dict()) for d in docs if not d.to_dict().get("checked")]
        completed = [(d.id, d.to_dict()) for d in docs if d.to_dict().get("checked")]

        # Build active section grouped by category
        active_column.controls.clear()
        grouped: dict[str, list] = {}
        for doc_id, data in active:
            grouped.setdefault(data["category"], []).append((doc_id, data))

        for category in CATEGORIES:
            if category not in grouped:
                continue
            active_column.controls.append(
                ft.Text(category.upper(), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_600)
            )
            for doc_id, data in grouped[category]:
                active_column.controls.append(
                    ft.Checkbox(
                        label=data["text"],
                        value=False,
                        on_change=lambda e, did=doc_id: set_checked(did, e.control.value),
                    )
                )

        # Build completed section
        completed_column.controls.clear()
        for doc_id, data in completed:
            completed_column.controls.append(
                ft.Row([
                    ft.Checkbox(
                        label=data["text"],
                        value=True,
                        label_style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH),
                        on_change=lambda e, did=doc_id: set_checked(did, e.control.value)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=lambda e, did=doc_id: delete_item(did),
                    ),
                ])
            )

        page.update()

    def on_add(e):
        text = item_input.value.strip()
        if not text:
            return
        add_item(text, category_dropdown.value)
        item_input.value = ""
        item_input.focus()
        page.update()

    def on_clear_all(e):
        clear_checked()

    watcher = watch(render)

    def on_disconnect(e):
        watcher.unsubscribe()

    page.on_disconnect = on_disconnect

    page.add(
        ft.Column([
            ft.Row([item_input, category_dropdown, ft.ElevatedButton("Add", on_click=on_add)]),
            ft.Divider(),
            ft.Text("Shopping List", size=18, weight=ft.FontWeight.BOLD),
            active_column,
            ft.Divider(),
            ft.Row([
                ft.Text("Completed", size=18, weight=ft.FontWeight.BOLD),
                ft.TextButton("Clear all", on_click=on_clear_all),
            ]),
            completed_column,
        ], expand=True)
    )