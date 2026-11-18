from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
java = root / "app/src/main/java/app/swaga/browser"

theme = java / "themes/SwagaTheme.kt"
s = theme.read_text(encoding="utf-8")
for line in [
    "import androidx.compose.animation.core.animateFloatAsState\n",
    "import androidx.compose.animation.core.spring\n",
    "import androidx.compose.foundation.interaction.MutableInteractionSource\n",
    "import androidx.compose.foundation.interaction.collectIsPressedAsState\n",
    "import androidx.compose.runtime.getValue\n",
    "import androidx.compose.runtime.remember\n",
    "import androidx.compose.ui.draw.shadow\n",
    "import androidx.compose.ui.graphics.graphicsLayer\n",
]:
    s = s.replace(line, "")
s, count = re.subn(
    r"@Composable\nfun Modifier\.panel\(.*?\n}\n\n@Composable\nfun Modifier\.appButton\(.*?\n}\n?$",
    '''@Composable
fun Modifier.panel(shape: Shape = RoundedCornerShape(18.dp), elevated: Boolean = false): Modifier {
    val c = LocalSwaga.current
    return this
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
    return this
        .clip(shape)
        .background(if (elevated) c.surfaceHigh else c.surface)
        .border(1.dp, c.outline.copy(alpha = 0.72f), shape)
        .clickable(onClick = onClick)
}
''',
    s, count=1, flags=re.S,
)
if count != 1 or any(x in s for x in ["animateFloatAsState", "graphicsLayer", "Modifier.shadow"]):
    raise SystemExit("Could not remove per-control Compose animation/shadow layers")
theme.write_text(s, encoding="utf-8")

# Avoid a continuous MediaPlayer/SurfaceView decoder on low-memory phones.
# The animated hero remains enabled on devices with at least 4 GiB RAM.
start = java / "ui/StartPage.kt"
s = start.read_text(encoding="utf-8")
s = s.replace("import android.net.Uri\n", "import android.app.ActivityManager\nimport android.content.Context\nimport android.net.Uri\n")
s = s.replace("import androidx.compose.foundation.background\n", "import androidx.compose.foundation.Image\nimport androidx.compose.foundation.background\n")
s = s.replace("import androidx.compose.ui.platform.LocalContext\n", "import androidx.compose.ui.platform.LocalContext\nimport androidx.compose.ui.res.painterResource\n")
old = '''private fun SwagaHeroVideo() {
    val context = LocalContext.current
    val videoView = remember(context) {
'''
new = '''private fun SwagaHeroVideo() {
    val context = LocalContext.current
    val useStaticHero = remember(context) {
        val manager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memory = ActivityManager.MemoryInfo()
        manager.getMemoryInfo(memory)
        memory.totalMem < 4L * 1024L * 1024L * 1024L
    }
    if (useStaticHero) {
        Image(
            painter = painterResource(R.drawable.ic_launcher_foreground),
            contentDescription = null,
            modifier = Modifier.size(56.dp).clip(RoundedCornerShape(15.dp)),
        )
        return
    }
    val videoView = remember(context) {
'''
if old not in s:
    raise SystemExit("SwagaHeroVideo anchor not found")
s = s.replace(old, new, 1)
start.write_text(s, encoding="utf-8")

bottom = java / "ui/BottomBar.kt"
s = bottom.read_text(encoding="utf-8").replace("shadowElevation = 3.dp,", "shadowElevation = 0.dp,")
bottom.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle.kts"
s = gradle.read_text(encoding="utf-8")
old = '''    buildTypes {
        release { isMinifyEnabled = false }
    }
'''
new = '''    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }
'''
if old not in s:
    raise SystemExit("Release buildTypes block not found")
s = s.replace(old, new, 1)
gradle.write_text(s, encoding="utf-8")

print("Low-RAM UI optimizations applied: lightweight click targets, no elevation shadows, static hero below 4 GiB RAM, installable release signing.")
