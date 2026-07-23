// šporáček — Material3 téma pre Jetpack Compose
// Zdroj: docs/app/tokens.json. Prepínanie svetlý/tmavý: default podľa
// systému (isSystemInDarkTheme), manuálna voľba používateľa má prednosť —
// rovnaké pravidlo ako na webe (prefers-color-scheme vs. data-theme).
package sk.sporacek.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.unit.dp

// rádiusy z UI kitu: sm 10 / md 14 / lg 18 / xl 20 / 2xl 24 / pill 999
val SporacekShapes = Shapes(
    extraSmall = RoundedCornerShape(10.dp),
    small = RoundedCornerShape(14.dp),
    medium = RoundedCornerShape(18.dp),
    large = RoundedCornerShape(20.dp),
    extraLarge = RoundedCornerShape(24.dp),
)

private fun lightScheme() = lightColorScheme(
    primary = SporacekLightColors.primary,
    onPrimary = SporacekLightColors.textInverse,
    secondary = SporacekLightColors.secondaryAccent,
    onSecondary = SporacekLightColors.successInk,
    tertiary = SporacekLightColors.accent,
    onTertiary = androidx.compose.ui.graphics.Color.White,
    background = SporacekLightColors.bg,
    onBackground = SporacekLightColors.text,
    surface = SporacekLightColors.surface,
    onSurface = SporacekLightColors.text,
    surfaceVariant = SporacekLightColors.surface2,
    onSurfaceVariant = SporacekLightColors.textSecondary,
    outline = SporacekLightColors.borderStrong,
    outlineVariant = SporacekLightColors.border,
    error = SporacekLightColors.accent,          // zámerné: terracotta = aj error (viď dizajn)
    onError = androidx.compose.ui.graphics.Color.White,
)

private fun darkScheme() = darkColorScheme(
    primary = SporacekDarkColors.primary,
    onPrimary = SporacekDarkColors.textInverse,
    secondary = SporacekDarkColors.secondaryAccent,
    onSecondary = SporacekDarkColors.successInk,
    tertiary = SporacekDarkColors.accent,
    onTertiary = androidx.compose.ui.graphics.Color.White,
    background = SporacekDarkColors.bg,
    onBackground = SporacekDarkColors.text,
    surface = SporacekDarkColors.surface,
    onSurface = SporacekDarkColors.text,
    surfaceVariant = SporacekDarkColors.surface2,
    onSurfaceVariant = SporacekDarkColors.textSecondary,
    outline = SporacekDarkColors.borderStrong,
    outlineVariant = SporacekDarkColors.border,
    error = SporacekDarkColors.accent,
    onError = androidx.compose.ui.graphics.Color.White,
)

@Composable
fun SporacekTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val sporacekColors = if (darkTheme) SporacekDarkColors else SporacekLightColors
    CompositionLocalProvider(LocalSporacekColors provides sporacekColors) {
        MaterialTheme(
            colorScheme = if (darkTheme) darkScheme() else lightScheme(),
            typography = SporacekTypography,
            shapes = SporacekShapes,
            content = content,
        )
    }
}

// Použitie v obrazovke:
//   val c = LocalSporacekColors.current
//   Text("…", color = c.textMuted)
// Poznámka k plynulosti: dátové triedy z API označ @Immutable / používaj
// ImmutableList, LazyColumn vždy s key = { it.slug } — bez toho Compose
// prerenderúva celé zoznamy a scroll sa seká.
