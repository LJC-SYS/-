@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.team.life.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Calculate
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.PushPin
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.SwapHoriz
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.team.life.data.model.AccountingCategory
import com.team.life.data.model.AccountingSummary
import com.team.life.data.model.CheckInSummary
import com.team.life.data.model.Dashboard
import com.team.life.data.model.LedgerDraft
import com.team.life.data.model.LedgerRecord
import com.team.life.data.model.MemoDraft
import com.team.life.data.model.MemoItem
import com.team.life.data.model.Priority
import com.team.life.data.model.RecordType
import com.team.life.data.model.SyncPhase
import com.team.life.data.model.SyncStatus
import com.team.life.data.model.ThemeMode
import com.team.life.data.model.TodoDraft
import com.team.life.data.model.TodoItem
import com.team.life.data.model.UserProfile
import com.team.life.data.model.UserSettings
import com.team.life.data.model.Weather
import com.team.life.tools.CalculatorEngine
import com.team.life.tools.UnitConverter
import java.text.NumberFormat
import java.time.LocalDate
import kotlinx.coroutines.launch

@Composable
fun LoginScreen(loading: Boolean, error: String?, onLogin: (String, String) -> Unit, onRegister: (String, String, String?, String?, String?) -> Unit, onGuest: () -> Unit) {
    var register by remember { mutableStateOf(false) }
    var account by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirm by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var nickname by remember { mutableStateOf("") }
    var localError by remember { mutableStateOf<String?>(null) }
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(Modifier.fillMaxWidth().padding(28.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(if (register) "创建账号" else "生活助手", style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
            OutlinedTextField(account, { account = it }, label = { Text(if (register) "用户名" else "用户名 / 邮箱 / 手机号") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            if (register) {
                OutlinedTextField(nickname, { nickname = it }, label = { Text("昵称（可选）") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(email, { email = it }, label = { Text("邮箱（可选）") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(phone, { phone = it }, label = { Text("手机号（可选）") }, modifier = Modifier.fillMaxWidth())
            }
            OutlinedTextField(password, { password = it }, label = { Text("密码") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth())
            if (register) OutlinedTextField(confirm, { confirm = it }, label = { Text("确认密码") }, visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth())
            (localError ?: error)?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(
                enabled = !loading,
                onClick = {
                    localError = when {
                        register && !account.matches(Regex("[A-Za-z0-9_]{4,20}")) -> "用户名需为 4～20 位字母、数字或下划线"
                        account.isBlank() -> "请输入账号"
                        password.isBlank() -> "请输入密码"
                        register && (password.length < 8 || password.none(Char::isLetter) || password.none(Char::isDigit)) -> "密码需至少 8 位且包含字母和数字"
                        register && email.isBlank() && phone.isBlank() -> "邮箱和手机号至少填写一项"
                        register && password != confirm -> "两次密码不一致"
                        else -> null
                    }
                    if (localError == null) {
                        if (register) onRegister(account, password, email, phone, nickname) else onLogin(account, password)
                    }
                },
                modifier = Modifier.fillMaxWidth(),
            ) { if (loading) CircularProgressIndicator(Modifier.height(20.dp)) else Text(if (register) "注册并登录" else "登录") }
            TextButton(onClick = { register = !register; localError = null }, modifier = Modifier.align(Alignment.CenterHorizontally)) { Text(if (register) "已有账号，去登录" else "没有账号，去注册") }
            OutlinedButton(onClick = onGuest, modifier = Modifier.fillMaxWidth()) { Text("游客使用（数据仅保存在本机）") }
        }
    }
}

@Composable
fun HomeScreen(dashboard: Dashboard, guest: Boolean, displayName: String, padding: PaddingValues, navigate: (String) -> Unit, onRefresh: () -> Unit) {
    LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        item {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) { Text("你好，$displayName", style = MaterialTheme.typography.headlineSmall); Text(if (guest) "游客模式 · 云端功能受限" else "今天也要认真生活") }
                IconButton(onClick = { navigate("notifications") }) { Icon(Icons.Default.Notifications, "提醒") }
                IconButton(onClick = onRefresh) { Icon(Icons.Default.Refresh, "刷新") }
            }
        }
        item { DashboardCard("天气 · ${dashboard.weather.city}", if (dashboard.weather.available) "${dashboard.weather.temperature}℃  ${dashboard.weather.condition}" else "暂无数据，点击重试", { navigate("weather") }) }
        item { DashboardCard("待办", "${dashboard.todos.count { !it.completed }} 项未完成", { navigate("todo") }) }
        item { DashboardCard("打卡", if (dashboard.checkIn.checkedToday) "今日已打卡 · 连续 ${dashboard.checkIn.streakDays} 天" else "今日尚未打卡", { navigate("checkin") }) }
        item { Text("常用工具", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold) }
        items(listOf("备忘录" to "memo", "记账" to "ledger", "单位换算" to "converter", "计算器" to "calculator")) { (label, route) -> DashboardCard(label, "点击打开", { navigate(route) }) }
    }
}

@Composable private fun DashboardCard(title: String, subtitle: String, onClick: () -> Unit) {
    Card(Modifier.fillMaxWidth().clickable(onClick = onClick)) { Column(Modifier.padding(18.dp)) { Text(title, style = MaterialTheme.typography.titleMedium); Text(subtitle, color = MaterialTheme.colorScheme.onSurfaceVariant) } }
}

@Composable
fun WeatherScreen(weather: Weather, online: Boolean, onBack: () -> Unit, onRetry: () -> Unit, onCity: () -> Unit) {
    Page("天气", onBack, actions = { IconButton(onClick = onRetry) { Icon(Icons.Default.Refresh, "重试") } }) { padding ->
        LazyColumn(Modifier.padding(padding).fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item {
                Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { Text(weather.city, style = MaterialTheme.typography.headlineSmall); TextButton(onClick = onCity) { Text("设置城市") } }
                    if (weather.available) Text("${weather.temperature}℃", style = MaterialTheme.typography.displayMedium) else Text("没有可用天气数据")
                    Text(weather.condition)
                    weather.humidity?.let { Text("湿度 $it%") }; weather.wind?.let { Text("风力 $it") }
                    if (!online || weather.cached) AssistChip({}, { Text("缓存数据") }); if (weather.degraded) AssistChip({}, { Text("降级数据") })
                    weather.fetchedAt?.let { Text("更新时间 $it", style = MaterialTheme.typography.bodySmall) }
                } }
            }
            item { Text("未来 7 日", style = MaterialTheme.typography.titleMedium) }
            if (weather.forecasts.isEmpty()) item { Text("暂无预报，检查网络后重试") }
            items(weather.forecasts) { day -> Card(Modifier.fillMaxWidth()) { Row(Modifier.padding(14.dp).fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) { Text(day.date); Text(day.condition); Text("${day.low}～${day.high}℃") } } }
        }
    }
}

@Composable
fun TodoScreen(todos: List<TodoItem>, onBack: () -> Unit, onToggle: (Long, Boolean) -> Unit, onSave: (Long?, TodoDraft) -> Unit, onDelete: (Long) -> Unit) {
    var search by remember { mutableStateOf("") }; var filter by remember { mutableStateOf("全部") }; var editing by remember { mutableStateOf<TodoItem?>(null) }; var adding by remember { mutableStateOf(false) }
    val shown = todos.filter { it.title.contains(search, true) || it.description.contains(search, true) }.filter { filter == "全部" || (filter == "未完成" && !it.completed) || (filter == "已完成" && it.completed) }
    Scaffold(topBar = { SimpleTop("待办", onBack) }, floatingActionButton = { FloatingActionButton({ adding = true }) { Icon(Icons.Default.Add, "新增") } }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp)) {
            OutlinedTextField(search, { search = it }, label = { Text("搜索") }, modifier = Modifier.fillMaxWidth())
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("全部", "未完成", "已完成").forEach { FilterChip(filter == it, { filter = it }, { Text(it) }) } }
            if (shown.isEmpty()) EmptyText("没有符合条件的待办") else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) { items(shown, key = { it.id }) { item ->
                Card(Modifier.fillMaxWidth().clickable { editing = item }) { Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(item.completed, { onToggle(item.id, it) }); Column(Modifier.weight(1f)) { Text(item.title, fontWeight = FontWeight.SemiBold); if (item.description.isNotBlank()) Text(item.description); Text(listOfNotNull(item.dueAt, item.priority.name, if (!item.synced) "待同步" else null).joinToString(" · "), style = MaterialTheme.typography.bodySmall) }
                    IconButton({ editing = item }) { Icon(Icons.Default.Edit, "编辑") }; IconButton({ onDelete(item.id) }) { Icon(Icons.Default.Delete, "删除") }
                } }
            } }
        }
    }
    if (adding || editing != null) TodoEditor(editing, { adding = false; editing = null }) { id, draft -> onSave(id, draft); adding = false; editing = null }
}

@Composable private fun TodoEditor(item: TodoItem?, dismiss: () -> Unit, save: (Long?, TodoDraft) -> Unit) {
    var title by remember(item) { mutableStateOf(item?.title.orEmpty()) }; var description by remember(item) { mutableStateOf(item?.description.orEmpty()) }; var date by remember(item) { mutableStateOf(item?.dueAt.orEmpty()) }; var priority by remember(item) { mutableStateOf(item?.priority ?: Priority.MEDIUM) }
    AlertDialog(onDismissRequest = dismiss, title = { Text(if (item == null) "新增待办" else "编辑待办") }, text = { Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(title, { title = it }, label = { Text("标题") }); OutlinedTextField(description, { description = it }, label = { Text("描述") }); OutlinedTextField(date, { date = it }, label = { Text("日期（如 2026-10-11）") })
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) { Priority.entries.forEach { FilterChip(priority == it, { priority = it }, { Text(when (it) { Priority.HIGH -> "高"; Priority.MEDIUM -> "中"; Priority.LOW -> "低" }) }) } }
    } }, confirmButton = { TextButton({ save(item?.id, TodoDraft(title, description, date.ifBlank { null }, priority)) }) { Text("保存") } }, dismissButton = { TextButton(dismiss) { Text("取消") } })
}

@Composable
fun MemoScreen(memos: List<MemoItem>, onBack: () -> Unit, onSave: (Long?, MemoDraft) -> Unit, onPin: (Long) -> Unit, onDelete: (Long) -> Unit) {
    var editing by remember { mutableStateOf<MemoItem?>(null) }; var adding by remember { mutableStateOf(false) }; var search by remember { mutableStateOf("") }
    val shown = memos.filter { it.title.contains(search, true) || it.content.contains(search, true) }
    Scaffold(topBar = { SimpleTop("备忘录", onBack) }, floatingActionButton = { FloatingActionButton({ adding = true }) { Icon(Icons.Default.Add, "新增") } }) { padding ->
        Column(Modifier.padding(padding).padding(16.dp)) { OutlinedTextField(search, { search = it }, label = { Text("搜索备忘录") }, modifier = Modifier.fillMaxWidth()); Spacer(Modifier.height(8.dp))
            if (shown.isEmpty()) EmptyText("还没有备忘录") else LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) { items(shown, key = { it.id }) { item -> Card(Modifier.fillMaxWidth().clickable { editing = item }) { Column(Modifier.padding(14.dp)) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { Text(item.title.ifBlank { "无标题" }, Modifier.weight(1f), fontWeight = FontWeight.Bold); IconButton({ onPin(item.id) }) { Icon(Icons.Default.PushPin, if (item.pinned) "取消置顶" else "置顶") }; IconButton({ onDelete(item.id) }) { Icon(Icons.Default.Delete, "删除") } }
                Text(item.content); Text("颜色 ${item.color}${if (!item.synced) " · 待同步" else ""}", style = MaterialTheme.typography.bodySmall)
            } } } }
        }
    }
    if (adding || editing != null) MemoEditor(editing, { adding = false; editing = null }) { id, draft -> onSave(id, draft); adding = false; editing = null }
}

@Composable private fun MemoEditor(item: MemoItem?, dismiss: () -> Unit, save: (Long?, MemoDraft) -> Unit) {
    var title by remember(item) { mutableStateOf(item?.title.orEmpty()) }; var content by remember(item) { mutableStateOf(item?.content.orEmpty()) }; var pinned by remember(item) { mutableStateOf(item?.pinned ?: false) }; var color by remember(item) { mutableStateOf(item?.color ?: "blue") }
    AlertDialog(onDismissRequest = dismiss, title = { Text(if (item == null) "新增备忘录" else "编辑备忘录") }, text = { Column(verticalArrangement = Arrangement.spacedBy(8.dp)) { OutlinedTextField(title, { title = it }, label = { Text("标题") }); OutlinedTextField(content, { content = it }, label = { Text("内容") }, minLines = 4); Row(verticalAlignment = Alignment.CenterVertically) { Checkbox(pinned, { pinned = it }); Text("置顶") }; Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) { listOf("blue", "green", "yellow", "pink").forEach { FilterChip(color == it, { color = it }, { Text(it) }) } } } }, confirmButton = { TextButton({ save(item?.id, MemoDraft(title, content, pinned, color)) }) { Text("保存") } }, dismissButton = { TextButton(dismiss) { Text("取消") } })
}

@Composable
fun LedgerScreen(records: List<LedgerRecord>, categories: List<AccountingCategory>, summary: AccountingSummary, onBack: () -> Unit, onSave: (Long?, LedgerDraft) -> Unit, onDelete: (Long) -> Unit) {
    var editing by remember { mutableStateOf<LedgerRecord?>(null) }; var adding by remember { mutableStateOf(false) }
    Scaffold(topBar = { SimpleTop("记账", onBack) }, floatingActionButton = { FloatingActionButton({ adding = true }) { Icon(Icons.Default.Add, "新增") } }) { padding -> LazyColumn(Modifier.padding(padding).fillMaxSize(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item { Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) { Text("本期结余 ${money(summary.balanceInCents)}", style = MaterialTheme.typography.headlineSmall); Text("收入 ${money(summary.incomeInCents)} · 支出 ${money(summary.expenseInCents)}") } } }
        item { Text("分类汇总", fontWeight = FontWeight.Bold) }; items(summary.groups) { Text("${it.label}：${money(it.amountInCents)}（${it.count} 笔）") }
        item { HorizontalDivider(); Text("明细", fontWeight = FontWeight.Bold) }
        if (records.isEmpty()) item { EmptyText("还没有记账记录") }
        items(records, key = { it.id }) { item -> Card(Modifier.fillMaxWidth().clickable { editing = item }) { Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) { Column(Modifier.weight(1f)) { Text(item.category, fontWeight = FontWeight.Bold); Text("${item.date} ${item.note}", style = MaterialTheme.typography.bodySmall) }; Text((if (item.type == RecordType.INCOME) "+" else "-") + money(item.amountInCents)); IconButton({ onDelete(item.id) }) { Icon(Icons.Default.Delete, "删除") } } } }
    } }
    if (adding || editing != null) LedgerEditor(editing, categories, { adding = false; editing = null }) { id, draft -> onSave(id, draft); adding = false; editing = null }
}

@Composable private fun LedgerEditor(item: LedgerRecord?, categories: List<AccountingCategory>, dismiss: () -> Unit, save: (Long?, LedgerDraft) -> Unit) {
    var type by remember(item) { mutableStateOf(item?.type ?: RecordType.EXPENSE) }; var category by remember(item) { mutableStateOf(item?.category ?: categories.firstOrNull { it.type == type }?.name.orEmpty()) }; var amount by remember(item) { mutableStateOf(item?.let { BigDecimalText(it.amountInCents) }.orEmpty()) }; var date by remember(item) { mutableStateOf(item?.date ?: LocalDate.now().toString()) }; var note by remember(item) { mutableStateOf(item?.note.orEmpty()) }
    val choices = categories.filter { it.type == type }.ifEmpty { listOf(AccountingCategory(1, if (type == RecordType.INCOME) "其他收入" else "其他支出", type)) }
    AlertDialog(onDismissRequest = dismiss, title = { Text(if (item == null) "新增记录" else "编辑记录") }, text = { Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { RecordType.entries.forEach { FilterChip(type == it, { type = it; category = "" }, { Text(if (it == RecordType.INCOME) "收入" else "支出") }) } }
        Row(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) { choices.forEach { FilterChip(category == it.name, { category = it.name }, { Text(it.name) }) } }
        OutlinedTextField(amount, { amount = it }, label = { Text("金额") }); OutlinedTextField(date, { date = it }, label = { Text("日期") }); OutlinedTextField(note, { note = it }, label = { Text("备注") })
    } }, confirmButton = { TextButton({ val selected = choices.firstOrNull { it.name == category } ?: choices.first(); save(item?.id, LedgerDraft(selected.id, selected.name, type, ((amount.toBigDecimalOrNull() ?: java.math.BigDecimal.ZERO) * java.math.BigDecimal(100)).toInt(), date, note)) }) { Text("保存") } }, dismissButton = { TextButton(dismiss) { Text("取消") } })
}

@Composable
fun CheckInScreen(summary: CheckInSummary, guest: Boolean, padding: PaddingValues, onCheckIn: () -> Unit, showPoints: () -> Unit, showBadges: () -> Unit) {
    LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item { Text("打卡与积分", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold) }
        if (guest) item { Card { Text("游客打卡仅记录在本机，不产生云端积分和徽章。", Modifier.padding(14.dp)) } }
        item { Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(18.dp), horizontalAlignment = Alignment.CenterHorizontally) { Text(if (summary.checkedToday) "今日已打卡" else "今日未打卡", style = MaterialTheme.typography.titleLarge); Text("连续 ${summary.streakDays} 天 · 累计 ${summary.totalDays} 天"); Button(onClick = onCheckIn, enabled = !summary.checkedToday) { Icon(Icons.Default.CheckCircle, null); Text(" 打卡") } } } }
        item { Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) { OutlinedButton(showPoints) { Text("积分 ${summary.points}") }; OutlinedButton(showBadges) { Text("徽章 ${summary.badges.count { it.earned }}") } } }
        item { Text("本月已打卡：${summary.checkedDays.sorted().joinToString("、").ifBlank { "暂无" }}") }
    }
}

@Composable fun PointsScreen(summary: CheckInSummary, onBack: () -> Unit) = Page("积分流水", onBack) { padding -> LazyColumn(Modifier.padding(padding), contentPadding = PaddingValues(16.dp)) { item { Text("当前积分 ${summary.points} · 今日 +${summary.todayEarned}", style = MaterialTheme.typography.titleLarge) }; if (summary.transactions.isEmpty()) item { EmptyText("暂无积分流水") }; items(summary.transactions) { Text("${it.createdAt}  ${it.description}  ${if (it.change >= 0) "+" else ""}${it.change}", Modifier.padding(vertical = 10.dp)) } } }
@Composable fun BadgesScreen(summary: CheckInSummary, onBack: () -> Unit) = Page("徽章", onBack) { padding -> LazyColumn(Modifier.padding(padding), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) { if (summary.badges.isEmpty()) item { EmptyText("暂无徽章数据") }; items(summary.badges) { Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(14.dp)) { Text(it.name, fontWeight = FontWeight.Bold); Text(it.description); Text(if (it.earned) "已获得 ${it.earnedAt.orEmpty()}" else "未解锁 · 目标 ${it.ruleValue}") } } } } }

@Composable
fun ProfileScreen(settings: UserSettings, guest: Boolean, profile: UserProfile?, sync: SyncStatus, online: Boolean, padding: PaddingValues, onSettings: (UserSettings) -> Unit, onProfile: (String, String?, String?) -> Unit, onPassword: (String, String) -> Unit, onSync: () -> Unit, onLogout: () -> Unit) {
    var editProfile by remember { mutableStateOf(false) }; var editPassword by remember { mutableStateOf(false) }; var cityCode by remember(settings.weatherCityCode) { mutableStateOf(settings.weatherCityCode) }; var cityName by remember(settings.weatherCityName) { mutableStateOf(settings.weatherCityName) }
    LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item { Text("个人中心", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold) }
        item { Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp)) { Text(if (guest) "游客" else profile?.nickname ?: "用户", style = MaterialTheme.typography.titleLarge); if (!guest) { Text(profile?.email ?: "未设置邮箱"); OutlinedButton({ editProfile = true }) { Text("修改资料") }; TextButton({ editPassword = true }) { Text("修改密码") } } } } }
        item { Text("主题"); Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) { ThemeMode.entries.forEach { FilterChip(settings.themeMode == it, { onSettings(settings.copy(themeMode = it)) }, { Text(when (it) { ThemeMode.SYSTEM -> "跟随系统"; ThemeMode.LIGHT -> "浅色"; ThemeMode.DARK -> "深色" }) }) } } }
        item { Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { Text("消息提醒", Modifier.weight(1f)); Switch(settings.notificationsEnabled, { onSettings(settings.copy(notificationsEnabled = it)) }) } }
        item { OutlinedTextField(cityCode, { cityCode = it }, label = { Text("天气城市代码") }, modifier = Modifier.fillMaxWidth()); OutlinedTextField(cityName, { cityName = it }, label = { Text("城市名称") }, modifier = Modifier.fillMaxWidth()); Button({ onSettings(settings.copy(weatherCityCode = cityCode, weatherCityName = cityName)) }) { Text("保存城市") } }
        item { Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(14.dp)) { Text(if (online) "网络在线" else "离线"); Text(when (sync.phase) { SyncPhase.SYNCING -> "同步中"; SyncPhase.ERROR -> "同步失败：${sync.message}"; SyncPhase.OFFLINE -> "等待联网同步"; else -> sync.lastSyncAt?.let { "上次同步 $it" } ?: "尚未同步" }); OutlinedButton(onSync) { Text("立即同步") } } } }
        item { Button(onClick = onLogout, modifier = Modifier.fillMaxWidth()) { Text(if (guest) "退出游客模式" else "退出登录") } }
    }
    if (editProfile) ProfileDialog(profile, { editProfile = false }) { n, e, p -> onProfile(n, e, p); editProfile = false }
    if (editPassword) PasswordDialog({ editPassword = false }) { o, n -> onPassword(o, n); editPassword = false }
}

@Composable private fun ProfileDialog(profile: UserProfile?, dismiss: () -> Unit, save: (String, String?, String?) -> Unit) { var n by remember { mutableStateOf(profile?.nickname.orEmpty()) }; var e by remember { mutableStateOf(profile?.email.orEmpty()) }; var p by remember { mutableStateOf(profile?.phone.orEmpty()) }; AlertDialog(onDismissRequest = dismiss, title = { Text("修改资料") }, text = { Column { OutlinedTextField(n, { n = it }, label = { Text("昵称") }); OutlinedTextField(e, { e = it }, label = { Text("邮箱") }); OutlinedTextField(p, { p = it }, label = { Text("手机号") }) } }, confirmButton = { TextButton({ save(n, e, p) }) { Text("保存") } }, dismissButton = { TextButton(dismiss) { Text("取消") } }) }
@Composable private fun PasswordDialog(dismiss: () -> Unit, save: (String, String) -> Unit) { var o by remember { mutableStateOf("") }; var n by remember { mutableStateOf("") }; var c by remember { mutableStateOf("") }; AlertDialog(onDismissRequest = dismiss, title = { Text("修改密码") }, text = { Column { OutlinedTextField(o, { o = it }, label = { Text("旧密码") }, visualTransformation = PasswordVisualTransformation()); OutlinedTextField(n, { n = it }, label = { Text("新密码") }, visualTransformation = PasswordVisualTransformation()); OutlinedTextField(c, { c = it }, label = { Text("确认新密码") }, visualTransformation = PasswordVisualTransformation()); if (n != c) Text("两次密码不一致", color = MaterialTheme.colorScheme.error) } }, confirmButton = { TextButton({ if (n == c) save(o, n) }) { Text("保存") } }, dismissButton = { TextButton(dismiss) { Text("取消") } }) }

@Composable fun ToolsScreen(padding: PaddingValues, navigate: (String) -> Unit) { LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) { item { Text("工具", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold) }; items(listOf(Triple("待办", "管理任务", "todo"), Triple("备忘录", "随手记录", "memo"), Triple("记账", "收支与汇总", "ledger"), Triple("单位换算", "长度、重量、温度等", "converter"), Triple("计算器", "基础四则运算", "calculator"))) { (a, b, r) -> DashboardCard(a, b) { navigate(r) } } } }

@Composable fun CalculatorScreen(onBack: () -> Unit) { val engine = remember { CalculatorEngine() }; var display by remember { mutableStateOf(engine.display) }; val keys = listOf("AC", "⌫", "%", "÷", "7", "8", "9", "×", "4", "5", "6", "-", "1", "2", "3", "+", "+/-", "0", ".", "="); Page("计算器", onBack) { padding -> Column(Modifier.padding(padding).padding(16.dp)) { Text(display, Modifier.fillMaxWidth().padding(20.dp), style = MaterialTheme.typography.displayMedium); keys.chunked(4).forEach { row -> Row(Modifier.fillMaxWidth()) { row.forEach { key -> Button({ display = engine.press(key) }, Modifier.weight(1f).padding(3.dp)) { Text(key) } } } } } } }

@Composable fun ConverterScreen(onBack: () -> Unit) { var category by remember { mutableStateOf(UnitConverter.categories.keys.first()) }; var from by remember(category) { mutableIntStateOf(0) }; var to by remember(category) { mutableIntStateOf(1) }; var input by remember { mutableStateOf("1") }; val options = UnitConverter.categories.getValue(category); val output = input.toDoubleOrNull()?.let { UnitConverter.convert(category, it, from, to) }; Page("单位换算", onBack) { padding -> Column(Modifier.padding(padding).padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) { Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) { UnitConverter.categories.keys.forEach { FilterChip(category == it, { category = it }, { Text(it) }) } }; Text("从"); Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) { options.forEachIndexed { i, it -> FilterChip(from == i, { from = i }, { Text(it.name) }) } }; OutlinedTextField(input, { input = it }, label = { Text("数值") }); Icon(Icons.Default.SwapHoriz, null); Text("到"); Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) { options.forEachIndexed { i, it -> FilterChip(to == i, { to = i }, { Text(it.name) }) } }; Text(output?.let { "结果：${"%.6f".format(it).trimEnd('0').trimEnd('.')} ${options[to].symbol}" } ?: "请输入有效数字", style = MaterialTheme.typography.headlineSmall) } } }

@Composable fun NotificationsScreen(dashboard: Dashboard, onBack: () -> Unit) = Page("提醒摘要", onBack) { padding -> LazyColumn(Modifier.padding(padding), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) { item { DashboardCard("待办提醒", "${dashboard.todos.count { !it.completed }} 项未完成") {} }; item { DashboardCard("打卡提醒", if (dashboard.checkIn.checkedToday) "今日已完成" else "今天还没有打卡") {} }; item { DashboardCard("天气", if (dashboard.weather.available) "${dashboard.weather.city} ${dashboard.weather.temperature}℃" else "暂无天气数据") {} } } }

@Composable private fun Page(title: String, onBack: () -> Unit, actions: @Composable () -> Unit = {}, content: @Composable (PaddingValues) -> Unit) { Scaffold(topBar = { SimpleTop(title, onBack, actions) }) { content(it) } }
@Composable private fun SimpleTop(title: String, onBack: () -> Unit, actions: @Composable () -> Unit = {}) { TopAppBar(title = { Text(title) }, navigationIcon = { IconButton(onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "返回") } }, actions = { actions() }) }
@Composable private fun EmptyText(text: String) { Box(Modifier.fillMaxWidth().padding(28.dp), contentAlignment = Alignment.Center) { Text(text, color = MaterialTheme.colorScheme.onSurfaceVariant) } }
private fun money(cents: Int): String = NumberFormat.getCurrencyInstance(java.util.Locale.CHINA).format(cents / 100.0)
private fun BigDecimalText(cents: Int): String = java.math.BigDecimal(cents).divide(java.math.BigDecimal(100)).stripTrailingZeros().toPlainString()
