package com.emuflow.agent

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Warning
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.emuflow.agent.ui.HomeScreen
import com.emuflow.agent.ui.PreflightScreen
import com.emuflow.agent.ui.SettingsScreen
import com.emuflow.agent.ui.theme.EmuFlowAgentTheme

/**
 * Hoofd-activiteit voor EmuFlow Agent.
 *
 * Bevat de NavigationBar (bottom nav) met drie bestemmingen:
 * - Home: status-overzicht + Resume Last Game
 * - Preflight: permission-flow voor eerste gebruik
 * - Instellingen: telemetrie opt-out, vault-map, etc.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            EmuFlowAgentTheme {
                EmuFlowNavHost()
            }
        }
    }
}

/**
 * Nav-routes als sealed class — type-safe navigatie.
 */
sealed class NavRoute(val route: String, val labelRes: Int) {
    data object Home : NavRoute("home", R.string.nav_home)
    data object Preflight : NavRoute("preflight", R.string.nav_preflight)
    data object Settings : NavRoute("settings", R.string.nav_settings)
}

@Composable
fun EmuFlowNavHost() {
    val navController: NavHostController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    val navItems = listOf(
        NavRoute.Home,
        NavRoute.Preflight,
        NavRoute.Settings
    )

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {
            NavigationBar {
                navItems.forEach { item ->
                    NavigationBarItem(
                        selected = currentRoute == item.route,
                        onClick = {
                            navController.navigate(item.route) {
                                popUpTo(navController.graph.startDestinationId) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = {
                            when (item) {
                                NavRoute.Home -> Icon(Icons.Default.Home, contentDescription = null)
                                NavRoute.Preflight -> Icon(Icons.Default.Warning, contentDescription = null)
                                NavRoute.Settings -> Icon(Icons.Default.Settings, contentDescription = null)
                            }
                        },
                        label = { Text(stringResource(item.labelRes)) }
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = NavRoute.Home.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(NavRoute.Home.route) {
                HomeScreen(navController = navController)
            }
            composable(NavRoute.Preflight.route) {
                PreflightScreen(navController = navController)
            }
            composable(NavRoute.Settings.route) {
                SettingsScreen(navController = navController)
            }
        }
    }
}
