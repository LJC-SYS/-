package com.team.life.data.repository

import com.team.life.data.local.CheckInEntity
import com.team.life.data.local.ForecastEntity
import com.team.life.data.local.LedgerEntity
import com.team.life.data.local.LifeDao
import com.team.life.data.local.MemoEntity
import com.team.life.data.local.OwnerKeys
import com.team.life.data.local.SessionData
import com.team.life.data.local.SyncActions
import com.team.life.data.local.TodoEntity
import com.team.life.data.local.UserPreferences
import com.team.life.data.local.WeatherEntity
import com.team.life.data.model.AccountingCategory
import com.team.life.data.model.AccountingGroup
import com.team.life.data.model.AccountingSummary
import com.team.life.data.model.Badge
import com.team.life.data.model.CheckInSummary
import com.team.life.data.model.Dashboard
import com.team.life.data.model.ForecastDay
import com.team.life.data.model.LedgerDraft
import com.team.life.data.model.LedgerRecord
import com.team.life.data.model.MemoDraft
import com.team.life.data.model.MemoItem
import com.team.life.data.model.PointTransaction
import com.team.life.data.model.Priority
import com.team.life.data.model.RecordType
import com.team.life.data.model.SyncStatus
import com.team.life.data.model.ThemeMode
import com.team.life.data.model.TodoDraft
import com.team.life.data.model.TodoItem
import com.team.life.data.model.UserProfile
import com.team.life.data.model.UserSettings
import com.team.life.data.model.Weather
import com.team.life.data.remote.ChangePasswordRequest
import com.team.life.data.remote.CheckInRequest
import com.team.life.data.remote.LifeApi
import com.team.life.data.remote.LoginRequest
import com.team.life.data.remote.LogoutRequest
import com.team.life.data.remote.NetworkMonitor
import com.team.life.data.remote.RegisterRequest
import com.team.life.data.remote.UpdateProfileRequest
import com.team.life.data.remote.UpdateSettingsRequest
import com.team.life.data.remote.apiCall
import com.team.life.data.remote.requireData
import com.team.life.data.remote.throwOnFailure
import java.math.BigDecimal
import java.math.RoundingMode
import java.time.LocalDate
import java.time.YearMonth
import java.util.UUID
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlin.math.roundToInt

interface LifeRepository {
    val session: Flow<SessionData>
    val settings: Flow<UserSettings>
    val isOnline: StateFlow<Boolean>
    val weather: Flow<Weather>
    val todos: Flow<List<TodoItem>>
    val memos: Flow<List<MemoItem>>
    val ledger: Flow<List<LedgerRecord>>
    val checkIn: StateFlow<CheckInSummary>
    val profile: StateFlow<UserProfile?>
    val categories: StateFlow<List<AccountingCategory>>
    val summary: Flow<AccountingSummary>
    val syncStatus: StateFlow<SyncStatus>
    val dashboard: Flow<Dashboard>

    suspend fun login(account: String, password: String): Result<Unit>
    suspend fun register(username: String, password: String, email: String? = null, phone: String? = null, nickname: String? = null): Result<Unit>
    suspend fun logout()
    suspend fun refreshAll(): Result<Unit>
    suspend fun refreshWeather(): Result<Unit>
    suspend fun saveTodo(id: Long?, draft: TodoDraft): Result<Unit>
    suspend fun toggleTodo(id: Long, completed: Boolean): Result<Unit>
    suspend fun deleteTodo(id: Long): Result<Unit>
    suspend fun saveMemo(id: Long?, draft: MemoDraft): Result<Unit>
    suspend fun toggleMemoPinned(id: Long): Result<Unit>
    suspend fun deleteMemo(id: Long): Result<Unit>
    suspend fun saveLedger(id: Long?, draft: LedgerDraft): Result<Unit>
    suspend fun deleteLedger(id: Long): Result<Unit>
    suspend fun checkIn(): Result<List<Badge>>
    suspend fun updateProfile(nickname: String, email: String?, phone: String?): Result<Unit>
    suspend fun changePassword(oldPassword: String, newPassword: String): Result<Unit>
    suspend fun updateSettings(settings: UserSettings): Result<Unit>
    suspend fun syncNow(): Result<Unit>
}

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class OfflineFirstLifeRepository(
    private val dao: LifeDao,
    private val api: LifeApi,
    private val preferences: UserPreferences,
    private val networkMonitor: NetworkMonitor,
    private val appScope: CoroutineScope,
    private val onDataChanged: suspend () -> Unit = {},
) : LifeRepository {
    override val session = preferences.session
    override val settings = preferences.settings
    override val isOnline = networkMonitor.isOnline

    private val ownerKey = session.map { it.ownerKey }.distinctUntilChanged()
        .stateIn(appScope, SharingStarted.Eagerly, preferences.sessionBlocking().ownerKey)
    private val _profile = MutableStateFlow<UserProfile?>(null)
    override val profile: StateFlow<UserProfile?> = _profile
    private val _checkIn = MutableStateFlow(CheckInSummary())
    override val checkIn: StateFlow<CheckInSummary> = _checkIn
    private val _categories = MutableStateFlow<List<AccountingCategory>>(emptyList())
    override val categories: StateFlow<List<AccountingCategory>> = _categories
    private val remoteSummary = MutableStateFlow<AccountingSummary?>(null)

    private val coordinator = SyncCoordinator(dao, api, preferences, { isOnline.value })
    override val syncStatus: StateFlow<SyncStatus> = coordinator.status

    override val todos: Flow<List<TodoItem>> = ownerKey.flatMapLatest(dao::observeTodos).map { rows -> rows.map(TodoEntity::toModel) }
    override val memos: Flow<List<MemoItem>> = ownerKey.flatMapLatest(dao::observeMemos).map { rows -> rows.map(MemoEntity::toModel) }
    override val ledger: Flow<List<LedgerRecord>> = ownerKey.flatMapLatest(dao::observeLedger).map { rows -> rows.map(LedgerEntity::toModel) }

    override val weather: Flow<Weather> = settings.flatMapLatest { setting ->
        combine(dao.observeWeather(setting.weatherCityCode), dao.observeForecast(setting.weatherCityCode)) { current, forecast ->
            if (current == null) Weather(cityCode = setting.weatherCityCode, city = setting.weatherCityName)
            else Weather(
                cityCode = current.cityCode,
                city = current.cityName,
                temperature = current.temperature.toDoubleOrNull()?.roundToInt(),
                condition = current.weatherText,
                humidity = current.humidity,
                wind = current.windInfo,
                cached = current.fromCache || !isOnline.value,
                degraded = current.degraded,
                fetchedAt = current.fetchedAt,
                forecasts = forecast.map { ForecastDay(it.date, it.weatherText, it.tempMax.toIntOrNull() ?: 0, it.tempMin.toIntOrNull() ?: 0, it.windInfo.orEmpty()) },
            )
        }
    }

    private val localSummary: Flow<AccountingSummary> = ledger.map { records ->
        val income = records.filter { it.type == RecordType.INCOME }.sumOf { it.amountInCents }
        val expense = records.filter { it.type == RecordType.EXPENSE }.sumOf { it.amountInCents }
        AccountingSummary(
            incomeInCents = income,
            expenseInCents = expense,
            groups = records.groupBy { it.type to it.category }.map { (key, rows) -> AccountingGroup(key.second, key.first, rows.sumOf { it.amountInCents }, rows.size) },
        )
    }
    override val summary: Flow<AccountingSummary> = combine(localSummary, remoteSummary, session, isOnline) { local, remote, session, online ->
        if (session.authenticated && online) remote ?: local else local
    }

    override val dashboard: Flow<Dashboard> = combine(weather, todos, memos, ledger, checkIn) { w, t, m, l, c -> Dashboard(w, t, m, l, c) }

    init {
        appScope.launch {
            ownerKey.collect { key ->
                loadLocalCheckIns(key)
                if (key != OwnerKeys.GUEST) refreshAll()
                else refreshWeather()
            }
        }
        appScope.launch {
            isOnline.drop(1).filter { it }.collect {
                syncNow()
                refreshAll()
            }
        }
    }

    override suspend fun login(account: String, password: String): Result<Unit> = authenticate {
        require(account.isNotBlank() && password.isNotBlank()) { "请输入账号和密码" }
        apiCall { api.login(LoginRequest(account.trim(), password, preferences.deviceIdBlocking())) }.requireData()
    }

    override suspend fun register(username: String, password: String, email: String?, phone: String?, nickname: String?): Result<Unit> = authenticate {
        require(username.matches(Regex("[A-Za-z0-9_]{4,20}"))) { "用户名需为 4～20 位字母、数字或下划线" }
        require(password.length in 8..32 && password.any(Char::isLetter) && password.any(Char::isDigit)) { "密码需为 8～32 位且同时包含字母和数字" }
        require(!email.isNullOrBlank() || !phone.isNullOrBlank()) { "邮箱和手机号至少填写一项" }
        apiCall { api.register(RegisterRequest(username.trim(), password, email.nullIfBlank(), phone.nullIfBlank(), nickname.nullIfBlank())) }.requireData()
    }

    private suspend fun authenticate(block: suspend () -> com.team.life.data.remote.TokenDto): Result<Unit> = runCatching {
        val token = block()
        preferences.saveSession(token.userId, token.username, token.nickname, token.accessToken, token.refreshToken)
        coordinator.moveGuestDataTo(token.userId)
        syncNow().getOrThrow()
        refreshRemote()
    }

    override suspend fun logout() {
        val refreshToken = session.first().refreshToken
        if (isOnline.value) runCatching { apiCall { api.logout(LogoutRequest(refreshToken)) }.throwOnFailure() }
        preferences.clearSession()
        _profile.value = null
        _checkIn.value = CheckInSummary()
    }

    override suspend fun refreshAll(): Result<Unit> = runCatching {
        refreshWeather().getOrThrow()
        if (session.first().authenticated && isOnline.value) {
            syncNow().getOrThrow()
            refreshRemote()
        } else loadLocalCheckIns(ownerKey.value)
    }

    override suspend fun refreshWeather(): Result<Unit> = runCatching {
        val setting = settings.first()
        if (!isOnline.value) {
            checkNotNull(dao.getWeather(setting.weatherCityCode)) { "当前离线且没有天气缓存" }
            return@runCatching
        }
        val current = apiCall { api.currentWeather(setting.weatherCityCode, setting.weatherCityName) }.requireData()
        dao.upsertWeather(WeatherEntity(current.cityCode, current.cityName, current.temperature, current.humidity, current.windInfo, current.weatherText, current.fromCache, current.degraded, current.fetchedAt, current.expiresAt))
        val forecast = apiCall { api.forecast(setting.weatherCityCode, 7, setting.weatherCityName) }.requireData()
        dao.deleteForecast(setting.weatherCityCode)
        dao.upsertForecast(forecast.list.map { ForecastEntity(forecast.cityCode, forecast.cityName, it.date, it.weatherText, it.tempMax, it.tempMin, it.windInfo, forecast.fromCache, forecast.degraded) })
    }

    override suspend fun saveTodo(id: Long?, draft: TodoDraft): Result<Unit> = runCatching {
        require(draft.title.isNotBlank()) { "请输入待办标题" }
        val existing = id?.let { dao.getTodo(ownerKey.value, it) }
        dao.upsertTodo((existing ?: TodoEntity(ownerKey = ownerKey.value, title = draft.title.trim())).copy(
            title = draft.title.trim(), description = draft.description.trim(), dueAt = draft.dueAt.nullIfBlank(),
            priority = draft.priority.toWire(), syncAction = existing.nextAction(), deleted = false, updatedAt = System.currentTimeMillis(),
        ))
        onDataChanged()
        syncIfPossible()
    }

    override suspend fun toggleTodo(id: Long, completed: Boolean): Result<Unit> = runCatching {
        val item = requireNotNull(dao.getTodo(ownerKey.value, id))
        dao.upsertTodo(item.copy(status = if (completed) "completed" else "pending", syncAction = item.nextAction(), updatedAt = System.currentTimeMillis()))
        onDataChanged()
        syncIfPossible()
    }

    override suspend fun deleteTodo(id: Long): Result<Unit> = runCatching {
        val item = requireNotNull(dao.getTodo(ownerKey.value, id))
        if (item.remoteId == null && ownerKey.value == OwnerKeys.GUEST) dao.deleteTodoByClientId(ownerKey.value, item.clientId)
        else dao.upsertTodo(item.copy(deleted = true, syncAction = SyncActions.DELETE, updatedAt = System.currentTimeMillis()))
        onDataChanged()
        syncIfPossible()
    }

    override suspend fun saveMemo(id: Long?, draft: MemoDraft): Result<Unit> = runCatching {
        require(draft.title.isNotBlank() || draft.content.isNotBlank()) { "备忘录内容不能为空" }
        val existing = id?.let { dao.getMemo(ownerKey.value, it) }
        dao.upsertMemo((existing ?: MemoEntity(ownerKey = ownerKey.value, content = draft.content)).copy(
            title = draft.title.trim(), content = draft.content.trim(), pinned = draft.pinned, color = draft.color,
            syncAction = existing.nextAction(), deleted = false, updatedAt = System.currentTimeMillis(),
        ))
        onDataChanged()
        syncIfPossible()
    }

    override suspend fun toggleMemoPinned(id: Long): Result<Unit> = runCatching {
        val item = requireNotNull(dao.getMemo(ownerKey.value, id))
        dao.upsertMemo(item.copy(pinned = !item.pinned, syncAction = item.nextAction(), updatedAt = System.currentTimeMillis()))
        onDataChanged()
        syncIfPossible()
    }

    override suspend fun deleteMemo(id: Long): Result<Unit> = runCatching {
        val item = requireNotNull(dao.getMemo(ownerKey.value, id))
        if (item.remoteId == null && ownerKey.value == OwnerKeys.GUEST) dao.deleteMemoByClientId(ownerKey.value, item.clientId)
        else dao.upsertMemo(item.copy(deleted = true, syncAction = SyncActions.DELETE, updatedAt = System.currentTimeMillis()))
        onDataChanged()
        syncIfPossible()
    }

    override suspend fun saveLedger(id: Long?, draft: LedgerDraft): Result<Unit> = runCatching {
        require(draft.amountInCents > 0) { "金额必须大于 0" }
        val existing = id?.let { dao.getLedger(ownerKey.value, it) }
        dao.upsertLedger((existing ?: LedgerEntity(ownerKey = ownerKey.value, categoryName = draft.categoryName, recordType = draft.type.toWire(), amountInCents = draft.amountInCents)).copy(
            categoryId = draft.categoryId, categoryName = draft.categoryName, recordType = draft.type.toWire(),
            amountInCents = draft.amountInCents, recordDate = draft.date, note = draft.note.trim(),
            syncAction = existing.nextAction(), deleted = false, updatedAt = System.currentTimeMillis(),
        ))
        onDataChanged()
        syncIfPossible()
    }

    override suspend fun deleteLedger(id: Long): Result<Unit> = runCatching {
        val item = requireNotNull(dao.getLedger(ownerKey.value, id))
        if (item.remoteId == null && ownerKey.value == OwnerKeys.GUEST) dao.deleteLedgerByClientId(ownerKey.value, item.clientId)
        else dao.upsertLedger(item.copy(deleted = true, syncAction = SyncActions.DELETE, updatedAt = System.currentTimeMillis()))
        onDataChanged()
        syncIfPossible()
    }

    override suspend fun checkIn(): Result<List<Badge>> = runCatching {
        val today = LocalDate.now().toString()
        val existing = dao.getCheckIns(ownerKey.value).any { it.date == today }
        check(!existing) { "今天已经打卡了" }
        if (ownerKey.value == OwnerKeys.GUEST) {
            dao.upsertCheckIn(CheckInEntity(ownerKey.value, today, 0, false))
            onDataChanged()
            loadLocalCheckIns(ownerKey.value)
            emptyList()
        } else {
            check(isOnline.value) { "当前离线，登录用户打卡需联网确认" }
            val result = apiCall { api.checkIn(CheckInRequest(UUID.randomUUID().toString())) }.requireData()
            dao.upsertCheckIn(CheckInEntity(ownerKey.value, result.checkInDate, result.pointsEarned, true))
            onDataChanged()
            val newBadges = result.newBadges.map { Badge(it.code, it.name, "本次打卡获得", 0, true, result.checkInTime) }
            refreshCheckIn()
            _checkIn.value = _checkIn.value.copy(newBadges = newBadges)
            newBadges
        }
    }

    override suspend fun updateProfile(nickname: String, email: String?, phone: String?): Result<Unit> = runCatching {
        require(session.first().authenticated) { "游客无法修改云端资料" }
        val dto = apiCall { api.updateProfile(UpdateProfileRequest(nickname.trim(), email = email.nullIfBlank(), phone = phone.nullIfBlank())) }.requireData()
        _profile.value = dto.toModel()
    }

    override suspend fun changePassword(oldPassword: String, newPassword: String): Result<Unit> = runCatching {
        require(oldPassword.isNotBlank() && newPassword.length in 8..32 && newPassword.any(Char::isLetter) && newPassword.any(Char::isDigit)) { "新密码需为 8～32 位且同时包含字母和数字" }
        apiCall { api.changePassword(ChangePasswordRequest(oldPassword, newPassword)) }.throwOnFailure()
    }

    override suspend fun updateSettings(settings: UserSettings): Result<Unit> = runCatching {
        preferences.saveSettings(settings)
        if (session.first().authenticated && isOnline.value) {
            apiCall { api.updateSettings(UpdateSettingsRequest(settings.themeMode.name.lowercase(), settings.notificationsEnabled, settings.language, settings.weatherCityCode)) }.throwOnFailure()
        }
        refreshWeather()
    }

    override suspend fun syncNow(): Result<Unit> = coordinator.sync(ownerKey.value)

    private suspend fun syncIfPossible() {
        if (ownerKey.value != OwnerKeys.GUEST && isOnline.value) coordinator.sync(ownerKey.value)
    }

    private suspend fun refreshRemote() {
        val profileDto = apiCall { api.profile() }.requireData()
        _profile.value = profileDto.toModel()
        val settingDto = apiCall { api.settings() }.requireData()
        val local = settings.first()
        preferences.saveSettings(local.copy(
            themeMode = runCatching { ThemeMode.valueOf(settingDto.themeMode.uppercase()) }.getOrDefault(local.themeMode),
            notificationsEnabled = settingDto.notificationEnabled,
            language = settingDto.language,
            weatherCityCode = settingDto.weatherCityCode ?: local.weatherCityCode,
        ))
        val todoRows = apiCall { api.todos() }.requireData().list
        todoRows.forEach { dto ->
            val old = dao.getTodoByClientId(ownerKey.value, dto.clientId)
            if (old != null && old.syncAction != SyncActions.NONE) return@forEach
            dao.upsertTodo(TodoEntity(old?.id ?: 0, ownerKey.value, dto.clientId, dto.id, dto.title, dto.description.orEmpty(), dto.dueAt, dto.priority, dto.status, old?.sortOrder ?: 0, dto.version, SyncActions.NONE, false))
        }
        val memoRows = apiCall { api.memos() }.requireData().list
        memoRows.forEach { dto ->
            val old = dao.getMemoByClientId(ownerKey.value, dto.clientId)
            if (old != null && old.syncAction != SyncActions.NONE) return@forEach
            dao.upsertMemo(MemoEntity(old?.id ?: 0, ownerKey.value, dto.clientId, dto.id, dto.title.orEmpty(), dto.content, dto.isPinned, dto.color ?: "blue", dto.version, SyncActions.NONE, false))
        }
        val ledgerRows = apiCall { api.accountingRecords() }.requireData().list
        ledgerRows.forEach { dto ->
            val old = dao.getLedgerByClientId(ownerKey.value, dto.clientId)
            if (old != null && old.syncAction != SyncActions.NONE) return@forEach
            dao.upsertLedger(LedgerEntity(old?.id ?: 0, ownerKey.value, dto.clientId, dto.id, dto.categoryId, dto.categoryName, dto.recordType, amountToCents(dto.amount), dto.recordDate, dto.note.orEmpty(), dto.version, SyncActions.NONE, false))
        }
        _categories.value = apiCall { api.accountingCategories() }.requireData().list.map {
            AccountingCategory(it.id, it.name, if (it.categoryType == "income") RecordType.INCOME else RecordType.EXPENSE)
        }
        val month = YearMonth.now()
        val serverSummary = apiCall { api.accountingSummary(month.atDay(1).toString(), month.atEndOfMonth().toString()) }.requireData()
        remoteSummary.value = AccountingSummary(
            incomeInCents = amountToCents(serverSummary.totalIncome),
            expenseInCents = amountToCents(serverSummary.totalExpense),
            groups = serverSummary.groups.map { group ->
                AccountingGroup(group.key, if (group.recordType == "income") RecordType.INCOME else RecordType.EXPENSE, amountToCents(group.amount), group.count)
            },
        )
        refreshCheckIn()
    }

    private suspend fun refreshCheckIn() {
        val now = YearMonth.now()
        val stats = apiCall { api.checkInStats() }.requireData()
        val calendar = apiCall { api.checkInCalendar(now.year, now.monthValue) }.requireData()
        val points = apiCall { api.points() }.requireData()
        val transactions = apiCall { api.pointTransactions() }.requireData().list
        val badges = apiCall { api.badges() }.requireData().list
        _checkIn.value = CheckInSummary(
            stats.todayChecked, stats.continuousDays, stats.maxContinuousDays, stats.totalCheckInDays, stats.currentMonthDays,
            points.pointsBalance, points.todayEarned, points.totalEarned, calendar.checkInDays.toSet(),
            transactions.map { PointTransaction(it.id, it.changeAmount, it.balanceAfter, it.transactionType, it.description.orEmpty(), it.createdAt) },
            badges.map { Badge(it.code, it.name, it.description.orEmpty(), it.ruleValue, it.earned, it.earnedAt) },
        )
    }

    private suspend fun loadLocalCheckIns(key: String) {
        val rows = dao.getCheckIns(key)
        val today = LocalDate.now()
        val monthDays = rows.filter { runCatching { YearMonth.from(LocalDate.parse(it.date)) == YearMonth.now() }.getOrDefault(false) }
        var streak = 0
        var cursor = today
        val dates = rows.map { it.date }.toSet()
        while (cursor.toString() in dates) { streak++; cursor = cursor.minusDays(1) }
        _checkIn.value = CheckInSummary(
            checkedToday = today.toString() in dates, streakDays = streak, maxStreakDays = streak, totalDays = rows.size,
            monthDays = monthDays.size, points = rows.sumOf { it.pointsEarned }, checkedDays = monthDays.map { LocalDate.parse(it.date).dayOfMonth }.toSet(),
        )
    }

    private fun String?.nullIfBlank() = this?.trim()?.takeIf(String::isNotEmpty)
    private fun Priority.toWire() = when (this) { Priority.HIGH -> "high"; Priority.MEDIUM -> "normal"; Priority.LOW -> "low" }
    private fun RecordType.toWire() = name.lowercase()
    private fun TodoEntity?.nextAction() = if (this == null || remoteId == null) SyncActions.CREATE else SyncActions.UPDATE
    private fun MemoEntity?.nextAction() = if (this == null || remoteId == null) SyncActions.CREATE else SyncActions.UPDATE
    private fun LedgerEntity?.nextAction() = if (this == null || remoteId == null) SyncActions.CREATE else SyncActions.UPDATE
    private fun amountToCents(value: String) = runCatching { BigDecimal(value).multiply(BigDecimal(100)).setScale(0, RoundingMode.HALF_UP).intValueExact() }.getOrDefault(0)
}

private fun TodoEntity.toModel() = TodoItem(id, title, description, dueAt, when (priority) { "high" -> Priority.HIGH; "low" -> Priority.LOW; else -> Priority.MEDIUM }, status, syncAction == SyncActions.NONE)
private fun MemoEntity.toModel() = MemoItem(id, title, content, pinned, color, syncAction == SyncActions.NONE)
private fun LedgerEntity.toModel() = LedgerRecord(id, categoryId, categoryName, if (recordType == "income") RecordType.INCOME else RecordType.EXPENSE, amountInCents, recordDate, note, syncAction == SyncActions.NONE)
private fun com.team.life.data.remote.UserProfileDto.toModel() = UserProfile(userId, username, nickname ?: username, email, phone, avatarUrl, pointsBalance, continuousDays, totalCheckInDays, badgeCount)
