import flet as ft
import requests

API_BASE_URL = "http://60.204.247.2:5000"

def main(page: ft.Page):
    page.title = "Salary Query"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 700

    current_user_code = ""

    emp_code_input = ft.TextField(label="Employee Code", width=300)
    password_input = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
    login_error_text = ft.Text(color="red")

    salary_list_view = ft.ListView(expand=True, spacing=10, padding=10)

    old_pwd_input = ft.TextField(label="Old Password", password=True, width=300)
    new_pwd_input = ft.TextField(label="New Password", password=True, width=300)
    pwd_msg_text = ft.Text()

    def show_login_page():
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.add(
            ft.Text("Salary System", size=30, weight="bold"),
            emp_code_input,
            password_input,
            login_error_text,
            ft.ElevatedButton("Login", on_click=btn_login_click, width=300)
        )
        page.update()

    def show_main_page():
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.START
        salary_list_view.controls.clear()
        salary_list_view.controls.append(ft.Text("Loading data...", color="grey"))
        page.add(
            ft.Row([
                ft.Text(f"Welcome, {current_user_code}", size=20, weight="bold"),
                ft.IconButton(ft.icons.SETTINGS, on_click=lambda _: show_pwd_page()),
                ft.IconButton(ft.icons.LOGOUT, on_click=lambda _: show_login_page())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            salary_list_view
        )
        page.update()
        load_salary_data()

    def show_pwd_page():
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        pwd_msg_text.value = ""
        page.add(
            ft.Text("Change Password", size=25, weight="bold"),
            old_pwd_input,
            new_pwd_input,
            pwd_msg_text,
            ft.ElevatedButton("Confirm", on_click=btn_change_pwd_click, width=300),
            ft.TextButton("Back", on_click=lambda _: show_main_page())
        )
        page.update()

    def btn_login_click(e):
        nonlocal current_user_code
        try:
            res = requests.post(f"{API_BASE_URL}/login", json={
                "emp_code": emp_code_input.value,
                "password": password_input.value
            }, timeout=5)
            if res.status_code == 200:
                current_user_code = emp_code_input.value
                password_input.value = "" 
                show_main_page()
            else:
                login_error_text.value = res.json().get("message", "Login failed")
                page.update()
        except Exception as ex:
            login_error_text.value = "Connection error: " + str(ex)
            page.update()

    def load_salary_data():
        salary_list_view.controls.clear()
        try:
            res = requests.get(f"{API_BASE_URL}/salary?emp_code={current_user_code}", timeout=5)
            if res.status_code == 200:
                data = res.json().get("data", [])
                if not data:
                    salary_list_view.controls.append(ft.Text("No data available"))
                else:
                    for item in data:
                        card = ft.Card(
                            content=ft.Container(
                                padding=10,
                                content=ft.Column([
                                    ft.Text(f"Month: {item['month']}", weight="bold"),
                                    ft.Text(f"Base Salary: {item['base']}"),
                                    ft.Text(f"Bonus: {item['bonus']} | Deduct: {item['deduction']}"),
                                    ft.Text(f"Net Pay: {item['net']}", color="green", weight="bold"),
                                ])
                            )
                        )
                        salary_list_view.controls.append(card)
            else:
                salary_list_view.controls.append(ft.Text(f"Request failed: {res.status_code}"))
        except Exception as ex:
            salary_list_view.controls.append(ft.Text(f"Load failed: {str(ex)}"))
        page.update()

    def btn_change_pwd_click(e):
        try:
            res = requests.post(f"{API_BASE_URL}/change_password", json={
                "emp_code": current_user_code,
                "old_password": old_pwd_input.value,
                "new_password": new_pwd_input.value
            }, timeout=5)
            if res.status_code == 200:
                pwd_msg_text.value = "Success! Remember new password."
                pwd_msg_text.color = "green"
            else:
                pwd_msg_text.value = res.json().get("message", "Change failed")
                pwd_msg_text.color = "red"
            page.update()
        except Exception as ex:
            pwd_msg_text.value = f"Error: {str(ex)}"
            pwd_msg_text.color = "red"
            page.update()

    show_login_page()

ft.app(target=main)
