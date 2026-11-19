from pathlib import Path
import sys

root = Path(sys.argv[1])
java = root / "app/src/main/java/app/swaga/browser"

theme = r'''package app.swaga.browser.themes

import android.app.Activity
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.dp
import androidx.core.view.WindowCompat

enum class ThemeId(val title: String) {
    DARK("OLED"),
    LIGHT("Светлая"),
}

// Last option is a monochrome/black accent. It adapts to the theme to remain visible.
val AccentChoices = listOf(
    Color(0xFF3B82F6),
    Color(0xFF22A06B),
    Color(0xFF8B6FE8),
    Color(0xFFE07878),
    Color(0xFFD0A64B),
    Color(0xFF000000),
)

@Immutable
class SwagaColors(
    val bg: Color,
    val surface: Color,
    val surfaceHigh: Color,
    val text: Color,
    val dim: Color,
    val muted: Color,
    val outline: Color,
    val divider: Color,
    val accent: Color,
    val accentStrong: Color,
    val accentContainer: Color,
    val onAccentContainer: Color,
    val onAccent: Color,
    val success: Color,
    val successSoft: Color,
    val selected: Color,
    val isDark: Boolean,
)

val LocalSwaga = staticCompositionLocalOf<SwagaColors> { error("SwagaTheme is missing") }

fun swagaColors(theme: ThemeId, accentIndex: Int): SwagaColors {
    val rawAccent = AccentChoices[accentIndex.coerceIn(0, AccentChoices.lastIndex)]
    val blackAccent = accentIndex == AccentChoices.lastIndex
    val dark = theme == ThemeId.DARK

    val bg = if (dark) Color(0xFF000000) else Color(0xFFF1F3F6)
    val surface = if (dark) Color(0xFF101012) else Color(0xFFFFFFFF)
    val high = if (dark) Color(0xFF1A1A1F) else Color(0xFFF8F9FB)
    val text = if (dark) Color(0xFFF8FAFC) else Color(0xFF15171C)
    val dim = if (dark) Color(0xFFA1A1AA) else Color(0xFF5F6875)
    val muted = if (dark) Color(0xFF71717A) else Color(0xFF87909D)
    val outline = if (dark) Color(0xFF2B2B32) else Color(0xFFDDE2E9)
    val divider = if (dark) Color(0xFF24242A) else Color(0xFFE9ECF1)

    // Black accent becomes crisp white in OLED mode and true near-black in light mode.
    val accent = when {
        blackAccent && dark -> Color(0xFFF1F3F5)
        blackAccent -> Color(0xFF17191E)
        dark -> rawAccent
        else -> lerp(rawAccent, Color(0xFF111827), 0.22f)
    }
    val accentStrong = if (dark) lerp(accent, Color.White, 0.10f) else lerp(accent, Color.Black, 0.08f)
    val accentContainer = lerp(surface, accent, if (dark) 0.20f else 0.11f)
    val onAccent = if (accent.luminance() > 0.48f) Color(0xFF101114) else Color.White
    val onAccentContainer = if (accentContainer.luminance() > 0.48f) Color(0xFF17191E) else Color.White

    return SwagaColors(
        bg = bg,
        surface = surface,
        surfaceHigh = high,
        text = text,
        dim = dim,
        muted = muted,
        outline = outline,
        divider = divider,
        accent = accent,
        accentStrong = accentStrong,
        accentContainer = accentContainer,
        onAccentContainer = onAccentContainer,
        onAccent = onAccent,
        success = Color(0xFF22C55E),
        successSoft = Color(0xFF86EFAC),
        selected = accentContainer,
        isDark = dark,
    )
}

@Composable
fun SwagaTheme(theme: ThemeId, accentIndex: Int, content: @Composable () -> Unit) {
    val c = swagaColors(theme, accentIndex)
    val scheme = if (c.isDark) {
        darkColorScheme(
            primary = c.accent,
            onPrimary = c.onAccent,
            primaryContainer = c.accentContainer,
            onPrimaryContainer = c.onAccentContainer,
            inversePrimary = c.accentStrong,
            secondary = c.accent,
            onSecondary = c.onAccent,
            secondaryContainer = c.accentContainer,
            onSecondaryContainer = c.onAccentContainer,
            tertiary = c.accentStrong,
            onTertiary = c.onAccent,
            background = c.bg,
            onBackground = c.text,
            surface = c.surface,
            onSurface = c.text,
            surfaceVariant = c.surfaceHigh,
            onSurfaceVariant = c.dim,
            surfaceTint = c.accent,
            outline = c.outline,
        )
    } else {
        lightColorScheme(
            primary = c.accent,
            onPrimary = c.onAccent,
            primaryContainer = c.accentContainer,
            onPrimaryContainer = c.onAccentContainer,
            inversePrimary = c.accentStrong,
            secondary = c.accent,
            onSecondary = c.onAccent,
            secondaryContainer = c.accentContainer,
            onSecondaryContainer = c.onAccentContainer,
            tertiary = c.accentStrong,
            onTertiary = c.onAccent,
            background = c.bg,
            onBackground = c.text,
            surface = c.surface,
            onSurface = c.text,
            surfaceVariant = c.surfaceHigh,
            onSurfaceVariant = c.dim,
            surfaceTint = c.accent,
            outline = c.outline,
        )
    }

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as? Activity)?.window
            if (window != null) {
                window.statusBarColor = android.graphics.Color.TRANSPARENT
                window.navigationBarColor = c.bg.toArgbCompat()
                val ctrl = WindowCompat.getInsetsController(window, view)
                ctrl.isAppearanceLightStatusBars = !c.isDark
                ctrl.isAppearanceLightNavigationBars = !c.isDark
            }
        }
    }
    CompositionLocalProvider(LocalSwaga provides c) {
        MaterialTheme(colorScheme = scheme, content = content)
    }
}

private fun Color.toArgbCompat(): Int =
    android.graphics.Color.argb(
        (alpha * 255).toInt(),
        (red * 255).toInt(),
        (green * 255).toInt(),
        (blue * 255).toInt(),
    )

@Composable
fun Modifier.panel(shape: Shape = RoundedCornerShape(18.dp), elevated: Boolean = false): Modifier {
    val c = LocalSwaga.current
    return this
        .clip(shape)
        .background(if (elevated) c.surfaceHigh else c.surface)
        .border(1.dp, c.outline.copy(alpha = 0.58f), shape)
}

@Composable
fun Modifier.appButton(
    shape: Shape = RoundedCornerShape(16.dp),
    elevated: Boolean = false,
    onClick: () -> Unit,
): Modifier {
    val c = LocalSwaga.current
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val scale by animateFloatAsState(
        targetValue = if (pressed) 0.975f else 1f,
        animationSpec = spring(stiffness = 650f, dampingRatio = 0.78f),
        label = "oled-button-press",
    )
    return this
        .graphicsLayer { scaleX = scale; scaleY = scale }
        .clip(shape)
        .background(if (elevated) c.surfaceHigh else c.surface)
        .border(1.dp, c.outline.copy(alpha = 0.58f), shape)
        .clickable(interactionSource = interaction, indication = null, onClick = onClick)
}
'''
theme_path = java / "themes/SwagaTheme.kt"
theme_path.parent.mkdir(parents=True, exist_ok=True)
theme_path.write_text(theme.strip() + "\n", encoding="utf-8")

# Spread the selected accent through controls that previously used fixed green/blue styling.
for rel in ["ui/Sheets.kt", "ui/ProtectionSheet.kt"]:
    p = java / rel
    s = p.read_text(encoding="utf-8")
    s = s.replace("checkedTrackColor = c.success", "checkedTrackColor = c.accent")
    s = s.replace("checkedBorderColor = c.success", "checkedBorderColor = c.accent")
    s = s.replace("color = if (vm.trackingProtectionEnabled) c.successSoft else c.dim",
                  "color = if (vm.trackingProtectionEnabled) c.accentStrong else c.dim")
    s = s.replace("color = c.dim, fontSize = 12.sp)\n                }\n                Switch(",
                  "color = if (vm.trackingProtectionEnabled) c.accentStrong else c.dim, fontSize = 12.sp)\n                }\n                Switch(")
    p.write_text(s, encoding="utf-8")

# Make selected accent swatches visibly selected using the active accent itself.
p = java / "ui/Sheets.kt"
s = p.read_text(encoding="utf-8")
s = s.replace(
    ".then(if (vm.accentIndex == i) Modifier.border(3.dp, c.text, CircleShape) else Modifier)",
    ".then(if (vm.accentIndex == i) Modifier.border(3.dp, c.accent, CircleShape) else Modifier)"
)
p.write_text(s, encoding="utf-8")

# The focused address field now uses the chosen accent as a restrained focus ring.
p = java / "ui/BottomBar.kt"
s = p.read_text(encoding="utf-8")
s = s.replace(
    ".panel(RoundedCornerShape(22.dp))\n            .padding(horizontal = 8.dp),",
    ".panel(RoundedCornerShape(22.dp))\n            .then(if (focused) Modifier.border(1.dp, c.accent.copy(alpha = 0.85f), RoundedCornerShape(22.dp)) else Modifier)\n            .padding(horizontal = 8.dp),"
)
p.write_text(s, encoding="utf-8")

print("Refined OLED/light themes, removed Midnight, added monochrome accent and expanded accent propagation.")
