from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root/'app/src/main/java/app/swaga/browser/ai/SwagaAiSheet.kt'
s = p.read_text()

imports = [
    'import androidx.compose.ui.text.AnnotatedString',
    'import androidx.compose.ui.text.SpanStyle',
    'import androidx.compose.ui.text.buildAnnotatedString',
    'import androidx.compose.ui.text.font.FontFamily',
    'import androidx.compose.ui.text.font.FontStyle',
]
for item in imports:
    if item not in s:
        s = s.replace('import androidx.compose.ui.text.font.FontWeight', item+'\nimport androidx.compose.ui.text.font.FontWeight', 1)

helper = r'''
private fun aiInlineMarkdown(value: String, accent: Color): AnnotatedString = buildAnnotatedString {
    val pattern = Regex("""(\*\*.+?\*\*|\x60[^\x60]+\x60|\*[^*]+\*)""")
    var cursor = 0
    pattern.findAll(value).forEach { match ->
        append(value.substring(cursor, match.range.first))
        val token = match.value
        when {
            token.startsWith("**") -> {
                pushStyle(SpanStyle(fontWeight = FontWeight.Bold))
                append(token.substring(2, token.length - 2))
                pop()
            }
            token.firstOrNull() == 96.toChar() -> {
                pushStyle(SpanStyle(fontFamily = FontFamily.Monospace, color = accent, background = accent.copy(alpha = 0.12f)))
                append(token.substring(1, token.length - 1))
                pop()
            }
            token.startsWith("*") -> {
                pushStyle(SpanStyle(fontStyle = FontStyle.Italic))
                append(token.substring(1, token.length - 1))
                pop()
            }
        }
        cursor = match.range.last + 1
    }
    append(value.substring(cursor))
}
'''
if 'private fun aiInlineMarkdown(' not in s:
    s = s.replace('@OptIn(ExperimentalMaterial3Api::class)', helper+'\n\n@OptIn(ExperimentalMaterial3Api::class)', 1)

bubble = s.index('private fun AiMessageBubble(')
needle = '    val totalWords = remember(paragraphs) { paragraphs.sumOf { it.size } }'
if 'val sourceLines = remember(message.content)' not in s[bubble:]:
    s = s.replace(needle, '    val sourceLines = remember(message.content) { message.content.lines() }\n'+needle, 1)

start_marker = '                SelectionContainer {\n                    Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {'
start = s.index(start_marker, bubble)
end_marker = '''                        if (isRevealing) {
                            Text("▍", color = colors.accent, fontSize = 13.sp, lineHeight = 19.sp)
                        }
                    }
                }'''
end = s.index(end_marker, start) + len(end_marker)
replacement = r'''                SelectionContainer {
                    Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                        var ordinal = 0
                        var inCodeBlock = false
                        sourceLines.forEach { sourceLine ->
                            val lineWords = Regex("""\S+""").findAll(sourceLine).toList()
                            val trimmed = sourceLine.trimStart()
                            val isFence = trimmed.length >= 3 && trimmed.take(3).all { it == 96.toChar() }
                            if (isFence) {
                                inCodeBlock = !inCodeBlock
                                Spacer(Modifier.height(3.dp))
                            } else if (sourceLine.isBlank()) {
                                Spacer(Modifier.height(7.dp))
                            } else {
                                val shownCount = if (!animateText) lineWords.size else (visibleWords - ordinal).coerceIn(0, lineWords.size)
                                if (shownCount > 0) {
                                    val endIndex = if (shownCount >= lineWords.size) sourceLine.length else lineWords[shownCount - 1].range.last + 1
                                    val shownLine = sourceLine.substring(0, endIndex)
                                    val bullet = Regex("""^\s*[-*•]\s+""").find(shownLine)
                                    val number = Regex("""^\s*\d+[.)]\s+""").find(shownLine)
                                    when {
                                        inCodeBlock -> Box(
                                            Modifier.fillMaxWidth().clip(RoundedCornerShape(9.dp))
                                                .background(colors.bg).padding(horizontal = 10.dp, vertical = 8.dp)
                                        ) {
                                            Text(shownLine, color = colors.text, fontSize = 12.sp, lineHeight = 17.sp, fontFamily = FontFamily.Monospace)
                                        }
                                        bullet != null -> Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Text("•", color = colors.accent, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                                            Text(aiInlineMarkdown(shownLine.substring(bullet.range.last + 1), colors.accent), color = colors.text, fontSize = 13.sp, lineHeight = 19.sp)
                                        }
                                        number != null -> Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Text(number.value.trim(), color = colors.accent, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                                            Text(aiInlineMarkdown(shownLine.substring(number.range.last + 1), colors.accent), color = colors.text, fontSize = 13.sp, lineHeight = 19.sp)
                                        }
                                        trimmed.startsWith("#") -> Text(
                                            aiInlineMarkdown(shownLine.trimStart().trimStart('#').trimStart(), colors.accent),
                                            color = colors.text, fontSize = 15.sp, lineHeight = 21.sp, fontWeight = FontWeight.Bold
                                        )
                                        else -> Text(
                                            aiInlineMarkdown(shownLine, colors.accent),
                                            color = colors.text, fontSize = 13.sp, lineHeight = 19.sp
                                        )
                                    }
                                }
                            }
                            ordinal += lineWords.size
                        }
                        if (isRevealing) {
                            Text("▍", color = colors.accent, fontSize = 13.sp, lineHeight = 19.sp)
                        }
                    }
                }'''
s = s[:start] + replacement + s[end:]
p.write_text(s)
print('AI messages now preserve paragraphs, headings, ordered/unordered lists, inline emphasis and fenced code blocks while retaining progressive word reveal.')
