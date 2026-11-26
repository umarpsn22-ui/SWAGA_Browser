from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root/'app/src/main/java/app/swaga/browser/ui/BottomBar.kt'
s = p.read_text()

def once(old, new, label):
    global s
    if old not in s:
        raise SystemExit('BottomBar patch cannot find '+label)
    s = s.replace(old, new, 1)

once('import androidx.compose.material.icons.filled.Lock',
     'import androidx.compose.material.icons.filled.Lock\nimport androidx.compose.material.icons.filled.Add',
     'Add icon import')
once('''    onAi: () -> Unit,
) {''','''    onAi: () -> Unit,
    onNewTab: () -> Unit,
) {''','BottomBar callback')
# Remove the crowded action cluster from the main row. These actions remain available in the overflow menu.
start = s.index('        GhostModeButton(active = vm.ghostModeEnabled, onClick = vm::toggleGhostMode)')
end_marker = '''        if (!vm.ghostModeEnabled) {
            IconButton(onClick = onTabs, modifier = Modifier.size(40.dp)) {
                TabsCountIcon(vm.tabs.size)
            }
        }
'''
end = s.index(end_marker, start) + len(end_marker)
replacement = '''        IconButton(
            onClick = onNewTab,
            modifier = Modifier.size(40.dp),
        ) {
            Icon(Icons.Filled.Add, contentDescription = "Новая вкладка", tint = c.text)
        }
        IconButton(onClick = onTabs, modifier = Modifier.size(40.dp)) {
            TabsCountIcon(vm.tabs.size)
        }
'''
s = s[:start] + replacement + s[end:]
# Add the removed actions to the menu so the bottom row stays compact and responsive.
once('''                DropdownMenuItem(
                    text = { Text("Swaga VPN · управление") },
                    onClick = { menu = false; onVpn() },
                )''',
'''                DropdownMenuItem(
                    text = { Text("Новая вкладка") },
                    onClick = { menu = false; onNewTab() },
                )
                DropdownMenuItem(
                    text = { Text(if (vm.ghostModeEnabled) "Выключить режим призрака" else "Включить режим призрака") },
                    onClick = { menu = false; vm.toggleGhostMode() },
                )
                DropdownMenuItem(
                    text = { Text("Защита и статистика") },
                    onClick = { menu = false; showProtection = true },
                )
                DropdownMenuItem(
                    text = { Text("Swaga VPN · управление") },
                    onClick = { menu = false; onVpn() },
                )''',
'overflow menu actions')
p.write_text(s)

p = root/'app/src/main/java/app/swaga/browser/ui/BrowserApp.kt'
s = p.read_text()
once = '''                    onAi = { showAi = true },
                )'''
if once not in s:
    raise SystemExit('BrowserApp patch cannot find BottomBar invocation')
s = s.replace(once, '''                    onAi = { showAi = true },
                    onNewTab = { vm.newTab() },
                )''', 1)
p.write_text(s)
print('BottomBar now always shows New Tab and Tabs controls; VPN, ghost mode and protection moved into overflow menu.')
