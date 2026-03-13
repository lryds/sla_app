import flet as ft
import requests

# ===============================
# ⚠️ 改成你后端服务器地址
# 例：http://60.204.247.2:5000
# ===============================
API_BASE_URL = "http://60.204.247.2:5000"


def main(page: ft.Page):
    # ===============================
    # 全局UI基础设置（安卓也可用）
    # ===============================
    page.title = "薪酬查询系统"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F6F8FB"  # 雾白底
    page.padding = 0

    # ===============================
    # 鲜艳莫兰迪色系（更亮更好看）
    # ===============================
    C = {
        "bg": "#F6F8FB",
        "card": "#FFFFFF",
        "soft": "#F1F5F9",
        "line": "#E6ECF5",
        "text": "#0F172A",
        "muted": "#64748B",

        "blue": "#6EA8FF",
        "blue2": "#8EC5FF",
        "green": "#6FC2A4",
        "orange": "#F0B37A",
        "red": "#EF8F8F",
        "purple": "#B9A0FF",
        "teal": "#7BD3EA",
    }

    # ===============================
    # 全局状态
    # ===============================
    current_user_code = ""
    current_user_name = ""
    current_dept_name = ""
    all_salary_data = []  # 薪酬列表缓存

    # ===============================
    # 一些通用小组件/函数
    # ===============================
    def money(v):
        try:
            return f"¥ {float(v):,.2f}"
        except:
            return "¥ 0.00"

    def info_chip(text, color_bg, color_fg):
        return ft.Container(
            bgcolor=color_bg,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border_radius=999,
            content=ft.Text(text, size=12, color=color_fg, weight=ft.FontWeight.W_600),
        )

    def small_row(label, value, value_color=None, bold=False):
        return ft.Row(
            [
                ft.Text(label, size=13, color=C["muted"], expand=True),
                ft.Text(
                    value,
                    size=13,
                    color=value_color if value_color else C["text"],
                    weight=ft.FontWeight.W_700 if bold else ft.FontWeight.W_500,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def section_title(title, color):
        return ft.Container(
            margin=ft.margin.only(top=10, bottom=6),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=C["soft"],
            border_radius=10,
            content=ft.Row(
                [
                    ft.Container(width=10, height=10, bgcolor=color, border_radius=3),
                    ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=C["text"]),
                ],
                spacing=8,
            ),
        )

    # ===============================
    # 登录页组件
    # ===============================
    emp_code_input = ft.TextField(
        label="职工代码",
        prefix_icon=ft.icons.BADGE_OUTLINED,
        width=320,
        border_radius=14,
        bgcolor=C["card"],
    )
    password_input = ft.TextField(
        label="密码",
        prefix_icon=ft.icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        width=320,
        border_radius=14,
        bgcolor=C["card"],
    )
    login_error_text = ft.Text("", color=C["red"], size=13)

    # ===============================
    # 主页组件：欢迎卡片
    # ===============================
    welcome_name_text = ft.Text("", size=18, weight=ft.FontWeight.W_800, color="white")
    welcome_sub_text = ft.Text("", size=12, color="#EEF6FF")

    welcome_card = ft.Container(
        padding=ft.padding.all(16),
        margin=ft.margin.only(left=12, right=12, top=12, bottom=8),
        border_radius=18,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[C["blue"], C["teal"]],
        ),
        shadow=ft.BoxShadow(blur_radius=18, color="#00000020", offset=ft.Offset(0, 8)),
        content=ft.Row(
            [
                ft.Container(
                    width=54,
                    height=54,
                    border_radius=16,
                    bgcolor="#FFFFFF26",
                    content=ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=36, color="white"),
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    [
                        welcome_name_text,
                        welcome_sub_text,
                        ft.Row(
                            [
                                info_chip("鲜艳莫兰迪", "#FFFFFF26", "white"),
                                info_chip("安全查询", "#FFFFFF26", "white"),
                            ],
                            spacing=8,
                        ),
                    ],
                    spacing=4,
                    expand=True,
                ),
            ],
            spacing=12,
        ),
    )

    # ===============================
    # 公告栏（横向滚动）
    # ===============================
    notice_row = ft.Row(scroll=ft.ScrollMode.ALWAYS, spacing=10)
    notice_area = ft.Container(
        visible=False,
        margin=ft.margin.only(left=12, right=12, bottom=8),
        padding=ft.padding.all(10),
        border_radius=16,
        bgcolor=C["card"],
        border=ft.border.all(1, C["line"]),
        content=notice_row,
    )

    # ===============================
    # 月份筛选 + 列表
    # ===============================
    month_dropdown = ft.Dropdown(
        label="选择月份",
        width=180,
        options=[ft.dropdown.Option("全部月份")],
        value="全部月份",
        border_radius=14,
        bgcolor=C["card"],
    )

    salary_list_view = ft.ListView(expand=True, spacing=12, padding=12)

    # ===============================
    # 修改密码页组件
    # ===============================
    old_pwd_input = ft.TextField(label="原密码", password=True, width=320, border_radius=14, bgcolor=C["card"])
    new_pwd_input = ft.TextField(label="新密码", password=True, width=320, border_radius=14, bgcolor=C["card"])
    pwd_msg_text = ft.Text("", size=13)

    # ===============================
    # 基本工资明细 BottomSheet
    # ===============================
    detail_content_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, expand=True)

    def close_detail_sheet():
        detail_bottom_sheet.open = False
        page.update()

    detail_bottom_sheet = ft.BottomSheet(
        open=False,
        content=ft.Container(
            height=620,
            bgcolor=C["card"],
            border_radius=ft.border_radius.only(top_left=22, top_right=22),
            padding=ft.padding.all(14),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(width=10, height=10, bgcolor=C["purple"], border_radius=3),
                                    ft.Text("基本工资明细", size=16, weight=ft.FontWeight.W_800, color=C["text"]),
                                ],
                                spacing=8,
                            ),
                            ft.IconButton(ft.icons.CLOSE, icon_color=C["muted"], on_click=lambda _: close_detail_sheet()),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(height=1, color=C["line"]),
                    ft.Container(content=detail_content_col, expand=True),
                ],
                expand=True,
                spacing=8,
            ),
        ),
    )
    page.overlay.append(detail_bottom_sheet)

    def detail_row(label, value, color=None, bold=False):
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, C["line"])),
            content=ft.Row(
                [
                    ft.Text(label, size=13, color=C["muted"], expand=True),
                    ft.Text(
                        money(value),
                        size=13,
                        color=color if color else C["text"],
                        weight=ft.FontWeight.W_800 if bold else ft.FontWeight.W_600,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

    # ===============================
    # 业务函数：网络请求
    # ===============================
    def btn_login_click(e):
        nonlocal current_user_code, current_user_name, current_dept_name
        login_error_text.value = ""
        page.update()

        code = (emp_code_input.value or "").strip()
        pwd = password_input.value or ""
        if not code or not pwd:
            login_error_text.value = "请输入职工代码和密码"
            page.update()
            return

        try:
            res = requests.post(
                f"{API_BASE_URL}/login",
                json={"emp_code": code, "password": pwd},
                timeout=8,
            )
            if res.status_code == 200:
                current_user_code = code
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

    def fetch_emp_info():
        """欢迎卡片显示：工号 + 姓名 + 科室（从 /emp_info 取）"""
        nonlocal current_user_name, current_dept_name
        try:
            res = requests.get(f"{API_BASE_URL}/emp_info?emp_code={current_user_code}", timeout=8)
            if res.status_code == 200:
                info = res.json().get("data", {})
                current_user_name = info.get("emp_name", current_user_name) or current_user_name
                current_dept_name = info.get("dept_name", "") or "暂无科室信息"
            else:
                current_dept_name = "暂无科室信息"
        except Exception:
            current_dept_name = "获取失败"

        # 更新欢迎卡片
        welcome_name_text.value = f"你好，{current_user_name or '同事'}"
        welcome_sub_text.value = f"工号：{current_user_code}  ·  科室：{current_dept_name}"
        page.update()

    def fetch_notices():
        notice_row.controls.clear()
        try:
            res = requests.get(f"{API_BASE_URL}/notices", timeout=8)
            if res.status_code == 200:
                data = res.json().get("data", [])
                if not data:
                    notice_area.visible = False
                    page.update()
                    return

                for item in data[:20]:
                    notice_card = ft.Container(
                        padding=ft.padding.all(10),
                        border_radius=14,
                        bgcolor="#FFF7ED",  # 柔橙底
                        border=ft.border.all(1, "#FED7AA"),
                        content=ft.Row(
                            [
                                ft.Container(
                                    width=34,
                                    height=34,
                                    border_radius=12,
                                    bgcolor="#FDBA7426",
                                    content=ft.Icon(ft.icons.CAMPAIGN, color="#C2410C", size=18),
                                    alignment=ft.alignment.center,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(item.get("title", ""), size=13, weight=ft.FontWeight.W_800, color="#7C2D12"),
                                        ft.Text(item.get("content", ""), size=12, color="#9A3412", max_lines=2),
                                        ft.Text(item.get("date", ""), size=11, color="#9A3412"),
                                    ],
                                    spacing=2,
                                    width=260,
                                ),
                            ],
                            spacing=10,
                        ),
                    )
                    notice_row.controls.append(notice_card)

                notice_area.visible = True
                page.update()
        except Exception:
            notice_area.visible = False
            page.update()

    def fetch_salary_data():
        nonlocal all_salary_data
        salary_list_view.controls.clear()
        salary_list_view.controls.append(
            ft.Container(
                padding=ft.padding.all(30),
                content=ft.Column(
                    [
                        ft.ProgressRing(color=C["blue"]),
                        ft.Text("正在加载薪酬数据...", color=C["muted"], size=13),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
            )
        )
        page.update()

        try:
            res = requests.get(f"{API_BASE_URL}/salary?emp_code={current_user_code}", timeout=10)
            if res.status_code == 200:
                all_salary_data = res.json().get("data", [])
                months = ["全部月份"]
                for it in all_salary_data:
                    m = it.get("month")
                    if m and m not in months:
                        months.append(m)

                month_dropdown.options = [ft.dropdown.Option(m) for m in months]
                month_dropdown.value = "全部月份"
                render_salary_list("全部月份")
            else:
                salary_list_view.controls.clear()
                salary_list_view.controls.append(ft.Text(f"请求失败: {res.status_code}", color=C["red"]))
                page.update()
        except Exception:
            salary_list_view.controls.clear()
            salary_list_view.controls.append(ft.Text("数据加载失败，请检查网络", color=C["red"]))
            page.update()

    def open_detail_sheet(month):
        """点击查看明细：请求 /salary_detail"""
        detail_content_col.controls.clear()
        detail_content_col.controls.append(
            ft.Container(
                padding=ft.padding.all(26),
                content=ft.Column(
                    [
                        ft.ProgressRing(color=C["purple"]),
                        ft.Text("正在加载基本工资明细...", color=C["muted"], size=13),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
            )
        )
        detail_bottom_sheet.open = True
        page.update()

        try:
            res = requests.get(
                f"{API_BASE_URL}/salary_detail?emp_code={current_user_code}&month={month}",
                timeout=12,
            )
            detail_content_col.controls.clear()

            if res.status_code == 200:
                d = res.json().get("data", {})
                # 头部信息
                detail_content_col.controls.append(
                    ft.Container(
                        padding=ft.padding.all(10),
                        border_radius=14,
                        bgcolor="#EEF2FF",  # 柔紫蓝底
                        border=ft.border.all(1, "#DDE3FF"),
                        content=ft.Column(
                            [
                                ft.Text(f"{d.get('emp_name','')}  ·  {d.get('emp_code','')}",
                                        size=14, weight=ft.FontWeight.W_800, color=C["text"]),
                                ft.Text(f"科室：{d.get('dept_name','')}  ·  月份：{d.get('month','')}",
                                        size=12, color=C["muted"]),
                            ],
                            spacing=4,
                        ),
                    )
                )

                # 应发
                detail_content_col.controls.append(section_title("应发明细", C["green"]))
                detail_content_col.controls += [
                    detail_row("岗位工资", d.get("post_salary", 0)),
                    detail_row("薪级工资", d.get("grade_salary", 0)),
                    detail_row("护补", d.get("nurse_subsidy", 0)),
                    detail_row("护龄", d.get("nurse_age", 0)),
                    detail_row("绩效工资", d.get("perform_salary", 0)),
                    detail_row("卫贴", d.get("med_subsidy", 0)),
                    detail_row("独补", d.get("solo_subsidy", 0)),
                    detail_row("应发合计", d.get("gross_total", 0), color=C["green"], bold=True),
                ]

                # 补发（有就展示）
                if float(d.get("sup_total", 0) or 0) != 0:
                    detail_content_col.controls.append(section_title("补发明细", C["blue"]))
                    detail_content_col.controls += [
                        detail_row("补岗位工资", d.get("sup_post", 0)),
                        detail_row("补薪级工资", d.get("sup_grade", 0)),
                        detail_row("补护补", d.get("sup_nurse", 0)),
                        detail_row("补护龄", d.get("sup_nurse_age", 0)),
                        detail_row("补绩效工资", d.get("sup_perform", 0)),
                        detail_row("补卫贴", d.get("sup_med", 0)),
                        detail_row("补独补", d.get("sup_solo", 0)),
                        detail_row("补发合计", d.get("sup_total", 0), color=C["blue"], bold=True),
                    ]

                # 扣款
                detail_content_col.controls.append(section_title("个人扣款", C["red"]))
                detail_content_col.controls += [
                    detail_row("医保", d.get("med_insurance", 0)),
                    detail_row("借款", d.get("loan", 0)),
                    detail_row("公积金", d.get("provident_fund", 0)),
                    detail_row("税费", d.get("tax_fee", 0)),
                    detail_row("会费", d.get("union_fee", 0)),
                    detail_row("抚养", d.get("alimony", 0)),
                    detail_row("企业养老", d.get("ent_pension", 0)),
                    detail_row("企业年金", d.get("ent_annuity", 0)),
                    detail_row("事业养老", d.get("car_pension", 0)),
                    detail_row("职业年金", d.get("car_annuity", 0)),
                    detail_row("失业保险", d.get("unemploy", 0)),
                    detail_row("绩效扣款", d.get("performance", 0)),
                    detail_row("其他扣款", d.get("other_deduct", 0)),
                    detail_row("代扣", d.get("agent_deduct", 0)),
                    detail_row("扣款合计", d.get("deduct_total", 0), color=C["red"], bold=True),
                ]

                # 其他补贴
                detail_content_col.controls.append(section_title("其他补贴", C["orange"]))
                detail_content_col.controls += [
                    detail_row("通讯补贴", d.get("comm_subsidy", 0)),
                    detail_row("岗位补贴", d.get("post_subsidy", 0)),
                    detail_row("伙食补助", d.get("meal_subsidy", 0)),
                ]

                # 实发合计（大卡片）
                detail_content_col.controls.append(
                    ft.Container(
                        margin=ft.margin.only(top=12),
                        padding=ft.padding.all(12),
                        border_radius=16,
                        bgcolor="#ECFDF5",  # 柔绿底
                        border=ft.border.all(1, "#BBF7D0"),
                        content=ft.Row(
                            [
                                ft.Text("实发合计", size=14, weight=ft.FontWeight.W_800, color="#065F46"),
                                ft.Text(money(d.get("net_salary", 0)), size=20, weight=ft.FontWeight.W_900, color="#047857"),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    )
                )
            else:
                detail_content_col.controls.append(
                    ft.Container(
                        padding=ft.padding.all(30),
                        content=ft.Column(
                            [
                                ft.Icon(ft.icons.INFO_OUTLINE, size=40, color=C["muted"]),
                                ft.Text("暂无该月基本工资明细数据", color=C["muted"], size=13),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                    )
                )

        except Exception:
            detail_content_col.controls.clear()
            detail_content_col.controls.append(
                ft.Container(
                    padding=ft.padding.all(30),
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.WIFI_OFF, size=40, color=C["muted"]),
                            ft.Text("加载失败，请检查网络", color=C["muted"], size=13),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                )
            )
        page.update()

    def render_salary_list(selected_month):
        salary_list_view.controls.clear()

        filtered = [
            it for it in all_salary_data
            if selected_month == "全部月份" or it.get("month") == selected_month
        ]

        if not filtered:
            salary_list_view.controls.append(
                ft.Container(
                    padding=ft.padding.all(20),
                    content=ft.Text("该月暂无薪酬数据", color=C["muted"]),
                )
            )
            page.update()
            return

        for it in filtered:
            month = it.get("month", "")

            # 基本工资行：右侧按钮查看明细
            base_row = ft.Row(
                [
                    ft.Text("基本工资", size=13, color=C["muted"], expand=True),
                    ft.Text(money(it.get("base_salary", 0)), size=13, weight=ft.FontWeight.W_700, color=C["text"]),
                    ft.FilledButton(
                        "明细",
                        style=ft.ButtonStyle(
                            bgcolor=C["purple"],
                            color="white",
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                        on_click=lambda e, m=month: open_detail_sheet(m),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

            card = ft.Container(
                bgcolor=C["card"],
                border=ft.border.all(1, C["line"]),
                border_radius=18,
                padding=ft.padding.all(14),
                shadow=ft.BoxShadow(blur_radius=16, color="#00000010", offset=ft.Offset(0, 6)),
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(width=10, height=10, bgcolor=C["blue"], border_radius=3),
                                ft.Text(f"{month} 薪酬单", size=16, weight=ft.FontWeight.W_900, color=C["text"]),
                            ],
                            spacing=8,
                        ),
                        ft.Divider(height=10, color=C["line"]),
                        base_row,
                        small_row("基础奖金", money(it.get("base_bonus", 0))),
                        small_row("浮动奖金", money(it.get("floating_bonus", 0))),
                        small_row("岗位奖金", money(it.get("position_bonus", 0))),
                        small_row("其他奖金", money(it.get("other_bonuses", 0))),
                        small_row("应扣税款", f"- {money(it.get('tax', 0))}", value_color=C["red"], bold=True),
                        ft.Divider(height=10, color=C["line"]),
                        ft.Row(
                            [
                                ft.Text("实发合计", size=14, weight=ft.FontWeight.W_800, color=C["text"]),
                                ft.Text(money(it.get("net_salary", 0)), size=22, weight=ft.FontWeight.W_900, color=C["green"]),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=8,
                ),
            )
            salary_list_view.controls.append(card)

        page.update()

    def btn_change_pwd_click(e):
        oldp = old_pwd_input.value or ""
        newp = new_pwd_input.value or ""
        if not oldp or not newp:
            pwd_msg_text.value = "请输入原密码和新密码"
            pwd_msg_text.color = C["red"]
            page.update()
            return

        try:
            res = requests.post(
                f"{API_BASE_URL}/change_password",
                json={"emp_code": current_user_code, "old_password": oldp, "new_password": newp},
                timeout=8,
            )
            if res.status_code == 200:
                pwd_msg_text.value = "密码修改成功！请牢记新密码。"
                pwd_msg_text.color = C["green"]
            else:
                pwd_msg_text.value = res.json().get("message", "修改失败")
                pwd_msg_text.color = C["red"]
            page.update()
        except Exception:
            pwd_msg_text.value = "请求失败，请检查网络"
            pwd_msg_text.color = C["red"]
            page.update()

    # ===============================
    # 页面切换：登录 / 主页 / 修改密码
    # ===============================
    def show_login_page():
        page.controls.clear()
        page.appbar = None
        page.bgcolor = C["bg"]

        page.add(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    [
                        ft.Container(
                            width=84,
                            height=84,
                            border_radius=24,
                            gradient=ft.LinearGradient(
                                begin=ft.alignment.top_left,
                                end=ft.alignment.bottom_right,
                                colors=[C["blue"], C["purple"]],
                            ),
                            content=ft.Icon(ft.icons.MONETIZATION_ON, size=44, color="white"),
                            alignment=ft.alignment.center,
                            shadow=ft.BoxShadow(blur_radius=18, color="#00000018", offset=ft.Offset(0, 8)),
                        ),
                        ft.Text("薪酬查询系统", size=22, weight=ft.FontWeight.W_900, color=C["text"]),
                        ft.Text("鲜艳莫兰迪配色 · 清爽易用", size=13, color=C["muted"]),
                        ft.Container(height=8),
                        emp_code_input,
                        password_input,
                        login_error_text,
                        ft.FilledButton(
                            "登 录",
                            style=ft.ButtonStyle(
                                bgcolor=C["blue"],
                                color="white",
                                padding=ft.padding.symmetric(horizontal=22, vertical=14),
                                shape=ft.RoundedRectangleBorder(radius=16),
                            ),
                            width=320,
                            on_click=btn_login_click,
                        ),
                        ft.Container(height=10),
                        ft.Text("如无法登录，请联系管理员核对工号/密码", size=12, color=C["muted"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
            )
        )
        page.update()

    def show_main_page():
        page.controls.clear()
        page.bgcolor = C["bg"]

        # AppBar
        page.appbar = ft.AppBar(
            title=ft.Text("薪酬查询系统", color="white", weight=ft.FontWeight.W_800),
            bgcolor=C["blue"],
            actions=[
                ft.IconButton(
                    ft.icons.SETTINGS,
                    tooltip="修改密码",
                    icon_color="white",
                    on_click=lambda _: show_pwd_page(),
                ),
                ft.IconButton(
                    ft.icons.LOGOUT,
                    tooltip="退出登录",
                    icon_color="white",
                    on_click=lambda _: show_login_page(),
                ),
            ],
        )

        month_dropdown.on_change = lambda e: render_salary_list(month_dropdown.value)

        # 顶部工具条（月份）
        month_bar = ft.Container(
            margin=ft.margin.only(left=12, right=12, bottom=6),
            padding=ft.padding.all(10),
            border_radius=16,
            bgcolor=C["card"],
            border=ft.border.all(1, C["line"]),
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(width=10, height=10, bgcolor=C["orange"], border_radius=3),
                            ft.Text("按月份筛选", size=13, weight=ft.FontWeight.W_700, color=C["text"]),
                        ],
                        spacing=8,
                    ),
                    month_dropdown
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

        page.add(
            welcome_card,
            notice_area,
            month_bar,
            ft.Container(expand=True, content=salary_list_view)
        )
        page.update()

        # 进入主页时加载数据
        fetch_emp_info()
        fetch_notices()
        fetch_salary_data()

    def show_pwd_page():
        page.controls.clear()
        page.appbar = ft.AppBar(
            title=ft.Text("修改密码", color="white", weight=ft.FontWeight.W_800),
            bgcolor=C["purple"],
            leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: show_main_page()),
        )
        pwd_msg_text.value = ""
        page.add(
            ft.Container(
                padding=ft.padding.all(16),
                content=ft.Column(
                    [
                        ft.Container(
                            padding=ft.padding.all(14),
                            border_radius=18,
                            bgcolor=C["card"],
                            border=ft.border.all(1, C["line"]),
                            shadow=ft.BoxShadow(blur_radius=14, color="#00000010", offset=ft.Offset(0, 6)),
                            content=ft.Column(
                                [
                                    ft.Text("为了安全，请设置更复杂的密码", size=13, color=C["muted"]),
                                    old_pwd_input,
                                    new_pwd_input,
                                    pwd_msg_text,
                                    ft.FilledButton(
                                        "确认修改",
                                        style=ft.ButtonStyle(
                                            bgcolor=C["purple"],
                                            color="white",
                                            padding=ft.padding.symmetric(horizontal=22, vertical=14),
                                            shape=ft.RoundedRectangleBorder(radius=16),
                                        ),
                                        on_click=btn_change_pwd_click,
                                    ),
                                ],
                                spacing=10,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        )
                    ],
                    spacing=12,
                ),
            )
        )
        page.update()

    # 程序入口
    show_login_page()


# ✅ 安卓打包/运行推荐写法
ft.app(target=main)
