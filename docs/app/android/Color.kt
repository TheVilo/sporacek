// šporáček — farebné tokeny pre Jetpack Compose (Material 3)
// Zdroj pravdy: docs/app/tokens.json (hodnoty overené proti WCAG AA).
// Súbor je referenčná implementácia na skopírovanie do Android projektu
// (balíček si uprav). Nemeň hodnoty tu bez zmeny tokens.json + tokens.css.
package sk.sporacek.app.ui.theme

import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

// ---- primitíva značky (nepoužívaj priamo v obrazovkách — len cez tému) ----
object BrandColors {
    val Forest = Color(0xFF204432)
    val ForestDeep = Color(0xFF163021)
    val ForestInk = Color(0xFF0E1F16)
    val Terracotta = Color(0xFFBA5F3F)
    val TerracottaDark = Color(0xFF8A4429)
    val Sage = Color(0xFF7FA38C)
    val Wheat = Color(0xFFE7D6B4)
    val Cream = Color(0xFFFAF6EE)
    val Sand = Color(0xFFF4EFE3)
    val Linen = Color(0xFFE8E3D8)
}

/**
 * Sémantické farby šporáčka nad rámec Material3 ColorScheme (odznaky, nav,
 * warning pár…). Obrazovky ich čítajú cez [LocalSporacekColors] — nikdy
 * BrandColors priamo. Rovnaké roly ako --color-* na webe.
 */
@Immutable
data class SporacekColors(
    val bg: Color,
    val surface: Color,
    val surface2: Color,
    val text: Color,
    val textSecondary: Color,
    val textMuted: Color,
    val textFaint: Color,
    val textInverse: Color,
    val primary: Color,
    val accent: Color,
    val accentPressed: Color,
    val secondaryAccent: Color,
    val success: Color,
    val successInk: Color,
    val warningBg: Color,
    val warningText: Color,
    val badgeBg: Color,
    val badgeText: Color,
    val border: Color,
    val borderStrong: Color,
    val navInactive: Color,
    val navActive: Color,
)

val SporacekLightColors = SporacekColors(
    bg = Color(0xFFFAF6EE),
    surface = Color(0xFFFFFFFF),
    surface2 = Color(0xFFF4EFE3),
    text = Color(0xFF204432),
    textSecondary = Color(0xFF4B6357),
    textMuted = Color(0xFF7A8A80),
    textFaint = Color(0xFF9AA8A0),          // len dekoratívne (ikony), nie text
    textInverse = Color(0xFFFAF6EE),
    primary = Color(0xFF204432),
    accent = Color(0xFFBA5F3F),
    accentPressed = Color(0xFF8A4429),
    secondaryAccent = Color(0xFF7FA38C),
    success = Color(0xFF7FA38C),
    successInk = Color(0xFF0E1F16),
    warningBg = Color(0xFFF0E6D2),
    warningText = Color(0xFF816135),
    badgeBg = Color(0xFFE7D6B4),
    badgeText = Color(0xFF204432),
    border = Color(0x14204432),             // forest @ 8 %
    borderStrong = Color(0x33204432),       // forest @ 20 %
    navInactive = Color(0xFF68756E),        // 4.82:1 na bielej — nie textFaint!
    navActive = Color(0xFF204432),
)

// Tmavý režim: odvodený cez OKLCH z rovnakých kotviacich farieb (rovnaký
// odtieň, upravená svetlosť) — pozadia sú tmavozelené (identita brandu),
// akcenty zosvetlené kvôli kontrastu. Elevácia = svetlejší surface, nie tieň.
val SporacekDarkColors = SporacekColors(
    bg = Color(0xFF030905),
    surface = Color(0xFF0A160F),
    surface2 = Color(0xFF15231B),
    text = Color(0xFFF0ECE4),
    textSecondary = Color(0xFFC2BDB2),
    textMuted = Color(0xFF8B958F),
    textFaint = Color(0xFF636B67),
    textInverse = Color(0xFF0A160F),
    primary = Color(0xFF8DAE9B),
    accent = Color(0xFFD1785A),
    accentPressed = Color(0xFFAC5B3E),
    secondaryAccent = Color(0xFF6F8F7B),
    success = Color(0xFF6F8F7B),
    successInk = Color(0xFF0A160F),
    warningBg = Color(0xFFCFB28D),
    warningText = Color(0xFF3A2400),
    badgeBg = Color(0xFFCBBC9D),
    badgeText = Color(0xFF05160D),
    border = Color(0xFF25312A),
    borderStrong = Color(0xFF517260),
    navInactive = Color(0xFF636B67),
    navActive = Color(0xFFF0ECE4),
)

val LocalSporacekColors = staticCompositionLocalOf { SporacekLightColors }
