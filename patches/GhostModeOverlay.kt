package app.swaga.browser.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import app.swaga.browser.themes.LocalSwaga

/** Compact glass transition card. Pursuer video asset will replace the temporary indicator. */
@Composable
fun GhostModeOverlay(
    visible: Boolean,
    active: Boolean,
    modifier: Modifier = Modifier,
) {
    val c = LocalSwaga.current
    val shape = RoundedCornerShape(22.dp)
    val glassTop = if (c.isDark) Color.White.copy(alpha = 0.22f) else Color.White.copy(alpha = 0.72f)
    val glassBody = if (c.isDark) c.surface.copy(alpha = 0.34f) else c.surface.copy(alpha = 0.58f)

    AnimatedVisibility(
        visible = visible,
        modifier = modifier.fillMaxWidth(),
        enter = fadeIn(tween(260)) +
            slideInVertically(animationSpec = tween(440)) { -it / 3 } +
            scaleIn(initialScale = 0.94f, animationSpec = tween(440)),
        exit = fadeOut(tween(360)) + scaleOut(targetScale = 0.97f, animationSpec = tween(360)),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth(0.88f)
                .shadow(24.dp, shape, clip = false)
                .background(
                    Brush.linearGradient(
                        listOf(
                            glassTop,
                            glassBody,
                            c.accent.copy(alpha = if (c.isDark) 0.13f else 0.10f),
                        ),
                    ),
                    shape,
                )
                .border(
                    1.dp,
                    Brush.linearGradient(
                        listOf(
                            Color.White.copy(alpha = 0.76f),
                            c.accent.copy(alpha = 0.42f),
                            Color.White.copy(alpha = 0.20f),
                        ),
                    ),
                    shape,
                )
                .padding(horizontal = 17.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            androidx.compose.foundation.layout.Box(
                Modifier
                    .size(38.dp)
                    .background(Color.White.copy(alpha = if (c.isDark) 0.14f else 0.46f), CircleShape)
                    .border(1.dp, Color.White.copy(alpha = 0.48f), CircleShape),
                contentAlignment = Alignment.Center,
            ) {
                androidx.compose.foundation.Canvas(Modifier.size(9.dp)) {
                    drawCircle(if (active) Color(0xFF83E6B0) else c.accent)
                }
            }
            Column(Modifier.weight(1f)) {
                Text(
                    text = if (active) "РЕЖИМ ПРИЗРАКА" else "Ahhh, fresh meat",
                    color = c.text,
                    fontSize = if (active) 12.sp else 15.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = if (active) 1.05.sp else 0.1.sp,
                )
                Spacer(Modifier.size(3.dp))
                Text(
                    text = if (active) "Приватный сеанс активен · без списка вкладок" else "Обычный режим восстановлен",
                    color = c.dim,
                    fontSize = 10.sp,
                )
            }
        }
    }
}
