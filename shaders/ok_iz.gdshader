// Stil v2 ok uçuş izi (scripts/actors/Ok.gd): ucu dolgun, kuyruğa doğru incelen mürekkep fırça çizgisi. Koyu mürekkep
// dış kenar + açık (oka özgü renkte) çekirdek; kuyrukta kuru fırça kıllarına ayrılarak erir. Kenarlar türevle
// yumuşatılır (MSAA gerekmez).
// Köşe verisi:
//   UV.x   iz boyunca dünya uzunluğu / 40 (bristle.png boyuna sarar)
//   UV.y   enine 0..1 (0,5 orta çizgi)
//   COLOR.rgb  çekirdek rengi, COLOR.a  0 baş (ok) .. 1 kuyruk
shader_type canvas_item;
render_mode blend_premul_alpha, unshaded;

uniform sampler2D bristle : filter_linear_mipmap, repeat_enable;
uniform vec3 c_ink = vec3(0.012, 0.008, 0.014);
uniform float hot_gain = 1.6;     // HDR: başa yakın çekirdek parlar (ışıma eşiğini hafifçe aşar)

void fragment() {
	float u = clamp(COLOR.a, 0.0, 1.0);
	float y = abs(UV.y * 2.0 - 1.0);
	vec4 b = texture(bristle, vec2(UV.x, clamp(UV.y, 0.004, 0.996)));
	// kenar pürüzü: kuyruğa doğru artar
	float rag = ((b.a - 0.5) * 0.18 + (b.r - 0.5) * 0.35 * u);
	float edge = 1.0 - y + rag;
	float aa = fwidth(y) * 1.1 + 0.02;
	float a = smoothstep(0.0, aa, edge);
	// kuru fırça: kuyruk kıllara ayrılır, en uçta tamamen erir
	float strand = smoothstep(-0.08, 0.08, b.r + 0.35 - u * 1.05);
	a *= mix(1.0, strand, smoothstep(0.25, 0.9, u));
	a *= 1.0 - smoothstep(0.82, 1.0, u);
	// çekirdek: ortada açık renk, başta HDR parıltı
	float core = 1.0 - smoothstep(0.3, 0.55 + aa, y - rag * 0.4 + u * 0.35);
	vec3 cc = COLOR.rgb * mix(hot_gain, 1.0, smoothstep(0.0, 0.45, u));
	vec3 col = mix(c_ink, cc, core);
	COLOR = vec4(col * a, a);
}
