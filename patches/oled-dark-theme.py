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
    MIDNIGHT("Полночь"),
    LIGHT("Светлая"),
}

val AccentChoices = listOf(
    Color(0xFF3B82F6), Color(0xFF68BFAF), Color(0xFFB49AE8),
    Color(0xFFE18C82), Color(0xFFD3B36B),
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
    val onAccent: Color,
    val success: Color,
    val successSoft: Color,
    val selected: Color,
    val isDark: Boolean,
)

val LocalSwaga = staticCompositionLocalOf<SwagaColors> { error("SwagaTheme is missing") }

fun swagaColors(theme: ThemeId, accentIndex: Int): SwagaColors {
    val base = AccentChoices[accentIndex.coerceIn(0, AccentChoices.lastIndex)]
    return when (theme) {
        ThemeId.MIDNIGHT -> build(
            bg = Color(0xFF000000), surface = Color(0xFF111318), high = Color(0xFF1B1D23),
            text = Color(0xFFFFFFFF), dim = Color(0xFF9CA3AF), muted = Color(0xFF6B7280),
            outline = Color(0xFF303036), divider = Color(0xFF27272A),
            accent = base, dark = true,
        )
        ThemeId.DARK -> build(
            bg = Color(0xFF000000), surface = Color(0xFF141416), high = Color(0xFF1F1F23),
            text = Color(0xFFFFFFFF), dim = Color(0xFF9CA3AF), muted = Color(0xFF6B7280),
            outline = Color(0xFF303036), divider = Color(0xFF27272A),
            accent = base, dark = true,
        )
        ThemeId.LIGHT -> build(
            bg = Color(0xFFF4F5F7), surface = Color(0xFFFFFFFF), high = Color(0xFFE9EBEF),
            text = Color(0xFF17191E), dim = Color(0xFF656B76), muted = Color(0xFF8A909B),
            outline = Color(0xFFD9DCE2), divider = Color(0xFFE4E6EB),
            accent = lerp(base, Color.Black, 0.3f), dark = false,
        )
    }
}

private fun build(
    bg: Color, surface: Color, high: Color, text: Color, dim: Color, muted: Color,
    outline: Color, divider: Color, accent: Color, dark: Boolean,
) = SwagaColors(
    bg = bg, surface = surface, surfaceHigh = high, text = text, dim = dim,
    muted = muted, outline = outline, divider = divider, accent = accent,
    onAccent = if (accent.luminance() > 0.5f) Color(0xFF101114) else Color.White,
    success = Color(0xFF22C55E), successSoft = Color(0xFF86EFAC),
    selected = if (dark) Color(0xFF172554) else Color(0xFFDBEAFE),
    isDark = dark,
)

@Composable
fun SwagaTheme(theme: ThemeId, accentIndex: Int, content: @Composable () -> Unit) {
    val c = swagaColors(theme, accentIndex)
    val scheme = if (c.isDark) {
        darkColorScheme(
            primary = c.accent, onPrimary = c.onAccent,
            secondary = c.success, onSecondary = Color(0xFF052E16),
            background = c.bg, onBackground = c.text,
            surface = c.surface, onSurface = c.text,
            surfaceVariant = c.surfaceHigh, onSurfaceVariant = c.dim,
            outline = c.outline,
        )
    } else {
        lightColorScheme(
            primary = c.accent, onPrimary = c.onAccent,
            secondary = c.success, onSecondary = Color(0xFF052E16),
            background = c.bg, onBackground = c.text,
            surface = c.surface, onSurface = c.text,
            surfaceVariant = c.surfaceHigh, onSurfaceVariant = c.dim,
            outline = c.outline,
        )
    }
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as? Activity)?.window
            if (window != null) {
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

@Composable
fun Modifier.panel(shape: Shape = RoundedCornerShape(18.dp), elevated: Boolean = false): Modifier {
    val c = LocalSwaga.current
    return this
        .clip(shape)
        .background(if (elevated) c.surfaceHigh else c.surface)
        .border(1.dp, c.outline.copy(alpha = 0.48f), shape)
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
        .border(1.dp, c.outline.copy(alpha = 0.48f), shape)
        .clickable(interactionSource = interaction, indication = null, onClick = onClick)
}
'''
p = java / "themes/SwagaTheme.kt"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(theme.strip() + "\n", encoding="utf-8")

# Apply consistent green enabled switches and OLED chip selection without changing layout.
for rel in ["ui/Sheets.kt", "ui/ProtectionSheet.kt"]:
    p = java / rel
    s = p.read_text(encoding="utf-8")
    if "import androidx.compose.material3.SwitchDefaults" not in s:
        s = s.replace("import androidx.compose.material3.Switch\n",
                      "import androidx.compose.material3.Switch\nimport androidx.compose.material3.SwitchDefaults\n")
    s = s.replace(
        "Switch(checked = vm.trackingProtectionEnabled, onCheckedChange = vm::setTrackingProtection)",
        """Switch(
                    checked = vm.trackingProtectionEnabled,
                    onCheckedChange = vm::setTrackingProtection,
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = Color.White,
                        checkedTrackColor = c.success,
                        checkedBorderColor = c.success,
                        uncheckedThumbColor = c.dim,
                        uncheckedTrackColor = c.surfaceHigh,
                        uncheckedBorderColor = c.outline,
                    ),
                )"""
    )
    if rel == "ui/Sheets.kt":
        if "import androidx.compose.material3.FilterChipDefaults" not in s:
            s = s.replace("import androidx.compose.material3.FilterChip\n",
                          "import androidx.compose.material3.FilterChip\nimport androidx.compose.material3.FilterChipDefaults\n")
        s = s.replace(
            "FilterChip(selected = vm.themeId == t, onClick = { vm.setTheme(t) }, label = { Text(t.title) })",
            """FilterChip(
                            selected = vm.themeId == t,
                            onClick = { vm.setTheme(t) },
                            label = { Text(t.title) },
                            colors = FilterChipDefaults.filterChipColors(
                                containerColor = c.surfaceHigh,
                                labelColor = c.dim,
                                selectedContainerColor = c.selected,
                                selectedLabelColor = c.text,
                                selectedLeadingIconColor = c.accent,
                            ),
                            border = FilterChipDefaults.filterChipBorder(
                                enabled = true,
                                selected = vm.themeId == t,
                                borderColor = c.outline,
                                selectedBorderColor = c.accent.copy(alpha = 0.65f),
                            ),
                        )"""
        )
    p.write_text(s, encoding="utf-8")

# Make active protection labels green, while leaving the main navigation and layout untouched.
p = java / "ui/Sheets.kt"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'color = if (vm.trackingProtectionEnabled) c.accent else c.dim,',
    'color = if (vm.trackingProtectionEnabled) c.successSoft else c.dim,'
)
p.write_text(s, encoding="utf-8")

p = java / "ui/ProtectionSheet.kt"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'color = c.dim, fontSize = 12.sp)\n                Switch(',
    'color = if (vm.trackingProtectionEnabled) c.successSoft else c.dim, fontSize = 12.sp)\n                Switch('
)
p.write_text(s, encoding="utf-8")

print("OLED Dark theme applied: pure black surfaces, blue selection, green active states.")
