from pathlib import Path
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFilter

root = Path(sys.argv[1])
raw = root/'app/src/main/res/raw'
video = raw/'swaga_hero.mp4'
if not video.exists():
    raise SystemExit('Source Swaga hero video is missing.')

def convex_hull(points):
    pts = sorted(set(points))
    if len(pts) <= 1:
        return pts
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower = []
    for point in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]

def remove_dark_backdrop(frame):
    rgb = frame.convert('RGB')
    hsv = rgb.convert('HSV')
    width, height = rgb.size
    hsv_pixels = hsv.load()
    points = []
    def is_yellow(x, y):
        h, saturation, value = hsv_pixels[x, y]
        return 11 <= h <= 68 and saturation > 65 and value > 65
    for y in range(height):
        for x in range(width):
            if not is_yellow(x, y):
                continue
            if (x == 0 or x == width-1 or y == 0 or y == height-1
                or not is_yellow(max(0, x-1), y)
                or not is_yellow(min(width-1, x+1), y)
                or not is_yellow(x, max(0, y-1))
                or not is_yellow(x, min(height-1, y+1))):
                points.append((x, y))
    if len(points) < 20:
        raise RuntimeError('Could not isolate the mascot silhouette in a video frame.')
    hull = convex_hull(points)
    mask = Image.new('L', (width, height), 0)
    ImageDraw.Draw(mask).polygon(hull, fill=255)
    # Expand the silhouette to preserve its dark hand-drawn outline.
    mask = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(0.45))
    result = rgb.convert('RGBA')
    result.putalpha(mask)
    return result

with tempfile.TemporaryDirectory(prefix='swaga-hero-') as temp:
    frames_dir = Path(temp)
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(video),
        '-vf', 'fps=10', '-fps_mode', 'passthrough',
        str(frames_dir/'frame_%03d.png')
    ], check=True)
    paths = sorted(frames_dir.glob('frame_*.png'))
    if len(paths) < 2:
        raise SystemExit('Hero video did not produce enough animation frames.')
    frames = [remove_dark_backdrop(Image.open(path)) for path in paths]
    output = raw/'swaga_hero_alpha.webp'
    frames[0].save(
        output, format='WEBP', save_all=True, append_images=frames[1:],
        duration=100, loop=0, lossless=False, quality=88, method=6
    )
    # The processed animation replaces the opaque MP4 in the app.
    video.unlink()
    with Image.open(output) as check:
        if not check.is_animated or check.n_frames < 2:
            raise SystemExit('Transparent hero animation validation failed.')
        alpha = check.convert('RGBA').getchannel('A')
        if alpha.getpixel((0, 0)) != 0:
            raise SystemExit('Hero background was not made transparent.')
print('Created transparent animated WebP mascot from the original hero video.')

# Switch the Android view from the opaque MP4 to the alpha WebP animation.
start_page = root/'app/src/main/java/app/swaga/browser/ui/StartPage.kt'
code = start_page.read_text()
new_imports = [
    'import android.graphics.ImageDecoder',
    'import android.graphics.drawable.AnimatedImageDrawable',
    'import android.graphics.drawable.BitmapDrawable',
    'import android.graphics.drawable.Drawable',
    'import android.os.Build',
    'import android.widget.ImageView',
]
for item in new_imports:
    if item not in code:
        code = code.replace('import android.graphics.BitmapFactory', 'import android.graphics.BitmapFactory\n'+item, 1)
start_marker = '@Composable\nprivate fun SwagaHeroVideo()'
end_marker = '\n@Composable\nprivate fun StartAction'
start = code.index(start_marker)
end = code.index(end_marker, start)
replacement = '''@Suppress("NewApi")
@Composable
private fun SwagaHeroVideo() {
    val context = LocalContext.current
    val hero: Drawable = remember(context) {
        val animated = if (Build.VERSION.SDK_INT >= 28) runCatching {
            ImageDecoder.decodeDrawable(ImageDecoder.createSource(context.resources, R.raw.swaga_hero_alpha))
        }.getOrNull() as? AnimatedImageDrawable else null
        animated?.apply { repeatCount = AnimatedImageDrawable.REPEAT_INFINITE }
            ?: BitmapDrawable(
                context.resources,
                BitmapFactory.decodeResource(context.resources, R.raw.swaga_hero_alpha)
                    ?: throw IllegalStateException("Transparent hero image is missing")
            )
    }
    DisposableEffect(hero) {
        (hero as? AnimatedImageDrawable)?.start()
        onDispose { (hero as? AnimatedImageDrawable)?.stop() }
    }
    AndroidView(
        factory = { viewContext ->
            ImageView(viewContext).apply {
                scaleType = ImageView.ScaleType.FIT_CENTER
                background = null
                setImageDrawable(hero)
                contentDescription = "Анимированный логотип Swaga"
            }
        },
        update = { view ->
            if (view.drawable !== hero) view.setImageDrawable(hero)
            (hero as? AnimatedImageDrawable)?.let { if (!it.isRunning) it.start() }
        },
        modifier = Modifier.size(112.dp),
    )
}
'''
code = code[:start] + replacement + code[end:]
start_page.write_text(code)
