from pathlib import Path
import sys

p = Path(sys.argv[1])/'app/src/main/java/app/swaga/browser/ui/StartPage.kt'
s = p.read_text()
def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit('Chrome start-page patch could not find '+label)
    s = s.replace(old, new, 1)

replace_once(
    '''        .padding(top = 14.dp, bottom = 4.dp)
        .panel(RoundedCornerShape(22.dp), elevated = true)
        .padding(horizontal = 14.dp, vertical = 8.dp),''',
    '''        .padding(top = 14.dp, bottom = 8.dp)
        .padding(horizontal = 2.dp, vertical = 2.dp),''',
    'header surface'
)
replace_once('"#SWAGA_Browser"', '"SwagaBrowser"', 'brand title')
replace_once(
    '''      Text(
        "Высокий шанс на свагу,#SWAGA_Browser",
        color = c.dim,
        fontSize = 10.sp,
        fontWeight = FontWeight.Medium,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis,
      )
''',
    '',
    'decorative tagline'
)
replace_once('Spacer(Modifier.height(18.dp))\n  SwagaHero', 'Spacer(Modifier.height(8.dp))\n  SwagaHero', 'hero top spacing')
replace_once('Spacer(Modifier.height(14.dp))\n\n            Row(', 'Spacer(Modifier.height(9.dp))\n\n            Row(', 'hero bottom spacing')
replace_once('Modifier.fillMaxWidth().height(106.dp)', 'Modifier.fillMaxWidth().height(76.dp)', 'hero row height')
replace_once('fontSize = 46.sp,', 'fontSize = 31.sp,', 'hero wordmark size')
replace_once('letterSpacing = (-3.6).sp,', 'letterSpacing = (-2.2).sp,', 'hero wordmark spacing')
replace_once('OrehMascot(Modifier.size(112.dp))', 'OrehMascot(Modifier.size(76.dp))', 'Oreh mascot size')
replace_once('modifier = Modifier.size(112.dp),', 'modifier = Modifier.size(76.dp),', 'animated hero size')
replace_once('''            .background(c.surfaceHigh)
            .padding(vertical = 6.dp),''', '''            .background(Color.Transparent)
            .padding(vertical = 5.dp),''', 'shortcut tile surface')
replace_once('.height(82.dp)\n            .combinedClickable', '.height(76.dp)\n            .combinedClickable', 'shortcut tile height')
s = s.replace('Text("+ Настроить сайты", color = c.accent, fontSize = 12.sp)', 'Text("Настроить сайты", color = c.accent, fontSize = 12.sp)', 1)
p.write_text(s)
print('Applied a cleaner Chrome-inspired start page with a compact header, smaller hero and quieter shortcut tiles.')
