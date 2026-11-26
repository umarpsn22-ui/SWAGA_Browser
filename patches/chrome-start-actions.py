from pathlib import Path
import sys
root = Path(sys.argv[1])
p = root/'app/src/main/java/app/swaga/browser/ui/StartPage.kt'
s = p.read_text()
s = s.replace('''    onSettings: () -> Unit,
) {''','''    onSettings: () -> Unit,
    onAi: () -> Unit,
    onIncognito: () -> Unit,
) {''',1)
needle = '''            Spacer(Modifier.height(19.dp))

            if (!vm.ghostModeEnabled'''
insert = '''            Spacer(Modifier.height(12.dp))
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                StartAction("Режим ИИ", Modifier.weight(1f), onAi)
                StartAction("Инкогнито", Modifier.weight(1f), onIncognito)
            }

            Spacer(Modifier.height(19.dp))

            if (!vm.ghostModeEnabled'''
if needle not in s:
    raise SystemExit('StartPage patch cannot find search action insertion point')
s = s.replace(needle, insert, 1)
p.write_text(s)

p = root/'app/src/main/java/app/swaga/browser/ui/BrowserApp.kt'
s = p.read_text()
needle = '''                            onSettings = { showSettings = true },
                        )'''
replace = '''                            onSettings = { showSettings = true },
                            onAi = { showAi = true },
                            onIncognito = { vm.toggleGhostMode() },
                        )'''
if needle not in s:
    raise SystemExit('BrowserApp patch cannot find StartPage invocation')
s = s.replace(needle, replace, 1)
p.write_text(s)
print('Added Chrome-style AI Mode and Incognito pill actions below the start-page search field.')
