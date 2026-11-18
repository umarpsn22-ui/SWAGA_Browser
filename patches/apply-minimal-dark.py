from pathlib import Path
import sys

root = Path(sys.argv[1])
java = root / "app/src/main/java/app/swaga/browser"

def write(rel, content):
    p = java / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + "\n", encoding="utf-8")

def replace_file(rel, old, new):
    p = java / rel
    s = p.read_text(encoding="utf-8")
    if old not in s:
        raise SystemExit(f"Pattern not found in {rel}: {old[:70]!r}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8")

write("themes/SwagaTheme.kt", r'''package app.swaga.browser.themes

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
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.dp
import androidx.core.view.WindowCompat

enum class ThemeId(val title: String) {
    DARK("Тёмная"),
    MIDNIGHT("Полночь"),
    LIGHT("Светлая"),
}

val AccentChoices = listOf(
    Color(0xFF8EA8FF), Color(0xFF68BFAF), Color(0xFFB49AE8),
    Color(0xFFE18C82), Color(0xFFD3B36B),
)

@Immutable
class SwagaColors(
    val bg: Color,
    val surface: Color,
    val surfaceHigh: Color,
    val text: Color,
    val dim: Color,
    val outline: Color,
    val accent: Color,
    val onAccent: Color,
    val isDark: Boolean,
)

val LocalSwaga = staticCompositionLocalOf<SwagaColors> { error("SwagaTheme is missing") }

fun swagaColors(theme: ThemeId, accentIndex: Int): SwagaColors {
    val base = AccentChoices[accentIndex.coerceIn(0, AccentChoices.lastIndex)]
    return when (theme) {
        ThemeId.MIDNIGHT -> build(
            bg = Color(0xFF0B0D12), surface = Color(0xFF14171E), high = Color(0xFF1C2029),
            text = Color(0xFFE8EAF0), dim = Color(0xFF9299A8), outline = Color(0xFF292E39),
            accent = base, dark = true,
        )
        ThemeId.DARK -> build(
            bg = Color(0xFF101114), surface = Color(0xFF191B20), high = Color(0xFF22252C),
            text = Color(0xFFE9EAF0), dim = Color(0xFF969BA6), outline = Color(0xFF2D3038),
            accent = base, dark = true,
        )
        ThemeId.LIGHT -> build(
            bg = Color(0xFFF4F5F7), surface = Color(0xFFFFFFFF), high = Color(0xFFE9EBEF),
            text = Color(0xFF17191E), dim = Color(0xFF656B76), outline = Color(0xFFD9DCE2),
            accent = lerp(base, Color.Black, 0.3f), dark = false,
        )
    }
}

private fun build(
    bg: Color, surface: Color, high: Color, text: Color, dim: Color, outline: Color,
    accent: Color, dark: Boolean,
) = SwagaColors(
    bg = bg, surface = surface, surfaceHigh = high, text = text, dim = dim, outline = outline,
    accent = accent,
    onAccent = if (accent.luminance() > 0.5f) Color(0xFF101114) else Color.White,
    isDark = dark,
)

@Composable
fun SwagaTheme(theme: ThemeId, accentIndex: Int, content: @Composable () -> Unit) {
    val c = swagaColors(theme, accentIndex)
    val scheme = if (c.isDark) {
        darkColorScheme(
            primary = c.accent, onPrimary = c.onAccent,
            background = c.bg, onBackground = c.text,
            surface = c.surface, onSurface = c.text,
            surfaceVariant = c.surfaceHigh, onSurfaceVariant = c.dim,
            outline = c.outline,
        )
    } else {
        lightColorScheme(
            primary = c.accent, onPrimary = c.onAccent,
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
        .then(if (elevated) Modifier.shadow(2.dp, shape, clip = false) else Modifier)
        .clip(shape)
        .background(if (elevated) c.surfaceHigh else c.surface)
        .border(1.dp, c.outline.copy(alpha = 0.72f), shape)
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
        label = "button-press-scale",
    )
    return this
        .graphicsLayer { scaleX = scale; scaleY = scale }
        .clip(shape)
        .background(if (elevated) c.surfaceHigh else c.surface)
        .border(1.dp, c.outline.copy(alpha = 0.72f), shape)
        .clickable(interactionSource = interaction, indication = null, onClick = onClick)
}
''')

write("ui/AppOverlays.kt", r'''package app.swaga.browser.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.ProvideTextStyle
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import app.swaga.browser.themes.LocalSwaga

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppSheet(onDismiss: () -> Unit, content: @Composable ColumnScope.() -> Unit) {
    val c = LocalSwaga.current
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = c.surface,
        contentColor = c.text,
        tonalElevation = 0.dp,
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp),
        scrimColor = Color.Black.copy(alpha = 0.58f),
        dragHandle = null,
        contentWindowInsets = { WindowInsets(0, 0, 0, 0) },
    ) {
        Column(Modifier.fillMaxWidth().navigationBarsPadding()) {
            Box(
                Modifier.align(Alignment.CenterHorizontally)
                    .padding(top = 10.dp, bottom = 12.dp)
                    .width(34.dp).height(4.dp)
                    .background(c.dim.copy(alpha = 0.58f), CircleShape),
            )
            content()
        }
    }
}

@Composable
fun AppDialog(
    onDismissRequest: () -> Unit,
    title: @Composable () -> Unit,
    text: @Composable () -> Unit,
    confirmButton: @Composable () -> Unit,
    dismissButton: @Composable (() -> Unit)? = null,
) {
    val c = LocalSwaga.current
    AlertDialog(
        onDismissRequest = onDismissRequest,
        title = { ProvideTextStyle(MaterialTheme.typography.titleLarge.copy(color = c.text)) { title() } },
        text = { ProvideTextStyle(MaterialTheme.typography.bodyMedium.copy(color = c.text)) { text() } },
        confirmButton = confirmButton,
        dismissButton = dismissButton,
        containerColor = c.surface,
        titleContentColor = c.text,
        textContentColor = c.text,
        shape = RoundedCornerShape(22.dp),
    )
}
''')

# Remove legacy glass material preference; the old persisted value is ignored.
p = java / "BrowserViewModel.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("import app.swaga.browser.themes.MaterialId\n", "")
s = s.replace("    var materialId by mutableStateOf(MaterialId.GLASS)\n        private set\n", "")
s = s.replace('        materialId = runCatching { MaterialId.valueOf(prefs.getString("material", "") ?: "") }.getOrDefault(MaterialId.GLASS)\n', "")
s = s.replace('    fun setMaterial(m: MaterialId) { materialId = m; prefs.edit().putString("material", m.name).apply() }\n', "")
s = s.replace("var themeId by mutableStateOf(ThemeId.MIDNIGHT)", "var themeId by mutableStateOf(ThemeId.DARK)")
s = s.replace("}.getOrDefault(ThemeId.MIDNIGHT)", "}.getOrDefault(ThemeId.DARK)")
p.write_text(s, encoding="utf-8")

p = java / "MainActivity.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("SwagaTheme(vm.themeId, vm.materialId, vm.accentIndex)", "SwagaTheme(vm.themeId, vm.accentIndex)")
p.write_text(s, encoding="utf-8")

p = java / "ui/Sheets.kt"
s = p.read_text(encoding="utf-8").replace("import app.swaga.browser.themes.MaterialId\n", "")
start = s.find('            Group("Материал") {')
if start >= 0:
    end = s.find('            Group("Акцентный цвет") {', start)
    if end < 0: raise SystemExit("Accent selector not found after material selector")
    s = s[:start] + s[end:]
s = s.replace("GlassSheet(", "AppSheet(")
p.write_text(s, encoding="utf-8")

p = java / "ui/BottomBar.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("import app.swaga.browser.themes.glassButton\n", "")
s = s.replace("import app.swaga.browser.themes.liquidGlass\n", "")
s = s.replace("import app.swaga.browser.themes.panel\n", "import app.swaga.browser.themes.panel\nimport app.swaga.browser.themes.appButton\n")
s = s.replace("liquidGlass(menuShape, elevated = true, frost = 1.7f)", "panel(menuShape, elevated = true)")
s = s.replace("containerColor = Color.Transparent,\n                tonalElevation = 0.dp,\n                shadowElevation = 0.dp,", "containerColor = c.surface,\n                tonalElevation = 0.dp,\n                shadowElevation = 3.dp,")
s = s.replace("GlassDialog(", "AppDialog(").replace(".glassButton(", ".appButton(")
p.write_text(s, encoding="utf-8")

p = java / "ui/BrowserApp.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("import app.swaga.browser.themes.liquidBackdrop\n", "")
s = s.replace("                // Glass bars need something to sit on; the aurora drifts only on the start page.\n                .liquidBackdrop(animated = tab != null && tab.url == null && !showSwitcher)\n", "                .background(c.bg)\n")
p.write_text(s, encoding="utf-8")

p = java / "ui/TabSwitcher.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("import app.swaga.browser.themes.LiquidBackdrop\n", "")
s = s.replace("import app.swaga.browser.themes.glassButton\n", "import app.swaga.browser.themes.appButton\n")
s = s.replace("    Box(Modifier.fillMaxSize()) {\n    LiquidBackdrop()\n", "    Box(Modifier.fillMaxSize().background(c.bg)) {\n")
s = s.replace(".glassButton(", ".appButton(")
p.write_text(s, encoding="utf-8")

p = java / "ui/StartPage.kt"
s = p.read_text(encoding="utf-8")
s = s.replace("import app.swaga.browser.themes.glassButton\n", "import app.swaga.browser.themes.appButton\n")
s = s.replace("import app.swaga.browser.themes.glassTileBrush\n", "")
s = s.replace(".glassButton(", ".appButton(")
s = s.replace("    val px = with(androidx.compose.ui.platform.LocalDensity.current) { size.toPx() }\n", "")
s = s.replace(".background(glassTileBrush(c, androidx.compose.ui.geometry.Size(px, px)))", ".background(c.surfaceHigh)")
p.write_text(s, encoding="utf-8")

# Rename the visual system and remove the glass implementation itself.
for p in java.rglob("*.kt"):
    if p.name in {"LiquidGlass.kt", "GlassComponents.kt"}: continue
    s = p.read_text(encoding="utf-8")
    s = s.replace("GlassSheet(", "AppSheet(").replace("GlassDialog(", "AppDialog(")
    p.write_text(s, encoding="utf-8")
for rel in ["themes/LiquidGlass.kt", "ui/GlassComponents.kt"]:
    p = java / rel
    if p.exists(): p.unlink()

# Version identity for the redesigned build.
gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
g = g.replace("versionCode = 3", "versionCode = 4")
g = g.replace('versionName = "1.1.0-gecko"', 'versionName = "1.2.0-minimal-dark"')
gradle.write_text(g, encoding="utf-8")

# Fail the build if any old glass API survived.
for p in java.rglob("*.kt"):
    s = p.read_text(encoding="utf-8")
    for token in ["LiquidGlass", "GlassWindowBlur", "liquidBackdrop", "liquidGlass", "glassButton", "glassTileBrush", "MaterialId", "materialId", "GlassSheet", "GlassDialog"]:
        if token in s:
            raise SystemExit(f"Legacy glass reference {token!r} remains in {p.relative_to(root)}")
print("Minimal dark UI applied.")
