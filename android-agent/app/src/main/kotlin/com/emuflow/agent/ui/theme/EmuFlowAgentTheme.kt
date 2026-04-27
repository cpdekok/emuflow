package com.emuflow.agent.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

// EmuFlow kleurpalet — minimalistisch, gaming-adjacent zonder gamer-clichés
private val EmuFlowPurple = Color(0xFF6750A4)   // Material 3 baseline primary
private val EmuFlowPurpleContainer = Color(0xFFEADDFF)
private val EmuFlowGreen = Color(0xFF4CAF50)    // Status "actief" kleur

private val LightColorScheme = lightColorScheme(
    primary = EmuFlowPurple,
    onPrimary = Color.White,
    primaryContainer = EmuFlowPurpleContainer,
    onPrimaryContainer = Color(0xFF21005D),
    secondary = Color(0xFF625B71),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFE8DEF8),
    onSecondaryContainer = Color(0xFF1D192B),
    background = Color(0xFFFFFBFE),
    surface = Color(0xFFFFFBFE),
    onBackground = Color(0xFF1C1B1F),
    onSurface = Color(0xFF1C1B1F)
)

private val DarkColorScheme = darkColorScheme(
    primary = Color(0xFFD0BCFF),
    onPrimary = Color(0xFF381E72),
    primaryContainer = Color(0xFF4F378B),
    onPrimaryContainer = EmuFlowPurpleContainer,
    secondary = Color(0xFFCCC2DC),
    onSecondary = Color(0xFF332D41),
    secondaryContainer = Color(0xFF4A4458),
    onSecondaryContainer = Color(0xFFE8DEF8),
    background = Color(0xFF1C1B1F),
    surface = Color(0xFF1C1B1F),
    onBackground = Color(0xFFE6E1E5),
    onSurface = Color(0xFFE6E1E5)
)

/**
 * EmuFlow Agent Material 3 thema.
 *
 * Ondersteunt:
 * - Dynamic Color (Android 12+, API 31+) — past aan de wallpaper-kleuren
 * - Dark mode via system-setting
 * - Fallback naar EmuFlow kleurpalet op oudere Android versies
 */
@Composable
fun EmuFlowAgentTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // Dynamic color beschikbaar op Android 12+ (onze minSdk is 30)
    dynamicColor: Boolean = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context)
            else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = MaterialTheme.typography, // Default Material 3 typography
        content = content
    )
}
