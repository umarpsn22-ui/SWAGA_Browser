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

# Keep the original Swaga hero video on every device so the mascot is never
# replaced by the generic launcher icon. The Compose/control optimizations
# below remain active on low-memory devices.
start = java / "ui/StartPage.kt"
s = start.read_text(encoding="utf-8")
s = s.replace("import android.app.ActivityManager\n", "")
s = s.replace("import android.content.Context\n", "")
s = s.replace("import androidx.compose.foundation.Image\n", "")
s = s.replace("import androidx.compose.ui.res.painterResource\n", "")
old = """private fun SwagaHeroVideo() {
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
"""
new = """private fun SwagaHeroVideo() {
    val context = LocalContext.current
    val videoView = remember(context) {
"""
if (old not in s) {
  throw new Error("Expected low-RAM mascot replacement block not found; refusing unsafe edit");
}
s = s.replace(old, new, 1)
start.write_text(s, encoding="utf-8")
