// Stil v2 renk derecelendirme + vinyet (yalnızca --stil=v2 ortamında, vignette.gdshader yerine).
// Sahnenin kendisini (ekran dokusu) okur: gölgeleri mora, orta tonları teal-yeşile çeker, hafif doygunluk düşüşü ve
// yumuşak S eğrisi; kenarlar mor-siyaha kararır (Shinobi: Art of Vengeance referansının sisli, buğulu havası).
// "hurt" parametresi vignette.gdshader ile aynı (Level.flash_red kenardan kırmızı nabız).
shader_type canvas_item;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform float strength : hint_range(0.0, 1.0) = 0.5;
uniform vec4 edge_color : source_color = vec4(0.07, 0.03, 0.08, 1.0);
uniform float hurt : hint_range(0.0, 1.0) = 0.0;
uniform vec4 hurt_color : source_color = vec4(0.55, 0.02, 0.04, 1.0);
uniform float amount : hint_range(0.0, 1.0) = 1.0;
uniform float saturation = 0.9;
uniform float contrast = 1.06;
uniform vec3 shadow_tint = vec3(0.92, 0.82, 1.0);
uniform vec3 mid_tint = vec3(0.95, 1.04, 1.0);
uniform vec3 lift = vec3(0.012, 0.02, 0.022);
// ısı dalgası (Tamu): ekran UV'si yatayda kıvrılır, alta doğru güçlenir; 0 = kapalı (Ötüken, Şahmeran)
uniform float heat = 0.0;
// v38: bantlaşma önleyici titreşim genliği (sRGB, 1 / 255 = bir 8 bit adım); 0 = kapalı
uniform float dither = 0.0039;

void fragment() {
	vec2 suv = SCREEN_UV;
	if (heat > 0.0) {
		float k = heat * smoothstep(0.15, 1.0, suv.y);
		suv.x += sin(suv.y * 90.0 + TIME * 3.1) * k + sin(suv.y * 37.0 - TIME * 1.7 + suv.x * 9.0) * k * 0.6;
	}
	vec3 lin = texture(screen_tex, suv).rgb;
	vec3 c = pow(max(lin, vec3(0.0)), vec3(1.0 / 2.2));
	vec3 g = c;
	float l = dot(g, vec3(0.299, 0.587, 0.114));
	g = mix(vec3(l), g, saturation);
	// ayrık tonlama: koyular mor, ortalar teal-yeşil
	float sh = 1.0 - smoothstep(0.0, 0.42, l);
	float md = smoothstep(0.15, 0.5, l) * (1.0 - smoothstep(0.6, 0.95, l));
	g *= mix(vec3(1.0), shadow_tint, sh * 0.6);
	g *= mix(vec3(1.0), mid_tint, md);
	g = (g - 0.5) * contrast + 0.5;
	g += lift * (1.0 - g);
	g = mix(c, g, amount);
	// vinyet (ekran oranına göre yuvarlak)
	vec2 d = (UV - vec2(0.5)) * vec2(1.0, 0.75);
	float r = length(d) * 1.25;
	float v = smoothstep(0.32, 0.8, r) * strength;
	g = mix(g, edge_color.rgb, v);
	float h = smoothstep(0.38, 0.8, r) * hurt;
	g = mix(g, hurt_color.rgb, clamp(h * 1.4, 0.0, 0.85));
	// v38 titreşim (dither): HDR 2D tampon ekrana 8 bit yazılırken koyu sis / pus / gök gradyanlarında bantlaşma
	// olmasın; iki kaydırılmış "interleaved gradient noise" toplamı = üçgen dağılım, ±1 / 255 (görünmez tane)
	vec2 fc = FRAGCOORD.xy;
	float n1 = fract(52.9829189 * fract(dot(fc, vec2(0.06711056, 0.00583715))));
	float n2 = fract(52.9829189 * fract(dot(fc + vec2(47.0, 17.0), vec2(0.06711056, 0.00583715))));
	g += (n1 + n2 - 1.0) * dither;
	COLOR = vec4(pow(max(g, vec3(0.0)), vec3(2.2)), 1.0);
}
