package com.team.life.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.team.life.AppContainer
import com.team.life.data.local.SessionData
import com.team.life.data.model.AccountingCategory
import com.team.life.data.model.AccountingSummary
import com.team.life.data.model.Dashboard
import com.team.life.data.model.LedgerDraft
import com.team.life.data.model.MemoDraft
import com.team.life.data.model.SyncStatus
import com.team.life.data.model.ThemeMode
import com.team.life.data.model.TodoDraft
import com.team.life.data.model.UserProfile
import com.team.life.data.model.UserSettings
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class AppUiState(
    val session: SessionData = SessionData(),
    val guest: Boolean = false,
    val settings: UserSettings = UserSettings(),
    val dashboard: Dashboard = Dashboard(),
    val profile: UserProfile? = null,
    val summary: AccountingSummary = AccountingSummary(),
    val categories: List<AccountingCategory> = emptyList(),
    val syncStatus: SyncStatus = SyncStatus(),
    val online: Boolean = true,
    val authBusy: Boolean = false,
    val authError: String? = null,
    val actionMessage: String? = null,
) {
    val authenticated: Boolean get() = session.authenticated
    val entered: Boolean get() = authenticated || guest
    val themeMode: ThemeMode get() = settings.themeMode
}

private data class DataState(
    val session: SessionData,
    val settings: UserSettings,
    val dashboard: Dashboard,
    val profile: UserProfile?,
    val summary: AccountingSummary,
)

class AppViewModel(private val container: AppContainer) : ViewModel() {
    private val guest = MutableStateFlow(container.preferences.guestModeBlocking())
    private val authBusy = MutableStateFlow(false)
    private val authError = MutableStateFlow<String?>(null)
    private val actionMessage = MutableStateFlow<String?>(null)

    private val data = combine(
        container.repository.session,
        container.repository.settings,
        container.repository.dashboard,
        container.repository.profile,
        container.repository.summary,
    ) { session, settings, dashboard, profile, summary -> DataState(session, settings, dashboard, profile, summary) }

    private val service = combine(
        container.repository.categories,
        container.repository.syncStatus,
        container.repository.isOnline,
    ) { categories, sync, online -> Triple(categories, sync, online) }

    val uiState: StateFlow<AppUiState> = combine(data, service, guest, authBusy, authError, actionMessage) { values ->
        val d = values[0] as DataState
        @Suppress("UNCHECKED_CAST") val s = values[1] as Triple<List<AccountingCategory>, SyncStatus, Boolean>
        AppUiState(d.session, values[2] as Boolean, d.settings, d.dashboard, d.profile, d.summary, s.first, s.second, s.third, values[3] as Boolean, values[4] as String?, values[5] as String?)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), AppUiState())

    fun login(account: String, password: String) = authenticate { container.repository.login(account, password) }
    fun register(username: String, password: String, email: String?, phone: String?, nickname: String?) = authenticate {
        container.repository.register(username, password, email, phone, nickname)
    }

    private fun authenticate(block: suspend () -> Result<Unit>) {
        if (authBusy.value) return
        viewModelScope.launch {
            authBusy.value = true
            authError.value = null
            val result = block()
            authError.value = result.exceptionOrNull()?.message
            if (result.isSuccess) { guest.value = false; container.preferences.setGuestMode(false) }
            authBusy.value = false
        }
    }

    fun continueAsGuest() { authError.value = null; guest.value = true; viewModelScope.launch { container.preferences.setGuestMode(true) } }
    fun logout() = viewModelScope.launch { guest.value = false; container.preferences.setGuestMode(false); container.repository.logout() }
    fun clearMessage() { actionMessage.value = null }

    fun refresh() = launchAction("数据已刷新") { container.repository.refreshAll() }
    fun refreshWeather() = launchAction("天气已刷新") { container.repository.refreshWeather() }
    fun syncNow() = launchAction("同步完成") { container.repository.syncNow() }
    fun saveTodo(id: Long?, draft: TodoDraft) = launchAction("待办已保存") { container.repository.saveTodo(id, draft) }
    fun toggleTodo(id: Long, completed: Boolean) = launchAction(null) { container.repository.toggleTodo(id, completed) }
    fun deleteTodo(id: Long) = launchAction("待办已删除") { container.repository.deleteTodo(id) }
    fun saveMemo(id: Long?, draft: MemoDraft) = launchAction("备忘录已保存") { container.repository.saveMemo(id, draft) }
    fun toggleMemoPinned(id: Long) = launchAction(null) { container.repository.toggleMemoPinned(id) }
    fun deleteMemo(id: Long) = launchAction("备忘录已删除") { container.repository.deleteMemo(id) }
    fun saveLedger(id: Long?, draft: LedgerDraft) = launchAction("记录已保存") { container.repository.saveLedger(id, draft) }
    fun deleteLedger(id: Long) = launchAction("记录已删除") { container.repository.deleteLedger(id) }
    fun checkIn() = launchAction("打卡成功") { container.repository.checkIn() }
    fun updateProfile(nickname: String, email: String?, phone: String?) = launchAction("资料已更新") { container.repository.updateProfile(nickname, email, phone) }
    fun changePassword(oldPassword: String, newPassword: String) = launchAction("密码已修改") { container.repository.changePassword(oldPassword, newPassword) }
    fun updateSettings(settings: UserSettings) = launchAction("设置已保存") { container.repository.updateSettings(settings) }

    private fun launchAction(success: String?, block: suspend () -> Result<*>) = viewModelScope.launch {
        val result = block()
        actionMessage.value = result.exceptionOrNull()?.message ?: success
    }

    companion object {
        fun factory(container: AppContainer): ViewModelProvider.Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = AppViewModel(container) as T
        }
    }
}
