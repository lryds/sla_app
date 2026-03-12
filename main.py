# main.py —— 员工手机App端完整代码（修复所有错误的最终版）
import flet as ft
import requests

API_BASE_URL = "http://60.204.247.2:5000"  # ⚠️ 改成你服务器的IP


def main(page: ft.Page):
    page.title = "薪酬查询系统"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.colors.BLUE_GREY_50
    page.window_width = 400
    page.window_height = 700

    # ===================================================
    # 全局状态变量（用 nonlocal 在函数内修改）
    # ===================================================
    current_user_code = ""   # 当前登录职工代码
    current_user_name = ""   # 当前登录姓名
    current_dept_name = ""   # 当前科室名称
    all_salary_data   = []   # 薪酬数据缓存

    # ===================================================
    # 登录页组件
    # ===================================================
    emp_code_input   = ft.TextField(
        label="职工代码", prefix_icon=ft.icons.PERSON, width=300
    )
    password_input   = ft.TextField(
        label="密码", prefix_icon=ft.icons.LOCK,
        password=True, can_reveal_password=True, width=300
    )
    login_error_text = ft.Text(color="red")

    # ===================================================
    # 主页组件
    # ===================================================
    # 欢迎卡片（职工代码 + 姓名 + 科室）
    welcome_name_text = ft.Text("", size=20, weight="bold",
                                color=ft.colors.WHITE)
    welcome_code_text = ft.Text("", size=13, color=ft.colors.BLUE_100)
    welcome_dept_text = ft.Text("", size=13, color=ft.colors.BLUE_100)

    welcome_card = ft.Container(
        padding=ft.padding.all(20),
        margin=ft.margin.all(10),
        border_radius=16,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_700, ft.colors.BLUE_400]
        ),
        shadow=ft.BoxShadow(
            blur_radius=10,
            color=ft.colors.BLUE_200,
            offset=ft.Offset(0, 4)
        ),
        content=ft.Row([
            ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=55, color=ft.colors.WHITE),
            ft.Column([
                welcome_name_text,
                welcome_code_text,
                welcome_dept_text,
            ], spacing=3)
        ], spacing=15)
    )

    # 月份筛选下拉框
    month_dropdown = ft.Dropdown(
        label="选择月份查询", width=200,
        options=[ft.dropdown.Option("全部月份")],
        value="全部月份"
    )

    # 薪酬卡片列表
    salary_list_view = ft.ListView(expand=True, spacing=15, padding=10)

    # 公告横向滚动栏
    notice_row  = ft.Row(scroll=ft.ScrollMode.ALWAYS, spacing=10)
    notice_area = ft.Container(
        content=notice_row,
        visible=False,
        padding=ft.padding.only(left=10, right=10, top=5)
    )

    # ===================================================
    # 修改密码页组件
    # ===================================================
    old_pwd_input = ft.TextField(label="原密码", password=True, width=300)
    new_pwd_input = ft.TextField(label="新密码", password=True, width=300)
    pwd_msg_text  = ft.Text()

    # ===================================================
    # 工资明细弹窗内容列（可滚动）
    # ===================================================
    detail_content_col = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        expand=True
    )

    # ===================================================
    # ✅ 先定义 close_detail_sheet，再定义弹窗
    #    这样弹窗里引用该函数时不会报"未定义"
    # ===================================================
    def close_detail_sheet():
        """关闭工资明细弹窗"""
        detail_bottom_sheet.open = False
        page.update()

    # 底部弹窗
    detail_bottom_sheet = ft.BottomSheet(
        content=ft.Container(
            padding=ft.padding.all(16),
            bgcolor=ft.colors.WHITE,
            border_radius=ft.border_radius.only(top_left=20, top_right=20),
            height=600,
            content=ft.Column([
                # 标题行
                ft.Row([
                    ft.Icon(ft.icons.DESCRIPTION, color=ft.colors.BLUE_700),
                    ft.Text("基本工资明细", size=18, weight="bold",
                            color=ft.colors.BLUE_900),
                    ft.IconButton(
                        ft.icons.CLOSE,
                        on_click=lambda _: close_detail_sheet(),
                        icon_color=ft.colors.GREY_600
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=8),
                # 可滚动内容区
                ft.Container(
                    content=detail_content_col,
                    expand=True
                )
            ])
        ),
        open=False
    )
    page.overlay.append(detail_bottom_sheet)

    # ===================================================
    # 工具函数：构建明细行 & 分组标题
    # ===================================================
    def make_detail_row(label, value, color=None, bold=False):
        """一行明细：左边标签，右边金额"""
        return ft.Container(
            padding=ft.padding.symmetric(vertical=5, horizontal=4),
            border=ft.border.only(
                bottom=ft.BorderSide(0.5, ft.colors.GREY_200)
            ),
            content=ft.Row([
                ft.Text(label, size=13, color=ft.colors.GREY_700, expand=True),
                ft.Text(
                    f"¥ {value:,.2f}",
                    size=13,
                    color=color if color else ft.colors.BLACK87,
                    weight="bold" if bold else "normal"
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

    def make_section_title(title, icon_name, icon_color):
        """分组标题（带背景色）"""
        return ft.Container(
            margin=ft.margin.only(top=12, bottom=4),
            padding=ft.padding.symmetric(horizontal=4, vertical=6),
            bgcolor=ft.colors.BLUE_GREY_50,
            border_radius=6,
            content=ft.Row([
                ft.Icon(icon_name, size=16, color=icon_color),
                ft.Text(title, size=14, weight="bold", color=icon_color)
            ], spacing=6)
        )

    # ===================================================
    # ✅ 先定义所有业务函数，再定义页面切换函数
    #    这样解决"btn_change_pwd_click 未解析"的问题
    # ===================================================

    def btn_login_click(e):
        """登录按钮点击"""
        nonlocal current_user_code, current_user_name, current_dept_name
        login_error_text.value = ""
        page.update()
        try:
            res = requests.post(
                f"{API_BASE_URL}/login",
                json={
                    "emp_code": emp_code_input.value,
                    "password": password_input.value
                },
                timeout=5
            )
            if res.status_code == 200:
                current_user_code = emp_code_input.value
                current_user_name = res.json().get("name", "")
                current_dept_name = ""
                password_input.value = ""
                show_main_page()
            else:
                login_error_text.value = res.json().get("message", "登录失败")
                page.update()
        except Exception:
            login_error_text.value = "服务器连接失败，请检查网络"
            page.update()

    def btn_change_pwd_click(e):
        """确认修改密码按钮点击"""
        try:
            res = requests.post(
                f"{API_BASE_URL}/change_password",
                json={
                    "emp_code":     current_user_code,
                    "old_password": old_pwd_input.value,
                    "new_password": new_pwd_input.value
                },
                timeout=5
            )
            if res.status_code == 200:
                pwd_msg_text.value = "✅ 密码修改成功！请牢记新密码。"
                pwd_msg_text.color = "green"
            else:
                pwd_msg_text.value = res.json().get("message", "修改失败")
                pwd_msg_text.color = "red"
            page.update()
        except Exception:
            pwd_msg_text.value = "请求出错，请重试"
            pwd_msg_text.color = "red"
            page.update()

    def fetch_emp_info():
        """拉取员工信息（姓名+科室），更新欢迎卡片"""
        nonlocal current_user_name, current_dept_name
        try:
            res = requests.get(
                f"{API_BASE_URL}/emp_info?emp_code={current_user_code}",
                timeout=5
            )
            if res.status_code == 200:
                info = res.json().get("data", {})
                current_user_name     = info.get("emp_name", current_user_name)
                current_dept_name     = info.get("dept_name", "")
                welcome_name_text.value = f"👤 {current_user_name}"
                welcome_code_text.value = f"工号：{current_user_code}"
                welcome_dept_text.value = f"科室：{current_dept_name}"
            else:
                welcome_name_text.value = f"👤 {current_user_name or current_user_code}"
                welcome_code_text.value = f"工号：{current_user_code}"
                welcome_dept_text.value = "科室：暂无信息"
            page.update()
        except Exception:
            welcome_name_text.value = f"👤 {current_user_name or current_user_code}"
            welcome_code_text.value = f"工号：{current_user_code}"
            welcome_dept_text.value = "科室：获取失败"
            page.update()

    def fetch_notices():
        """获取公告数据"""
        notice_row.controls.clear()
        try:
            res = requests.get(f"{API_BASE_URL}/notices", timeout=5)
            if res.status_code == 200:
                notices_data = res.json().get("data", [])
                if notices_data:
                    for item in notices_data:
                        notice_card = ft.Container(
                            bgcolor=ft.colors.ORANGE_50,
                            padding=ft.padding.all(8),
                            border_radius=8,
                            border=ft.border.all(1, ft.colors.ORANGE_200),
                            content=ft.Row([
                                ft.Icon(ft.icons.CAMPAIGN,
                                        color=ft.colors.ORANGE_700, size=20),
                                ft.Text(
                                    f"【{item['title']}】{item['content']} ({item['date']})",
                                    color=ft.colors.ORANGE_900, size=13
                                )
                            ])
                        )
                        notice_row.controls.append(notice_card)
                    notice_area.visible = True
                else:
                    notice_area.visible = False
                page.update()
        except Exception:
            pass  # 公告获取失败不影响主流程

    def fetch_salary_data():
        """获取薪酬列表"""
        nonlocal all_salary_data
        salary_list_view.controls.clear()
        salary_list_view.controls.append(
            ft.ProgressBar(width=300, color="blue")
        )
        page.update()
        try:
            res = requests.get(
                f"{API_BASE_URL}/salary?emp_code={current_user_code}",
                timeout=5
            )
            if res.status_code == 200:
                all_salary_data = res.json().get("data", [])
                months = ["全部月份"]
                for item in all_salary_data:
                    if item['month'] not in months:
                        months.append(item['month'])
                month_dropdown.options = [ft.dropdown.Option(m) for m in months]
                month_dropdown.value   = "全部月份"
                render_salary_list("全部月份")
            else:
                salary_list_view.controls.clear()
                salary_list_view.controls.append(
                    ft.Text(f"请求失败: {res.status_code}")
                )
                page.update()
        except Exception:
            salary_list_view.controls.clear()
            salary_list_view.controls.append(
                ft.Text("数据加载失败，请检查网络")
            )
            page.update()

    def open_detail_sheet(month):
        """点击'查看明细'后，请求后端并展示明细弹窗"""
        # 先清空，显示加载中
        detail_content_col.controls.clear()
        detail_content_col.controls.append(
            ft.Container(
                padding=ft.padding.all(30),
                content=ft.Column([
                    ft.ProgressRing(color=ft.colors.BLUE_600),
                    ft.Text("正在加载明细数据...",
                            color=ft.colors.GREY_600, size=13)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   spacing=10)
            )
        )
        detail_bottom_sheet.open = True
        page.update()

        # 请求后端明细接口
        try:
            res = requests.get(
                f"{API_BASE_URL}/salary_detail"
                f"?emp_code={current_user_code}&month={month}",
                timeout=8
            )
            detail_content_col.controls.clear()

            if res.status_code == 200:
                d = res.json().get("data", {})

                # ---- 员工信息头部 ----
                detail_content_col.controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(vertical=8, horizontal=4),
                        content=ft.Column([
                            ft.Text(
                                f"{d.get('emp_name','')}  {d.get('emp_code','')}",
                                size=15, weight="bold",
                                color=ft.colors.BLUE_900
                            ),
                            ft.Text(
                                f"科室：{d.get('dept_name','')}　月份：{d.get('month','')}",
                                size=12, color=ft.colors.GREY_600
                            ),
                        ], spacing=3)
                    )
                )
                detail_content_col.controls.append(ft.Divider(height=6))

                # ---- 应发部分 ----
                detail_content_col.controls.append(
                    make_section_title("📋 应发明细",
                                       ft.icons.ARROW_UPWARD,
                                       ft.colors.GREEN_700)
                )
                detail_content_col.controls += [
                    make_detail_row("岗位工资",   d.get("post_salary", 0)),
                    make_detail_row("薪级工资",   d.get("grade_salary", 0)),
                    make_detail_row("护补",       d.get("nurse_subsidy", 0)),
                    make_detail_row("护龄",       d.get("nurse_age", 0)),
                    make_detail_row("绩效工资",   d.get("perform_salary", 0)),
                    make_detail_row("卫贴",       d.get("med_subsidy", 0)),
                    make_detail_row("独补",       d.get("solo_subsidy", 0)),
                    make_detail_row("应发合计",   d.get("gross_total", 0),
                                    color=ft.colors.GREEN_700, bold=True),
                ]

                # ---- 补发部分（有数据才显示）----
                if d.get("sup_total", 0) != 0:
                    detail_content_col.controls.append(
                        make_section_title("➕ 补发明细",
                                           ft.icons.ADD_CIRCLE_OUTLINE,
                                           ft.colors.BLUE_600)
                    )
                    detail_content_col.controls += [
                        make_detail_row("补岗位工资", d.get("sup_post", 0)),
                        make_detail_row("补薪级工资", d.get("sup_grade", 0)),
                        make_detail_row("补护补",     d.get("sup_nurse", 0)),
                        make_detail_row("补护龄",     d.get("sup_nurse_age", 0)),
                        make_detail_row("补绩效工资", d.get("sup_perform", 0)),
                        make_detail_row("补卫贴",     d.get("sup_med", 0)),
                        make_detail_row("补独补",     d.get("sup_solo", 0)),
                        make_detail_row("补发合计",   d.get("sup_total", 0),
                                        color=ft.colors.BLUE_600, bold=True),
                    ]

                # ---- 扣款明细 ----
                detail_content_col.controls.append(
                    make_section_title("➖ 个人扣款",
                                       ft.icons.REMOVE_CIRCLE_OUTLINE,
                                       ft.colors.RED_600)
                )
                detail_content_col.controls += [
                    make_detail_row("医保",     d.get("med_insurance", 0)),
                    make_detail_row("借款",     d.get("loan", 0)),
                    make_detail_row("公积金",   d.get("provident_fund", 0)),
                    make_detail_row("税费",     d.get("tax_fee", 0)),
                    make_detail_row("会费",     d.get("union_fee", 0)),
                    make_detail_row("抚养",     d.get("alimony", 0)),
                    make_detail_row("企业养老", d.get("ent_pension", 0)),
                    make_detail_row("企业年金", d.get("ent_annuity", 0)),
                    make_detail_row("事业养老", d.get("car_pension", 0)),
                    make_detail_row("职业年金", d.get("car_annuity", 0)),
                    make_detail_row("失业保险", d.get("unemploy", 0)),
                    make_detail_row("绩效扣款", d.get("performance", 0)),
                    make_detail_row("其他扣款", d.get("other_deduct", 0)),
                    make_detail_row("代扣",     d.get("agent_deduct", 0)),
                    make_detail_row("扣款合计", d.get("deduct_total", 0),
                                    color=ft.colors.RED_600, bold=True),
                ]

                # ---- 其他补贴 ----
                detail_content_col.controls.append(
                    make_section_title("🎁 其他补贴",
                                       ft.icons.CARD_GIFTCARD,
                                       ft.colors.PURPLE_600)
                )
                detail_content_col.controls += [
                    make_detail_row("通讯补贴", d.get("comm_subsidy", 0)),
                    make_detail_row("岗位补贴", d.get("post_subsidy", 0)),
                    make_detail_row("伙食补助", d.get("meal_subsidy", 0)),
                ]

                # ---- 实发合计（大字展示）----
                detail_content_col.controls.append(ft.Divider(height=10))
                detail_content_col.controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(vertical=12, horizontal=4),
                        bgcolor=ft.colors.GREEN_50,
                        border_radius=8,
                        content=ft.Row([
                            ft.Text("💰 实发合计",
                                    size=16, weight="bold",
                                    color=ft.colors.GREEN_800),
                            ft.Text(
                                f"¥ {d.get('net_salary', 0):,.2f}",
                                size=24, weight="bold",
                                color=ft.colors.GREEN_700
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    )
                )

            else:
                # 没有明细数据时的提示
                detail_content_col.controls.append(
                    ft.Container(
                        padding=ft.padding.all(30),
                        content=ft.Column([
                            ft.Icon(ft.icons.INFO_OUTLINE,
                                    size=40, color=ft.colors.GREY_400),
                            ft.Text("暂无该月基本工资明细数据",
                                    color=ft.colors.GREY_500, size=14)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                           spacing=10)
                    )
                )

        except Exception as ex:
            detail_content_col.controls.clear()
            detail_content_col.controls.append(
                ft.Container(
                    padding=ft.padding.all(30),
                    content=ft.Column([
                        ft.Icon(ft.icons.WIFI_OFF,
                                size=40, color=ft.colors.GREY_400),
                        ft.Text("加载失败，请检查网络",
                                color=ft.colors.GREY_500, size=14)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                       spacing=10)
                )
            )

        page.update()

    def render_salary_list(selected_month):
        """渲染薪酬卡片列表，基本工资行右侧带'查看明细'按钮"""
        salary_list_view.controls.clear()
        filtered_data = [
            item for item in all_salary_data
            if selected_month == "全部月份" or item['month'] == selected_month
        ]

        if not filtered_data:
            salary_list_view.controls.append(
                ft.Text("该月暂无薪酬数据", color="grey")
            )
        else:
            for item in filtered_data:
                month = item['month']

                # ✅ 基本工资行 + 右侧"查看明细"按钮
                # 注意用 m=month 绑定当前月份，避免循环闭包问题
                base_salary_row = ft.Row([
                    ft.Text("基本工资:", size=13,
                            color=ft.colors.BLACK87, expand=True),
                    ft.Text(f"¥ {item['base_salary']:,.2f}", size=13),
                    ft.TextButton(
                        "查看明细",
                        style=ft.ButtonStyle(
                            color=ft.colors.BLUE_600,
                            padding=ft.padding.symmetric(horizontal=4)
                        ),
                        on_click=lambda e, m=month: open_detail_sheet(m)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

                card = ft.Card(
                    elevation=3,
                    surface_tint_color=ft.colors.WHITE,
                    content=ft.Container(
                        padding=15,
                        bgcolor=ft.colors.WHITE,
                        border_radius=8,
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.icons.CALENDAR_MONTH,
                                        color=ft.colors.BLUE_700),
                                ft.Text(f"{month} 薪酬单",
                                        size=18, weight="bold",
                                        color=ft.colors.BLUE_900)
                            ]),
                            ft.Divider(height=8),
                            base_salary_row,
                            ft.Row([
                                ft.Text("基础奖金:", size=13,
                                        color=ft.colors.BLACK87),
                                ft.Text(f"¥ {item['base_bonus']:,.2f}",
                                        size=13)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text("浮动奖金:", size=13,
                                        color=ft.colors.BLACK87),
                                ft.Text(f"¥ {item['floating_bonus']:,.2f}",
                                        size=13)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text("岗位奖金:", size=13,
                                        color=ft.colors.BLACK87),
                                ft.Text(f"¥ {item['position_bonus']:,.2f}",
                                        size=13)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text("其他奖金:", size=13,
                                        color=ft.colors.BLACK87),
                                ft.Text(f"¥ {item['other_bonuses']:,.2f}",
                                        size=13)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([
                                ft.Text("应扣税款:", size=13,
                                        color=ft.colors.RED_400),
                                ft.Text(f"-¥ {item['tax']:,.2f}",
                                        size=13, color=ft.colors.RED_400)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Divider(height=8),
                            ft.Row([
                                ft.Text("实发合计:",
                                        weight="bold", size=16),
                                ft.Text(f"¥ {item['net_salary']:,.2f}",
                                        color=ft.colors.GREEN_700,
                                        weight="bold", size=22)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ])
                    )
                )
                salary_list_view.controls.append(card)
        page.update()

    # ===================================================
    # 页面切换函数（放在所有业务函数之后，确保引用有效）
    # ===================================================
    def show_login_page():
        page.controls.clear()
        page.appbar = None
        page.vertical_alignment   = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        login_card = ft.Card(
            elevation=5,
            content=ft.Container(
                padding=30, width=350,
                bgcolor=ft.colors.WHITE, border_radius=15,
                content=ft.Column([
                    ft.Icon(ft.icons.MONETIZATION_ON,
                            size=60, color=ft.colors.BLUE_700),
                    ft.Text("薪酬查询系统", size=24,
                            weight="bold", color=ft.colors.BLUE_900),
                    ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                    emp_code_input,
                    password_input,
                    login_error_text,
                    ft.ElevatedButton(
                        "登 录",
                        on_click=btn_login_click,
                        width=300,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_700,
                            color=ft.colors.WHITE
                        )
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
        page.add(login_card)
        page.update()

    def show_main_page():
        page.controls.clear()
        page.vertical_alignment   = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        page.appbar = ft.AppBar(
            title=ft.Text("薪酬查询系统",
                          color=ft.colors.WHITE, size=18),
            bgcolor=ft.colors.BLUE_700,
            actions=[
                ft.IconButton(
                    ft.icons.SETTINGS, tooltip="修改密码",
                    icon_color=ft.colors.WHITE,
                    on_click=lambda _: show_pwd_page()
                ),
                ft.IconButton(
                    ft.icons.LOGOUT, tooltip="退出登录",
                    icon_color=ft.colors.WHITE,
                    on_click=lambda _: show_login_page()
                )
            ]
        )

        month_dropdown.on_change = (
            lambda e: render_salary_list(month_dropdown.value)
        )

        page.add(
            welcome_card,    # 欢迎卡片
            notice_area,     # 公告横向滚动
            ft.Container(
                padding=ft.padding.only(top=5, left=10, right=10),
                content=ft.Row(
                    [month_dropdown],
                    alignment=ft.MainAxisAlignment.END
                )
            ),
            salary_list_view
        )
        page.update()

        # 同时加载三类数据
        fetch_emp_info()
        fetch_notices()
        fetch_salary_data()

    def show_pwd_page():
        page.controls.clear()
        page.appbar = None
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        pwd_msg_text.value = ""
        page.add(
            ft.Text("修改密码", size=25, weight="bold"),
            old_pwd_input,
            new_pwd_input,
            pwd_msg_text,
            # ✅ btn_change_pwd_click 此时已定义，不会报错
            ft.ElevatedButton("确认修改",
                              on_click=btn_change_pwd_click,
                              width=300),
            ft.TextButton("返回主页",
                          on_click=lambda _: show_main_page())
        )
        page.update()

    # ===================================================
    # 程序入口：启动时显示登录页
    # ===================================================
    show_login_page()


# 生产模式：Web浏览器访问，监听8000端口
ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8000)
