package com.team.life.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

private val LightColors = lightColorScheme(
    primary = BrandBlue,
    onPrimary = Color.White,
    primaryContainer = BrandBlueContainer,
    onPrimaryContainer = Color(0xFF0A2666),
    secondary = BrandTeal,
    secondaryContainer = BrandTealContainer,
    tertiary = PointsOrange,
    tertiaryContainer = PointsOrangeContainer,
    error = AlertPink,
    errorContainer = AlertPinkContainer,
    background = AppBackground,
    surface = Color.White,
    surfaceVariant = SurfaceContainer,
    outline = OutlineSoft,
    onSurface = Ink,
    onSurfaceVariant = MutedInk,
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFFAFC2FF),
    onPrimary = Color(0xFF0A2666),
    primaryContainer = Color(0xFF2B3D7E),
    onPrimaryContainer = BrandBlueContainer,
    secondary = Color(0xFF7FDCCF),
    secondaryContainer = Color(0xFF14524B),
    tertiary = Color(0xFFFFC46B),
    tertiaryContainer = Color(0xFF5A3D12),
    error = Color(0xFFFFB1C7),
    errorContainer = Color(0xFF5C1F33),
    background = Color(0xFF0F1218),
    surface = Color(0xFF171B24),
    surfaceVariant = Color(0xFF1F2430),
    outline = Color(0xFF2C3344),
    onSurface = Color(0xFFE6E8F0),
    onSurfaceVariant = Color(0xFFA6ADBF),
)

private val AppShapes = Shapes(
    extraSmall = RoundedCornerShape(4.dp),
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(22.dp),
)

@Composable
fun LifeAssistantTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit,
) {
    val context = LocalContext.current
    val colors = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && darkTheme -> dynamicDarkColorScheme(context)
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> dynamicLightColorScheme(context)
        darkTheme -> DarkColors
        else -> LightColors
    }
    MaterialTheme(colorScheme = colors, typography = AppTypography, shapes = AppShapes, content = content)
}
