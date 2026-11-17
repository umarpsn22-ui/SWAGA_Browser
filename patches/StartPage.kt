package app.swaga.browser.ui

import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.graphics.drawable.AnimatedImageDrawable
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.Drawable
import android.os.Build
import android.widget.ImageView
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
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import app.swaga.browser.BrowserViewModel
import app.swaga.browser.R

private data class QuickLink(
    val title: String,
    val url: String,
    val mark: String,
    val tile: Color,
    val ink: Color,
)

private val quickLinks = listOf(
    QuickLink("Search", "https://www.google.com", "G", Color(0xFFF8FAFC), Color(0xFF4285F4)),
    QuickLink("Booking", "https://www.booking.com", "B.", Color(0xFF003B95), Color.White),
    QuickLink("Skyscanner", "https://www.skyscanner.net", "✦", Color(0xFF0876D1), Color.White),
    QuickLink("Weather", "https://www.accuweather.com", "☼", Color(0xFFF5F8FA), Color(0xFFF08A27)),
    QuickLink("iHerb", "https://www.iherb.com", "iHerb", Color(0xFF69A900), Color.White),
    QuickLink("YouTube", "https://www.youtube.com", "▶", Color(0xFFF7F9FA), Color(0xFFE62117)),
    QuickLink("Maps", "https://maps.google.com", "●", Color(0xFFF7F9FA), Color(0xFF3185D8)),
    QuickLink("GitHub", "https://github.com", "GH", Color(0xFF24292F), Color.White),
)

private val deepTeal = Color(0xFF041514)

@Composable
fun StartPage(
    vm: BrowserViewModel,
    onEngines: () -> Unit,
    onSettings: () -> Unit,
) {
    val focusManager = LocalFocusManager.current
    var query by remember { mutableStateOf("") }

    Box(
        Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    listOf(Color(0xFF020C0B), Color(0xFF092322), Color(0xFF061918), deepTeal),
                ),
            ),
    ) {
        Box(
            Modifier
                .align(Alignment.TopEnd)
                .padding(top = 40.dp, end = 4.dp)
                .size(230.dp)
                .blur(52.dp)
                .background(
                    Brush.radialGradient(listOf(Color(0xFF247C70).copy(alpha = 0.34f), Color.Transparent)),
                    CircleShape,
                ),
        )
        Box(
            Modifier
                .align(Alignment.BottomStart)
                .padding(start = 2.dp, bottom = 30.dp)
                .size(210.dp)
                .blur(48.dp)
                .background(
                    Brush.radialGradient(listOf(Color(0xFF135A55).copy(alpha = 0.32f), Color.Transparent)),
                    CircleShape,
                ),
        )

        Box(
            Modifier
                .fillMaxSize()
                .padding(horizontal = 8.dp, vertical = 7.dp)
                .clip(RoundedCornerShape(31.dp))
                .background(
                    Brush.linearGradient(
                        listOf(
                            Color(0xD10C2B2A),
                            Color(0xB90B2928),
                            Color(0xC6071D1D),
                        ),
                    ),
                )
                .border(
                    1.dp,
                    Brush.linearGradient(
                        listOf(Color.White.copy(alpha = 0.29f), Color.White.copy(alpha = 0.08f), Color(0xFF78BDB0).copy(alpha = 0.19f)),
                    ),
                    RoundedCornerShape(31.dp),
                ),
        ) {
            Column(
                Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 18.dp, vertical = 15.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                        Text(
                            "#SWAGA_Browser",
                            color = Color(0xFFF5FBFA),
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = (-0.35).sp,
                        )
                        Text(
                            "Высокий шанс на свагу,#SWAGA_Browser",
                            color = Color(0xFFA9C3BE),
                            fontSize = 9.5.sp,
                            fontWeight = FontWeight.Medium,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    Box(
                        Modifier
                            .size(42.dp)
                            .clip(CircleShape)
                            .background(Color(0xB9091B1A))
                            .border(1.dp, Color.White.copy(alpha = 0.13f), CircleShape)
                            .clickable(onClick = onSettings),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(
                            Icons.Filled.Settings,
                            contentDescription = "Настройки",
                            tint = Color(0xFFE8F2F0),
                            modifier = Modifier.size(20.dp),
                        )
                    }
                }

                Spacer(Modifier.height(65.dp))

                Row(
                    Modifier.fillMaxWidth().height(78.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        "#SWAGAA",
                        color = Color(0xFFF7FAF9),
                        fontSize = 46.sp,
                        fontWeight = FontWeight.Black,
                        letterSpacing = (-3.0).sp,
                        maxLines = 1,
                        softWrap = false,
                    )
                    Spacer(Modifier.width(5.dp))
                    AnimatedSwagaSticker(Modifier.size(68.dp))
                }

                Spacer(Modifier.height(13.dp))

                Row(
                    Modifier
                        .fillMaxWidth()
                        .height(60.dp)
                        .clip(RoundedCornerShape(30.dp))
                        .background(Color(0xD4061111))
                        .border(1.dp, Color.White.copy(alpha = 0.13f), RoundedCornerShape(30.dp))
                        .padding(start = 10.dp, end = 7.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(
                        Modifier
                            .size(38.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF193D3B))
                            .clickable(onClick = onEngines),
                        contentAlignment = Alignment.Center,
                    ) {
                        EngineBadge(vm.engine, 29.dp)
                    }
                    Spacer(Modifier.width(12.dp))
                    BasicTextField(
                        value = query,
                        onValueChange = { query = it },
                        singleLine = true,
                        textStyle = TextStyle(
                            color = Color(0xFFEAF2F0),
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Medium,
                        ),
                        cursorBrush = SolidColor(Color(0xFF8BCFC2)),
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search, keyboardType = KeyboardType.Uri),
                        keyboardActions = KeyboardActions(
                            onSearch = {
                                vm.submit(query)
                                query = ""
                                focusManager.clearFocus()
                            },
                        ),
                        modifier = Modifier.weight(1f),
                        decorationBox = { inner ->
                            Box(contentAlignment = Alignment.CenterStart) {
                                if (query.isEmpty()) {
                                    Text(
                                        "Поиск в ${vm.engine.name}",
                                        color = Color(0xFF9BAEAA),
                                        fontSize = 14.sp,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis,
                                    )
                                }
                                inner()
                            }
                        },
                    )
                    Box(
                        Modifier
                            .size(44.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF102D2C))
                            .clickable {
                                vm.submit(query)
                                query = ""
                                focusManager.clearFocus()
                            },
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(
                            Icons.Filled.Search,
                            contentDescription = "Искать",
                            tint = Color(0xFFB9D8D2),
                            modifier = Modifier.size(20.dp),
                        )
                    }
                }

                if (vm.ghostModeEnabled) {
                    Spacer(Modifier.height(15.dp))
                    Text(
                        "ПРИВАТНЫЙ СЕАНС АКТИВЕН",
                        modifier = Modifier
                            .clip(RoundedCornerShape(20.dp))
                            .background(Color(0xFF174B43).copy(alpha = 0.75f))
                            .border(1.dp, Color(0xFF8CD8C0).copy(alpha = 0.25f), RoundedCornerShape(20.dp))
                            .padding(horizontal = 13.dp, vertical = 7.dp),
                        color = Color(0xFFB9E9D9),
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.7.sp,
                    )
                }

                Spacer(Modifier.height(28.dp))

                quickLinks.chunked(4).forEach { links ->
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        links.forEach { link ->
                            ShortcutTile(link, Modifier.weight(1f)) { vm.submit(link.url) }
                        }
                        repeat(4 - links.size) { Spacer(Modifier.weight(1f)) }
                    }
                    Spacer(Modifier.height(16.dp))
                }

                Spacer(Modifier.height(10.dp))
            }
        }
    }
}

@Composable
private fun ShortcutTile(link: QuickLink, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Column(
        modifier
            .height(91.dp)
            .clip(RoundedCornerShape(15.dp))
            .clickable(onClick = onClick)
            .padding(top = 2.dp, bottom = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Box(
            Modifier
                .size(56.dp)
                .clip(RoundedCornerShape(15.dp))
                .background(link.tile)
                .border(1.dp, Color.White.copy(alpha = 0.11f), RoundedCornerShape(15.dp)),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                link.mark,
                color = link.ink,
                fontSize = if (link.mark.length > 2) 11.sp else if (link.mark.length == 2) 20.sp else 30.sp,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                softWrap = false,
            )
        }
        Spacer(Modifier.height(6.dp))
        Text(
            link.title,
            color = Color(0xFFC3D2CF),
            fontSize = 9.5.sp,
            fontWeight = FontWeight.Medium,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            textAlign = TextAlign.Center,
        )
    }
}

@Suppress("NewApi")
@Composable
private fun AnimatedSwagaSticker(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val sticker: Drawable = remember(context) {
        val animated = if (Build.VERSION.SDK_INT >= 28) {
            runCatching {
                ImageDecoder.decodeDrawable(ImageDecoder.createSource(context.resources, R.raw.swaga_sticker))
            }.getOrNull() as? AnimatedImageDrawable
        } else null

        animated?.apply {
            repeatCount = AnimatedImageDrawable.REPEAT_INFINITE
        } ?: BitmapDrawable(
            context.resources,
            BitmapFactory.decodeResource(context.resources, R.raw.swaga_sticker),
        )
    }

    DisposableEffect(sticker) {
        (sticker as? AnimatedImageDrawable)?.start()
        onDispose {
            (sticker as? AnimatedImageDrawable)?.stop()
        }
    }

    AndroidView(
        factory = { viewContext ->
            ImageView(viewContext).apply {
                scaleType = ImageView.ScaleType.FIT_CENTER
                background = null
                setImageDrawable(sticker)
                contentDescription = "Анимированный стикер Swaga"
            }
        },
        update = { imageView ->
            if (imageView.drawable !== sticker) imageView.setImageDrawable(sticker)
            (sticker as? AnimatedImageDrawable)?.let { if (!it.isRunning) it.start() }
        },
        modifier = modifier,
    )
}
