package com.team.life.ui

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.GridView
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navDeepLink
import com.team.life.ui.screens.BadgesScreen
import com.team.life.ui.screens.CalculatorScreen
import com.team.life.ui.screens.CheckInScreen
import com.team.life.ui.screens.ConverterScreen
import com.team.life.ui.screens.HomeScreen
import com.team.life.ui.screens.LedgerScreen
import com.team.life.ui.screens.LoginScreen
import com.team.life.ui.screens.MemoScreen
import com.team.life.ui.screens.NotificationsScreen
import com.team.life.ui.screens.PointsScreen
import com.team.life.ui.screens.ProfileScreen
import com.team.life.ui.screens.TodoScreen
import com.team.life.ui.screens.ToolsScreen
import com.team.life.ui.screens.WeatherScreen

private data class NavItem(val route: String, val label: String, val icon: ImageVector)
private val bottomItems = listOf(
    NavItem("home", "首页", Icons.Default.Home),
    NavItem("tools", "工具", Icons.Default.GridView),
    NavItem("checkin", "打卡", Icons.Default.CalendarMonth),
    NavItem("profile", "我的", Icons.Default.Person),
)

@Composable
fun LifeAssistantApp(state: AppUiState, viewModel: AppViewModel) {
    if (!state.entered) {
        LoginScreen(state.authBusy, state.authError, viewModel::login, viewModel::register, viewModel::continueAsGuest)
        return
    }
    val navController = rememberNavController()
    val backStack by navController.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route
    val snackbar = remember { SnackbarHostState() }
    LaunchedEffect(state.actionMessage) {
        state.actionMessage?.let { snackbar.showSnackbar(it); viewModel.clearMessage() }
    }
    Scaffold(
        snackbarHost = { SnackbarHost(snackbar) },
        bottomBar = {
            if (bottomItems.any { it.route == currentRoute }) NavigationBar {
                bottomItems.forEach { item -> NavigationBarItem(
                    selected = currentRoute == item.route,
                    onClick = { navController.navigate(item.route) { popUpTo(navController.graph.findStartDestination().id) { saveState = true }; launchSingleTop = true; restoreState = true } },
                    icon = { Icon(item.icon, item.label) }, label = { Text(item.label) },
                ) }
            }
        },
    ) { rootPadding ->
        NavHost(navController, "home") {
            composable("home") { HomeScreen(state.dashboard, state.guest, if (state.guest) "朋友" else state.profile?.nickname ?: state.session.nickname ?: "你", rootPadding, navController::navigate, viewModel::refresh) }
            composable("tools") { ToolsScreen(rootPadding, navController::navigate) }
            composable("checkin", deepLinks = listOf(navDeepLink { uriPattern = "lifeassistant://open/checkin" })) { CheckInScreen(state.dashboard.checkIn, state.guest, rootPadding, viewModel::checkIn, { navController.navigate("points") }, { navController.navigate("badges") }) }
            composable("profile") { ProfileScreen(state.settings, state.guest, state.profile, state.syncStatus, state.online, rootPadding, viewModel::updateSettings, viewModel::updateProfile, viewModel::changePassword, viewModel::syncNow, viewModel::logout) }
            composable("weather", deepLinks = listOf(navDeepLink { uriPattern = "lifeassistant://open/weather" })) { WeatherScreen(state.dashboard.weather, state.online, navController::popBackStack, viewModel::refreshWeather) { navController.navigate("profile") } }
            composable("todo", deepLinks = listOf(navDeepLink { uriPattern = "lifeassistant://open/todo" })) { TodoScreen(state.dashboard.todos, navController::popBackStack, viewModel::toggleTodo, viewModel::saveTodo, viewModel::deleteTodo) }
            composable("memo") { MemoScreen(state.dashboard.memos, navController::popBackStack, viewModel::saveMemo, viewModel::toggleMemoPinned, viewModel::deleteMemo) }
            composable("ledger") { LedgerScreen(state.dashboard.ledger, state.categories, state.summary, navController::popBackStack, viewModel::saveLedger, viewModel::deleteLedger) }
            composable("calculator") { CalculatorScreen(navController::popBackStack) }
            composable("converter") { ConverterScreen(navController::popBackStack) }
            composable("notifications") { NotificationsScreen(state.dashboard, navController::popBackStack) }
            composable("points") { PointsScreen(state.dashboard.checkIn, navController::popBackStack) }
            composable("badges") { BadgesScreen(state.dashboard.checkIn, navController::popBackStack) }
        }
    }
}
