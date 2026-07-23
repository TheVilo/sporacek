// šporáček — typografia pre Jetpack Compose (Material 3)
// Zdroj: docs/app/tokens.json. Fonty: Plus Jakarta Sans (UI, variabilné váhy
// 400–800) + Source Serif 4 (akcent — veľké čísla úspor, citáty).
// Fonty pridaj cez androidx.compose.ui.text.googlefonts (Downloadable Fonts),
// nech sa nebalia do APK:
//   implementation("androidx.compose.ui:ui-text-google-fonts:<verzia>")
package sk.sporacek.app.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.googlefonts.Font
import androidx.compose.ui.text.googlefonts.GoogleFont
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import sk.sporacek.app.R

private val fontProvider = GoogleFont.Provider(
    providerAuthority = "com.google.android.gms.fonts",
    providerPackage = "com.google.android.gms",
    certificates = R.array.com_google_android_gms_fonts_certs,
)

val JakartaSans = FontFamily(
    Font(GoogleFont("Plus Jakarta Sans"), fontProvider, FontWeight.Normal),
    Font(GoogleFont("Plus Jakarta Sans"), fontProvider, FontWeight.Medium),
    Font(GoogleFont("Plus Jakarta Sans"), fontProvider, FontWeight.SemiBold),
    Font(GoogleFont("Plus Jakarta Sans"), fontProvider, FontWeight.Bold),
    Font(GoogleFont("Plus Jakarta Sans"), fontProvider, FontWeight.ExtraBold),
)

val SourceSerif = FontFamily(
    Font(GoogleFont("Source Serif 4"), fontProvider, FontWeight.Medium),
    Font(GoogleFont("Source Serif 4"), fontProvider, FontWeight.SemiBold),
)

// Mapovanie rolí z UI kitu na Material3 Typography.
// (h1→displaySmall, h2/h3→headline*, title→titleLarge, subtitle→titleMedium,
//  bodyLarge/body→body*, caption→labelMedium, micro→labelSmall)
val SporacekTypography = Typography(
    displaySmall = TextStyle(   // H1 „Poďme ušetriť"
        fontFamily = JakartaSans, fontWeight = FontWeight.ExtraBold,
        fontSize = 32.sp, lineHeight = 33.sp, letterSpacing = (-0.03).em,
    ),
    headlineMedium = TextStyle( // H2 sekcia „Jedálniček na dnes"
        fontFamily = JakartaSans, fontWeight = FontWeight.ExtraBold,
        fontSize = 22.sp, lineHeight = 24.sp, letterSpacing = (-0.02).em,
    ),
    headlineSmall = TextStyle(  // H3 titul karty
        fontFamily = JakartaSans, fontWeight = FontWeight.ExtraBold,
        fontSize = 22.sp, lineHeight = 25.sp, letterSpacing = (-0.02).em,
    ),
    titleLarge = TextStyle(     // Title „Poďme nakupovať"
        fontFamily = JakartaSans, fontWeight = FontWeight.ExtraBold,
        fontSize = 20.sp, lineHeight = 23.sp, letterSpacing = (-0.02).em,
    ),
    titleMedium = TextStyle(    // Subtitle / text CTA
        fontFamily = JakartaSans, fontWeight = FontWeight.Bold,
        fontSize = 17.sp, lineHeight = 22.sp, letterSpacing = (-0.01).em,
    ),
    bodyLarge = TextStyle(
        fontFamily = JakartaSans, fontWeight = FontWeight.SemiBold,
        fontSize = 16.sp, lineHeight = 24.sp,
    ),
    bodyMedium = TextStyle(
        fontFamily = JakartaSans, fontWeight = FontWeight.Medium,
        fontSize = 14.sp, lineHeight = 22.sp,
    ),
    labelMedium = TextStyle(    // Caption „30 min · 2 porcie · 8 surovín"
        fontFamily = JakartaSans, fontWeight = FontWeight.SemiBold,
        fontSize = 12.sp, lineHeight = 17.sp,
    ),
    labelSmall = TextStyle(     // Micro „3 jedlá zostávajú"
        fontFamily = JakartaSans, fontWeight = FontWeight.Bold,
        fontSize = 11.sp, lineHeight = 14.sp,
    ),
)
