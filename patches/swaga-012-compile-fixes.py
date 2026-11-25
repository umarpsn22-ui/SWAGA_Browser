from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
base = root / "app/src/main/java/app/swaga/browser"

def replace(path: Path, old: str, new: str, label: str) -> None:
    source = path.read_text(encoding="utf-8")
    if new in source:
        return
    if old not in source:
        raise SystemExit(f"Expected source fragment missing: {label}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")

# SelectionContainer is part of foundation.text.selection, not foundation.selection.
replace(
    base / "ai/SwagaAiSheet.kt",
    "import androidx.compose.foundation.selection.SelectionContainer",
    "import androidx.compose.foundation.text.selection.SelectionContainer",
    "SelectionContainer import",
)

# The start page runs the per-keystroke Animatable from a composable effect.
replace(
    base / "ui/StartPage.kt",
    "import androidx.compose.runtime.Composable\n",
    "import androidx.compose.runtime.Composable\nimport androidx.compose.runtime.LaunchedEffect\n",
    "LaunchedEffect import",
)

mini = base / "ui/SwagaMiniPlayer.kt"
source = mini.read_text(encoding="utf-8")
source = source.replace("import androidx.compose.material.icons.filled.Pause\n", "")
source = source.replace("import androidx.compose.material.icons.filled.SkipNext\n", "")
source = source.replace("import androidx.compose.material.icons.filled.SkipPrevious\n", "")
source = source.replace(
    'Icon(Icons.Filled.SkipPrevious, contentDescription = "Предыдущая", tint = c.text, modifier = Modifier.size(18.dp))',
    'Text("|◀", color = c.text, fontSize = 12.sp)',
)
source = source.replace(
    'Icon(if (SwagaMusicPlayer.isPlaying) Icons.Filled.Pause else Icons.Filled.PlayArrow, contentDescription = if (SwagaMusicPlayer.isPlaying) "Пауза" else "Продолжить", tint = c.accent, modifier = Modifier.size(21.dp))',
    'if (SwagaMusicPlayer.isPlaying) Text("Ⅱ", color = c.accent, fontSize = 18.sp) else Icon(Icons.Filled.PlayArrow, contentDescription = "Продолжить", tint = c.accent, modifier = Modifier.size(21.dp))',
)
source = source.replace(
    'Icon(Icons.Filled.SkipNext, contentDescription = "Следующая", tint = c.text, modifier = Modifier.size(18.dp))',
    'Text("▶|", color = c.text, fontSize = 12.sp)',
)
if "Icons.Filled.SkipPrevious" in source or "Icons.Filled.SkipNext" in source or "Icons.Filled.Pause" in source:
    raise SystemExit("Mini-player still references unavailable material icons")
mini.write_text(source, encoding="utf-8")
print("Fixed Compose selection/effect imports and replaced unavailable mini-player glyph icons.")
