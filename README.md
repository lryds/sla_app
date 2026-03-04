项目文档：薪酬查询系统 (Flet Android 端)
一、 项目概述
本项目是一个基于 Python Flet 框架开发的轻量级安卓端（Android APK）应用程序。
主要功能包括：

员工登录：通过职工代码和密码进行身份验证。
薪酬查询：登录后，调用后端 API 接口，按月份动态列表展示员工的基本工资、奖金、扣款及实发工资。
密码修改：提供用户修改个人登录密码的入口。
二、 技术栈与环境依赖
前端 UI 框架：Flet (版本 0.21.2 —— 目前打包 Android 最稳定版本)
网络请求：requests 库
打包工具：GitHub Actions 自动化 CI/CD 流程 (集成 Flutter 3.19.6 与 Java 17)
Python 运行环境：Python 3.10.14
三、 核心技术踩坑与解决方案 (💡 重要排错记录)
在开发与打包部署过程中，我们遇到并解决了一系列经典难题，特此记录：

1. 登录成功后界面白屏（无数据渲染）
问题原因：在 Flet 中，如果在 UI 控件（如 ListView）还未通过 page.add() 挂载到页面上时，就向其内部注入数据，会导致视图无法同步更新。此外，数据加载完毕后缺少 page.update() 通知引擎重绘。
解决方案：
严格遵循生命周期：先构建基础页面框架并 page.add()，再调用 load_salary_data() 获取数据。
在数据请求结束后的 finally 或函数末尾，必须显式调用 page.update()。
为网络请求添加 timeout=5，防止因后端无响应导致前端 UI 卡死。
2. 打包报错：name 'unicode' is not defined
问题原因：这是 Flet 依赖的底层工具箱（处理 iOS/Mac 配置的 pbxproj 库）存在的历史遗留 Bug。当项目路径、应用名称（pyproject.toml）中包含中文字符时，底层会调用 Python 2 时代的 unicode 语法，导致在 Python 3 环境下直接崩溃。
解决方案：
去中文：将 pyproject.toml 和代码中的应用代号全部改为纯英文（如 SalaryApp）。
热补丁注入：在 GitHub Actions 中向 Python 环境注入 sitecustomize.py，拦截并重写 unicode 函数，强行将旧语法转换为 str 或 bytes.decode。
3. 打包报错：str() argument 'encoding' must be str, not None
问题原因：上一步的热补丁拦截了 unicode(data, encoding) 调用，但底层源码有时会传入 encoding=None，导致 str() 解析失败。
解决方案：升级热补丁，增加对 None 参数和 bytes 类型的判断与容错处理（默认转换为 utf-8）。
4. 打包报错：ERROR: Invalid requirement: '' (pip 安装依赖失败)
问题原因：在创建 requirements.txt 时，文件末尾多出了空行，或存在 Windows 格式的换行符（CRLF），导致打包工具里的 pip 将空行误认为是一个包名。
解决方案：在 GitHub Actions 脚本中引入 sed 文本处理命令，在打包前自动清理 requirements.txt 中的所有空行、首尾空格和 \r 符号。
四、 最终生产环境配置 (黄金标准代码)
为了保证项目的可复现性，以下是最终跑通的 3 个核心配置文件：

1. pyproject.toml (Flet 打包配置文件)
注意：此处切勿使用中文。

TOML
[
tool.flet
]
app_name = "SalaryApp"
app_version = "1.0.0"
org = "com.salary.app"

[
tool.flet.android
]
min_sdk_version = 21
2. requirements.txt (依赖文件)
注意：保持纯净，不要在末尾敲多余的回车空行。

TXT
flet==0.21.2
requests
3. .github/workflows/build.yml (终极无报错 CI/CD 构建脚本)
此脚本包含了我们一步步打补丁的全部成果，是项目最宝贵的资产。

YAML
name: Build Android APK

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build-android:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10.14'

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip setuptools wheel
          pip install "flet==0.21.2"
          pip install "requests"

      # 终极补丁：解决底层 pbxproj 库的中文字符/unicode解析崩溃 Bug
      - name: Patch unicode bug (Advanced)
        run: |
          cat << 'EOF' > sitecustomize.py
          import builtins
          def mock_unicode(data, encoding='utf-8', errors='strict'):
              if encoding is None:
                  encoding = 'utf-8'
              if isinstance(data, bytes):
                  return data.decode(encoding, errors)
              return str(data)
          builtins.unicode = mock_unicode
          EOF
          echo "PYTHONPATH=$PWD" >> $GITHUB_ENV

      - name: Setup Java 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Setup Flutter 3.19.6
        uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.19.6'
          channel: 'stable'
          cache: true

      - name: Accept Android licenses
        run: |
          yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses || true

      - name: Disable Flutter analytics
        run: flutter config --no-analytics

      # 文本清洗：防止 requirements.txt 包含空行导致 pip 崩溃
      - name: Clean requirements.txt
        run: |
          if [ -f "requirements.txt" ]; then
            sed -i 's/\r$//' requirements.txt
            sed -i '/^[[:space:]]*$/d' requirements.txt
            sed -i 's/^[ \t]*//;s/[ \t]*$//' requirements.txt
          fi

      - name: Build APK
        run: flet build apk

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: salary-apk
          path: build/apk/*.apk
五、 后续开发与维护建议
增减依赖包：如果在开发中引入了新的 Python 库（如 pandas、httpx 等），直接添加到 requirements.txt 中即可。GitHub Actions 会在下次 Push 时自动清理空行并打包。
App 汉化名称：虽然我们在 pyproject.toml 中使用了英文防止打包失败，但如果你希望安装到手机桌面上显示的软件名是中文，可以在 main.py 的同级目录下创建一个 assets 文件夹，后续通过自定义 Android 的 AndroidManifest.xml 来修改桌面显示名称。
版本更新：若 Flet 发布了新版本（如 0.26+ 修复了这些底层 Bug），在确认打包无误前，请勿轻易更改 requirements.txt 中的 flet==0.21.2，这是目前经严格测试最稳妥的版本。
文档归档日期：2026年3月
项目状态：稳定运行，自动化构建流水线已打通。

再次祝贺项目落地！作为初学者能坚持排查出这么深层的环境 Bug 非常不容易，你表现得非常有耐心。如果未来你要加新功能（比如增加图表显示、导出 Excel 等），随时可以来找我探讨！
