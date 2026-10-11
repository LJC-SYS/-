package com.team.life.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.team.life.data.model.AccountingSummary
import com.team.life.data.model.CheckInSummary
import com.team.life.data.model.LedgerRecord
import com.team.life.data.model.MemoItem
import com.team.life.data.model.SyncStatus
import com.team.life.data.model.TodoItem
import com.team.life.data.model.UserProfile
import com.team.life.data.model.UserSettings
import com.team.life.data.model.Weather
import com.team.life.data.repository.LifeRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

sealed interface FeatureUiState<out T> {
    data object Loading : FeatureUiState<Nothing>
    data class Content<T>(val value: T) : FeatureUiState<T>
    data object Empty : FeatureUiState<Nothing>
    data class Error(val message: String) : FeatureUiState<Nothing>
    data class Offline<T>(val cached: T?) : FeatureUiState<T>
}

abstract class FeatureViewModel<T>(
    protected val repository: LifeRepository,
    source: Flow<T>,
    private val empty: (T) -> Boolean,
) : ViewModel() {
    private val error = MutableStateFlow<String?>(null)
    val uiState: StateFlow<FeatureUiState<T>> = combine(source, repository.isOnline, error) { value, online, message ->
        when {
            message != null && !online -> FeatureUiState.Offline(value)
            message != null -> FeatureUiState.Error(message)
            !online -> FeatureUiState.Offline(value)
            empty(value) -> FeatureUiState.Empty
            else -> FeatureUiState.Content(value)
        }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), FeatureUiState.Loading)

    protected fun runAction(block: suspend () -> Result<*>) = viewModelScope.launch {
        error.value = block().exceptionOrNull()?.message
    }
}

class WeatherViewModel(repository: LifeRepository) : FeatureViewModel<Weather>(repository, repository.weather, { !it.available }) {
    fun retry() = runAction(repository::refreshWeather)
}
class TodoViewModel(repository: LifeRepository) : FeatureViewModel<List<TodoItem>>(repository, repository.todos, List<TodoItem>::isEmpty)
class MemoViewModel(repository: LifeRepository) : FeatureViewModel<List<MemoItem>>(repository, repository.memos, List<MemoItem>::isEmpty)
class LedgerViewModel(repository: LifeRepository) : FeatureViewModel<List<LedgerRecord>>(repository, repository.ledger, List<LedgerRecord>::isEmpty)
class CheckInViewModel(repository: LifeRepository) : FeatureViewModel<CheckInSummary>(repository, repository.checkIn, { it.totalDays == 0 })
class ProfileViewModel(repository: LifeRepository) : FeatureViewModel<UserProfile?>(repository, repository.profile, { it == null })

data class SettingsFeature(val settings: UserSettings, val sync: SyncStatus, val summary: AccountingSummary)
class SettingsViewModel(repository: LifeRepository) : FeatureViewModel<SettingsFeature>(
    repository,
    combine(repository.settings, repository.syncStatus, repository.summary, ::SettingsFeature),
    { false },
)
