// Ekran uzayı şok dalgası: merkezden genişleyen ince bir halkada ekran görüntüsünü ışınsal olarak
// içe doğru kaydırır (ısı/basınç kırılması). Kayma 960x540 mantıksal piksel ızgarasına yuvarlanır,
// böylece bulanıklık yerine piksel sanatına uygun "kayık" bir halka görünür. Halka dışında görüntü
// olduğu gibi örneklenir (hiçbir piksel değişmez).
shader_type canvas_item;
render_mode unshaded;

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest, repeat_disable;
uniform vec2 center = vec2(0.5, 0.5);          // ekran UV'si
uniform vec2 view_size = vec2(960.0, 540.0);   // mantıksal görünüm boyutu (piksel)
uniform float radius = 0.0;                    // halka yarıçapı (mantıksal piksel)
uniform float thickness = 8.0;                 // halka kalınlığı (mantıksal piksel)
uniform float strength = 3.0;                  // en çok kayma (mantıksal piksel)
uniform float rim = 0.05;                      // halkanın iç kenarındaki hafif aydınlanma

void fragment() {
	vec2 p = SCREEN_UV * view_size;
	vec2 c = center * view_size;
	vec2 d = p - c;
	float dist = length(d);
	// üçgen profil: halkanın tam ortasında 1, kenarlarında 0
	float w = clamp(1.0 - abs(dist - radius) / max(thickness * 0.5, 0.5), 0.0, 1.0);
	float mag = floor(w * strength + 0.5);
	vec3 col;
	if (mag < 0.5) {
		col = texture(screen_tex, SCREEN_UV).rgb;
	} else {
		vec2 dir = d / max(dist, 0.001);
		vec2 off = -dir * mag;   // içe doğru kırılma (mercek etkisi)
		col = texture(screen_tex, SCREEN_UV + off / view_size).rgb;
		// halkanın ön kenarı bir tık aydınlık: basınç cephesi
		col += vec3(rim) * step(radius, dist);
	}
	COLOR = vec4(col, 1.0);
}
