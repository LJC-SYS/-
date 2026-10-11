# 一站生活 · Android

基于 Kotlin、Jetpack Compose、Material 3、MVVM、Room、DataStore、Retrofit、WorkManager 和 Glance 的原生 Android 客户端。

## 环境要求

- JDK 17
- Android SDK 37
- Gradle 9.4.1（Wrapper 已包含）
- 本地后端默认地址：`http://10.0.2.2:8000/api/v1/`

## 环境变体

| Flavor | 地址来源 | 默认值 |
| --- | --- | --- |
| `local` | `LOCAL_API_BASE_URL` | 模拟器本机后端 |
| `qa` | `TEST_API_BASE_URL` | 模拟器本机后端 |
| `prod` | `PROD_API_BASE_URL` | `https://example.invalid/api/v1/` |

Android Gradle Plugin 保留所有以 `test` 开头的 flavor 名称，因此计划中的 `test` 环境在工程中命名为 `qa`，但仍读取 `TEST_API_BASE_URL`。属性可放在用户级 `gradle.properties` 或作为同名环境变量提供。Release 未配置正式签名。

## 功能

- 登录、注册、游客模式、Token 注入与互斥刷新
- 当前天气、1～7 日预报、城市设置、Room 缓存与离线降级
- 打卡、日历、积分流水、徽章
- 待办、备忘录、收入/支出记账及分类汇总
- 游客/用户数据隔离、离线墓碑、增量推拉、冲突服务端优先
- 资料、密码、消息开关、`system/light/dark` 三态主题和同步状态
- 单位换算、计算器、提醒摘要
- 天气、打卡、待办三个独立 Glance 小组件及 Deep Link

## 验证命令

```powershell
.\gradlew.bat testLocalDebugUnitTest
.\gradlew.bat lintLocalDebug
.\gradlew.bat assembleLocalDebug
.\gradlew.bat assembleProdRelease
```

APK 输出：

- `app/build/outputs/apk/local/debug/app-local-debug.apk`
- `app/build/outputs/apk/prod/release/app-prod-release-unsigned.apk`

## 目录

```text
app/src/main/java/com/team/life/
├── data/       # Room、DataStore、网络契约、Repository 与同步
├── tools/      # 计算器与单位换算核心
├── ui/         # ViewModel、导航、页面与主题
└── widget/     # 三个 Glance 小组件与刷新 Worker
```
