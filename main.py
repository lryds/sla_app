import flet as ft
import requests

API_BASE_URL = "http://60.204.247.2:5000"

def main(page: ft.Page):
    page.title = "薪酬查询系统"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.colors.BLUE_GREY_50
    page.window_width = 400
    page.window_height = 700

    current_user_code = ""
    all_salary_data = []

    # --- 登录页组件 ---
    emp_code_input = ft.TextField(label="职工代码", prefix_icon=ft.icons.PERSON, width=300)
    password_input = ft.TextField(label="密码", prefix_icon=ft.icons.LOCK, password=True, can_reveal_password=True, width=300)
    login_error_text = ft.Text(color="red")

    # --- 主页组件 ---
    month_dropdown = ft.Dropdown(label="选择月份查询", width=200, options=[ft.dropdown.Option("全部月份")], value="全部月份")
    salary_list_view = ft.ListView(expand=True, spacing=15, padding=10)
    
    # 🌟 新增：公告栏组件 (横向滑动)
    notice_row = ft.Row(scroll=ft.ScrollMode.ALWAYS, spacing=10)
    notice_area = ft.Container(
        content=notice_row,
        visible=False, # 默认隐藏，等查到数据再显示
        padding=ft.padding.only(left=10, right=10, top=10)
    )

    # --- 密码修改组件 ---
    old_pwd_input = ft.TextField(label="原密码", password=True, width=300)
    new_pwd_input = ft.TextField(label="新密码", password=True, width=300)
    pwd_msg_text = ft.Text()

    # ================= 页面切换逻辑 =================
    def show_login_page():
        page.controls.clear()
        page.appbar = None
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        login_card = ft.Card(
            elevation=5,
            content=ft.Container(
                padding=30, width=350, bgcolor=ft.colors.WHITE, border_radius=15,
                content=ft.Column([
                    ft.Icon(ft.icons.MONETIZATION_ON, size=60, color=ft.colors.BLUE_700),
                    ft.Text("薪酬查询系统", size=24, weight="bold", color=ft.colors.BLUE_900),
                    ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                    emp_code_input, password_input, login_error_text,
                    ft.ElevatedButton("登 录", on_click=btn_login_click, width=300, 
                                      style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
        page.add(login_card)
        page.update()

    def show_main_page():
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        page.appbar = ft.AppBar(
            title=ft.Text(f"欢迎, 职工 {current_user_code}", color=ft.colors.WHITE, size=18),
            bgcolor=ft.colors.BLUE_700,
            actions=[
                ft.IconButton(ft.icons.SETTINGS, tooltip="修改密码", icon_color=ft.colors.WHITE, on_click=lambda _: show_pwd_page()),
                ft.IconButton(ft.icons.LOGOUT, tooltip="退出登录", icon_color=ft.colors.WHITE, on_click=lambda _: show_login_page())
            ]
        )

        month_dropdown.on_change = lambda e: render_salary_list(month_dropdown.value)
        
        # 🌟 把公告栏 (notice_area) 加在页面最上方！
        page.add(
            notice_area, 
            ft.Container(
                padding=ft.padding.only(top=5, left=10, right=10),
                content=ft.Row([month_dropdown], alignment=ft.MainAxisAlignment.END)
            ),
            salary_list_view
        )
        page.update()
        
        # 进入主页后，同时去拿工资数据和公告数据
        fetch_notices()
        fetch_salary_data()

    def show_pwd_page():
        page.controls.clear()
        page.appbar = None
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        pwd_msg_text.value = ""
        page.add(
            ft.Text("修改密码", size=25, weight="bold"),
            old_pwd_input, new_pwd_input, pwd_msg_text,
            ft.ElevatedButton("确认修改", on_click=btn_change_pwd_click, width=300),
            ft.TextButton("返回主页", on_click=lambda _: show_main_page())
        )
        page.update()

    # ================= 业务逻辑 =================
    def btn_login_click(e):
        nonlocal current_user_code
        try:
            res = requests.post(f"{API_BASE_URL}/login", json={
                "emp_code": emp_code_input.value, "password": password_input.value
            }, timeout=5)
            if res.status_code == 200:
                current_user_code = emp_code_input.value
                password_input.value = "" 
                show_main_page()
            else:
                login_error_text.value = res.json().get("message", "登录失败")
                page.update()
        except Exception as ex:
            login_error_text.value = "服务器连接失败，请检查网络"
            page.update()

    # 🌟 新增：获取公告数据的函数
    def fetch_notices():
        notice_row.controls.clear()
        try:
            res = requests.get(f"{API_BASE_URL}/notices", timeout=5)
            if res.status_code == 200:
                notices_data = res.json().get("data", [])
                if notices_data:
                    for item in notices_data:
                        # 画一个带橙色小喇叭的公告卡片
                        notice_card = ft.Container(
                            bgcolor=ft.colors.ORANGE_50,
                            padding=ft.padding.all(8),
                            border_radius=8,
                            border=ft.border.all(1, ft.colors.ORANGE_200),
                            content=ft.Row([
                                ft.Icon(ft.icons.CAMPAIGN, color=ft.colors.ORANGE_700, size=20),
                                ft.Text(f"【{item['title']}】{item['content']} ({item['date']})", 
                                        color=ft.colors.ORANGE_900, size=13)
                            ])
                        )
                        notice_row.controls.append(notice_card)
                    notice_area.visible = True  # 有数据才让它显示
                else:
                    notice_area.visible = False
                page.update()
        except Exception:
            pass # 获取不到公告就默默隐藏，不影响查工资主流程

    def fetch_salary_data():
        nonlocal all_salary_data
        salary_list_view.controls.clear()
        salary_list_view.controls.append(ft.ProgressBar(width=300, color="blue"))
        page.update()

        try:
            res = requests.get(f"{API_BASE_URL}/salary?emp_code={current_user_code}", timeout=5)
            if res.status_code == 200:
                all_salary_data = res.json().get("data", [])
                months = ["全部月份"]
                for item in all_salary_data:
                    if item['month'] not in months:
                        months.append(item['month'])
                
                month_dropdown.options = [ft.dropdown.Option(m) for m in months]
                month_dropdown.value = "全部月份"
                render_salary_list("全部月份")
            else:
                salary_list_view.controls.clear()
                salary_list_view.controls.append(ft.Text(f"请求失败: {res.status_code}"))
                page.update()
        except Exception as ex:
            salary_list_view.controls.clear()
            salary_list_view.controls.append(ft.Text("数据加载失败，请检查网络"))
            page.update()

    def render_salary_list(selected_month):
        salary_list_view.controls.clear()
        filtered_data = [
            item for item in all_salary_data 
            if selected_month == "全部月份" or item['month'] == selected_month
        ]

        if not filtered_data:
            salary_list_view.controls.append(ft.Text("该月暂无薪酬数据", color="grey"))
        else:
            for item in filtered_data:
                card = ft.Card(
                    elevation=3,
                    surface_tint_color=ft.colors.WHITE,
                    content=ft.Container(
                        padding=15, bgcolor=ft.colors.WHITE, border_radius=8,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.CALENDAR_MONTH, color=ft.colors.BLUE_700),
                                ft.Text(f"{item['month']} 薪酬单", size=18, weight="bold", color=ft.colors.BLUE_900)
                            ]),
                            ft.Divider(height=10),
                            ft.Row([ft.Text("基本工资:"), ft.Text(f"¥ {item['base_salary']:.2f}")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("基础奖金:"), ft.Text(f"¥ {item['base_bonus']:.2f}")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("浮动奖金:"), ft.Text(f"¥ {item['floating_bonus']:.2f}")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("岗位奖金:"), ft.Text(f"¥ {item['position_bonus']:.2f}")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("其他奖金:"), ft.Text(f"¥ {item['other_bonuses']:.2f}")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("应扣税款:"), ft.Text(f"-¥ {item['tax']:.2f}", color="red")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=10),
                            ft.Row([
                                ft.Text("实发合计:", weight="bold", size=16), 
                                ft.Text(f"¥ {item['net_salary']:.2f}", color="green", weight="bold", size=22)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ])
                    )
                )
                salary_list_view.controls.append(card)
        page.update()

    def btn_change_pwd_click(e):
        try:
            res = requests.post(f"{API_BASE_URL}/change_password", json={
                "emp_code": current_user_code,
                "old_password": old_pwd_input.value,
                "new_password": new_pwd_input.value
            }, timeout=5)
            if res.status_code == 200:
                pwd_msg_text.value = "密码修改成功！请牢记新密码。"
                pwd_msg_text.color = "green"
            else:
                pwd_msg_text.value = res.json().get("message", "修改失败")
                pwd_msg_text.color = "red"
            page.update()
        except Exception as ex:
            pwd_msg_text.value = "请求出错，请重试"
            pwd_msg_text.color = "red"
            page.update()

    show_login_page()

ft.app(target=main)
