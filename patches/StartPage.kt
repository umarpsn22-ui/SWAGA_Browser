package app.swaga.browser.ui

import android.net.Uri
import android.widget.VideoView
import app.swaga.browser.BrowserViewModel
import app.swaga.browser.R
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

private data class QuickLink(
    val title: String,
    val url: String,
    val symbol: String,
    val tileColor: Color,
    val symbolColor: Color,
)

private val quickLinks = listOf(
    QuickLink("Search", "https://www.google.com", "G", Color.White, Color(0xFF4285F4)),
    QuickLink("Booking", "https://www.booking.com", "B.", Color(0xFF0755A5), Color.White),
    QuickLink("Skyscanner", "https://www.skyscanner.net", "✦", Color(0xFF0878D8), Color.White),
    QuickLink("Weather", "https://www.accuweather.com", "☼", Color.White, Color(0xFFE66A12)),
    QuickLink("iHerb", "https://www.iherb.com", "i", Color(0xFF5A9E16), Color.White),
    QuickLink("YouTube", "https://www.youtube.com", "▶", Color.White, Color(0xFFE62117)),
    QuickLink("Maps", "https://maps.google.com", "⌖", Color.White, Color(0xFF25885A)),
    QuickLink("Telegram", "https://web.telegram.org", "➤", Color(0xFF249BD7), Color.White),
)

private val GlassSurface = Color(0xB50A2423)

@Composable
fun StartPage(
    vm: BrowserViewModel,
    onEngines: () -> Unit,
    onSettings: () -> Unit,
) {
    val focusManager = LocalFocusManager.current
    var query by remember { mutableStateOf("") }
    val userBookmarks = if (!vm.ghostModeEnabled) vm.bookmarks.take(8) else emptyList()
    val links = (if (userBookmarks.size >= 4) {
        userBookmarks.map {
            QuickLink(
                title = it.title,
                url = it.url,
                symbol = it.title.trim().firstOrNull()?.uppercase() ?: "•",
                tileColor = Color(0xFF24413F),
                symbolColor = Color.White,
            )
        } + quickLinks.filterNot { default -> userBookmarks.any { it.url == default.url } }
    } else {
        quickLinks
    }).take(8)

    val submitSearch: () -> Unit = {
        val value = query.trim()
        if (value.isNotEmpty()) {
            vm.submit(value)
            query = ""
            focusManager.clearFocus()
        }
    }

    Box(
        Modifier
            .fillMaxSize()
            .background(
                Brush.linearGradient(
                    colors = listOf(
                        Color(0xFF001715),
                        Color(0xFF062B29),
                        Color(0xFF001D1C),
                        Color(0xFF001514),
                    ),
                ),
            ),
    ) {
        Box(
            Modifier
                .size(420.dp)
                .align(Alignment.Center)
                .background(
                    Brush.radialGradient(
                        colors = listOf(Color(0xFF1C625A).copy(alpha = 0.22f), Color.Transparent),
                    ),
                    CircleShape,
                ),
        )

        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 21.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(top = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(
                    Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(3.dp),
                ) {
                    Text(
                        "#SWAGA_Browser",
                        color = Color(0xFFF5FAF9),
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = (-0.45).sp,
                    )
                    Text(
                        "Высокий шанс на свагу,#SWAGA_Browser",
                        color = Color(0xFFA7C0BC),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Medium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }

                Box(
                    Modifier
                        .size(54.dp)
                        .background(
                            Brush.radialGradient(
                                listOf(Color(0xFF4DFF64).copy(alpha = 0.34f), Color.Transparent),
                            ),
                            CircleShape,
                        ),
                    contentAlignment = Alignment.Center,
                ) {
                    Box(
                        Modifier
                            .size(42.dp)
                            .clip(CircleShape)
                            .background(Color(0xC6091C1B))
                            .border(1.dp, Color.White.copy(alpha = 0.12f), CircleShape)
                            .clickable(onClick = onSettings),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(
                            Icons.Filled.Settings,
                            contentDescription = "Настройки",
                            tint = Color(0xFFEAF2F0),
                            modifier = Modifier.size(21.dp),
                        )
                    }
                }
            }

            Spacer(Modifier.height(92.dp))

            Row(
                Modifier
                    .fillMaxWidth()
                    .height(78.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    "#SWAGAA",
                    color = Color(0xFFF7FBFA),
                    fontSize = 43.sp,
                    fontWeight = FontWeight.Black,
                    letterSpacing = (-2.8).sp,
                    maxLines = 1,
                    softWrap = false,
                )
                Spacer(Modifier.width(7.dp))
                SwagaHeroVideo(Modifier.size(62.dp))
            }

            Spacer(Modifier.height(22.dp))

            Row(
                Modifier
                    .fillMaxWidth()
                    .height(62.dp)
                    .shadow(16.dp, RoundedCornerShape(30.dp), clip = false)
                    .clip(RoundedCornerShape(30.dp))
                    .background(
                        Brush.linearGradient(
                            listOf(
                                Color(0xE9001111),
                                GlassSurface,
                                Color(0xD9001111),
                            ),
                        ),
                    )
                    .border(1.dp, Color.White.copy(alpha = 0.13f), RoundedCornerShape(30.dp))
                    .padding(start = 11.dp, end = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(
                    Modifier
                        .size(38.dp)
                        .clip(CircleShape)
                        .background(Color(0xFF304D59))
                        .clickable(onClick = onEngines),
                    contentAlignment = Alignment.Center,
                ) {
                    Text("ϟ", color = Color.White, fontSize = 25.sp, fontWeight = FontWeight.Bold)
                }
                Spacer(Modifier.width(11.dp))
                Box(
                    Modifier
                        .width(1.dp)
                        .height(26.dp)
                        .background(Color.White.copy(alpha = 0.17f)),
                )
                Spacer(Modifier.width(12.dp))
                BasicTextField(
                    value = query,
                    onValueChange = { query = it },
                    singleLine = true,
                    textStyle = TextStyle(
                        color = Color(0xFFF2F7F6),
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                    ),
                    cursorBrush = SolidColor(Color(0xFF8BCFC2)),
                    keyboardOptions = KeyboardOptions(
                        imeAction = ImeAction.Search,
                        keyboardType = KeyboardType.Uri,
                    ),
                    keyboardActions = KeyboardActions(onSearch = { submitSearch() }),
                    modifier = Modifier.weight(1f),
                    decorationBox = { inner ->
                        Box(contentAlignment = Alignment.CenterStart) {
                            if (query.isEmpty()) {
                                Text(
                                    "Поиск в " + vm.engine.name,
                                    color = Color(0xFF9CB2AE),
                                    fontSize = 14.sp,
                                )
                            }
                            inner()
                        }
                    },
                )
                Box(
                    Modifier
                        .size(42.dp)
                        .clip(RoundedCornerShape(17.dp))
                        .background(Color(0xFF183B3B).copy(alpha = 0.82f))
                        .clickable(onClick = submitSearch),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Filled.Search,
                        contentDescription = "Искать",
                        tint = Color(0xFFDDEBE8),
                        modifier = Modifier.size(21.dp),
                    )
                }
            }

            Spacer(Modifier.height(35.dp))

            val rows = links.chunked(4)
            rows.forEachIndexed { index, row ->
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(7.dp),
                    verticalAlignment = Alignment.Top,
                ) {
                    row.forEach { link ->
                        StartTile(
                            link = link,
                            modifier = Modifier.weight(1f),
                            onClick = { vm.submit(link.url) },
                        )
                    }
                    repeat((4 - row.size).coerceAtLeast(0)) {
                        Spacer(Modifier.weight(1f))
                    }
                }
                if (index != rows.lastIndex) {
                    Spacer(Modifier.height(16.dp))
                }
            }

            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun SwagaHeroVideo(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    var playbackFailed by remember { mutableStateOf(false) }
    val videoView = remember(context) {
        VideoView(context).apply {
            setOnPreparedListener { player ->
                player.isLooping = true
                player.setVolume(0f, 0f)
                // Start only after MediaPlayer reports READY.
                start()
            }
            setOnErrorListener { _, _, _ ->
                playbackFailed = true
                true
            }
            setVideoURI(
                Uri.parse("android.resource://" + context.packageName + "/" + R.raw.swaga_hero),
            )
        }
    }

    DisposableEffect(videoView) {
        onDispose { videoView.stopPlayback() }
    }

    Box(
        modifier
            .shadow(12.dp, RoundedCornerShape(16.dp), clip = false)
            .clip(RoundedCornerShape(16.dp))
            .background(Color(0xFF071211))
            .border(1.dp, Color.White.copy(alpha = 0.12f), RoundedCornerShape(16.dp)),
    ) {
        if (playbackFailed) {
            Image(
                painter = painterResource(R.drawable.swaga_hero_fallback),
                contentDescription = "Стикер рядом с логотипом",
                modifier = Modifier.fillMaxSize(),
            )
        } else {
            AndroidView(
                factory = { videoView },
                modifier = Modifier.fillMaxSize(),
            )
        }
    }
}

@Composable
private fun StartTile(
    link: QuickLink,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Column(
        modifier
            .clip(RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(bottom = 2.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(
            Modifier
                .size(57.dp)
                .shadow(8.dp, RoundedCornerShape(15.dp), clip = false)
                .clip(RoundedCornerShape(15.dp))
                .background(link.tileColor)
                .border(1.dp, Color.White.copy(alpha = 0.10f), RoundedCornerShape(15.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                link.symbol,
                color = link.symbolColor,
                fontSize = if (link.symbol.length > 1) 22.sp else 29.sp,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
            )
        }
        Spacer(Modifier.height(7.dp))
        Text(
            link.title,
            color = Color(0xFFC1D0CD),
            fontSize = 10.sp,
            fontWeight = FontWeight.Medium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            textAlign = TextAlign.Center,
        )
    }
}
