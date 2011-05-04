import tempita

var_nos = {}
var_code = {}

def var(num, name, code):
    var_nos[num] = name
    var_code[name] = tempita.Template(code)

# Variables note: all functions will have their weights as 'w',
# input variables 'tx' and 'ty', and output 'ox' and 'oy' available
# from the calling context. Each statement will be placed inside brackets,
# to avoid namespace pollution.
var(0, 'linear', """
    ox += tx * w;
    oy += ty * w;
    """)

var(1, 'sinusoidal', """
    ox += w * sinf(tx);
    oy += w * sinf(ty);
    """)

var(2, 'spherical', """
    float r2 = w / (tx*tx + ty*ty);
    ox += tx * r2;
    oy += ty * r2;
    """)

var(3, 'swirl', """
    float r2 = tx*tx + ty*ty;
    float c1 = sinf(r2);
    float c2 = cosf(r2);
    ox += w * (c1*tx - c2*ty);
    oy += w * (c2*tx + c1*ty);
    """)

var(4, 'horseshoe', """
    float r = w / sqrtf(tx*tx + ty*ty);
    ox += r * (tx - ty) * (tx + ty);
    oy += 2.0f * tx * ty * r;
    """)

var(5, 'polar', """
    ox += w * atan2f(tx, ty) * M_1_PI;
    oy += w * (sqrtf(tx * tx + ty * ty) - 1.0f);
    """)

var(6, 'handkerchief', """
    float a = atan2f(tx, ty);
    float r = sqrtf(tx*tx + ty*ty);
    ox += w * r * sinf(a+r);
    oy += w * r * cosf(a-r);
    """)

var(7, 'heart', """
    float sq = sqrtf(tx*tx + ty*ty);
    float a = sq * atan2f(tx, ty);
    float r = w * sq;
    ox += r * sinf(a)
    oy -= r * cosf(a)
    """)

var(8, 'disc', """
    float a = w * atan2f(tx, ty) * M_1_PI;
    float r = M_PI * sqrtf(tx*tx + ty*ty);
    ox += sinf(r) * a
    oy += cosf(r) * a
    """)

var(9, 'spiral', """
    float a = atan2f(tx, ty);
    float r = sqrtf(tx*tx + ty*ty);
    float r1 = w / r;
    ox += r1 * (cosf(a) + sinf(r));
    oy += r1 * (sinf(a) - cosf(r));
    """)

var(10, 'hyperbolic', """
    float a = atan2f(tx, ty);
    float r = sqrtf(tx*tx + ty*ty);
    ox += w * sinf(a) / r;
    oy += w * cosf(a) * r;
    """)

var(11, 'diamond', """
    float a = atan2f(tx, ty);
    float r = sqrtf(tx*tx + ty*ty);
    ox += w * sinf(a) * cosf(r);
    oy += w * cosf(a) * sinf(r);
    """)

var(12, 'ex', """
    float a = atan2f(tx, ty);
    float r = sqrtf(tx*tx + ty*ty);
    float n0 = sinf(a+r);
    float n1 = cosf(a-r);
    float m0 = n0*n0*n0*r;
    float m1 = n1*n1*n1*r;
    ox += w * (m0 + m1);
    oy += w * (m0 - m1);
    """)

var(13, 'julia', """
    float a = 0.5f * atan2f(tx, ty)
    if (mwc_next(rctx) & 1) a += M_PI;
    float r = w * sqrtf(tx*tx + ty*ty);
    ox += r * cosf(a);
    oy += r * sinf(a);
    """)

var(14, 'bent', """
    float nx = 1.0f;
    if (tx < 0.0f) nx = 2.0f;
    float ny = 1.0f;
    if (ty < 0.0f) ny = 0.5f;
    ox += w * nx * tx;
    oy += w * ny * ty;
    """)

var(15, 'waves', """
    float c10 = {{px.get(None, 'pre_xy')}};
    float c11 = {{px.get(None, 'pre_yy')}};
    float dx = {{px.get(None, 'pre_xo')}};
    float dy = {{px.get(None, 'pre_yo')}};
    float dx2 = 1.0f / (dx * dx);
    float dy2 = 1.0f / (dy * dy);

    ox += w * (tx + c10 + sinf(ty * dx2));
    oy += w * (ty + c11 + sinf(tx * dy2));
    """)

var(16, 'fisheye', """
    float r = sqrtf(tx*tx + ty*ty);
    r = 2.0f * w / (r + 1.0f);
    ox += r * ty;
    oy += r * tx;
    """)

var(17, 'popcorn', """
    float dx = tanf(3.0f*ty);
    float dy = tanf(3.0f*tx);
    ox += w * (tx + {{px.get(None, 'pre_xo')}} * sinf(dx));
    oy += w * (ty + {{px.get(None, 'pre_yo')}} * sinf(dy));
    """)

var(18, 'exponential', """
    float dx = w * expf(tx - 1.0f);
    float dy = M_PI * ty;
    ox += dx * cosf(dy);
    oy += dx * sinf(dy);
    """)

var(19, 'power', """
    float a = atan2f(tx, ty);
    float sa = sinf(a);
    float r = w * powf(sqrtf(tx*tx + ty*ty),sa);
    ox += r * cosf(a);
    oy += r * sa;
    """)

var(20, 'cosine', """
    float a = M_PI * tx;
    ox += w * cosf(a) * coshf(ty);
    oy -= w * sinf(a) * sinhf(ty);
    """)

var(21, 'rings', """
    float dx = {{px.get(None, 'pre_xo')}} * {{px.get(None, 'pre_xo')}};
    float r = sqrtf(tx*tx + ty*ty);
    float a = atan2f(tx, ty);
    r = w * (fmodf(r+dx, 2.0f*dx) - dx + r * (1.0f - dx));
    ox += r * cosf(a);
    oy += r * sinf(a);
    """)

var(22, 'fan', """
    float dx = M_PI * ({{px.get(None, 'pre_xo')}} * {{px.get(None, 'pre_xo')}});
    float dx2 = 0.5f * dx;
    float dy = {{px.get(None, 'pre_yo')}};
    float a = atan2f(tx, ty);
    a += (fmodf(a+dy, dx) > dx2) ? -dx2 : dx2;
    float r = w * sqrtf(tx*tx + ty*ty);
    ox += r * cosf(a);
    oy += r * sinf(a);
    """)

var(23, 'blob', """
    float r = sqrtf(tx*tx + ty*ty);
    float a = atan2f(tx, ty);
    float bdiff = 0.5f * ({{px.get('xf.blob_high - xf.blob_low','blob_diff'}})
    r *= w * ({{px.get('xf.blob_low')}} + bdiff * (1.0f + sinf({{px.get('xf.blob_waves')}} * a)))
    ox += sinf(a) * r;
    oy += cosf(a) * r;
    """)

var(24, 'pdj', """
    float nx1 = cosf({{px.get('xf.pdj_b')}} * tx);
    float nx2 = sinf({{px.get('xf.pdj_c')}} * tx);
    float ny1 = sinf({{px.get('xf.pdj_a')}} * ty);
    float ny2 = cosf({{px.get('xf.pdj_d')}} * ty);
    ox += w * (ny1 - nx1);
    oy += w * (nx2 - ny2);
    """)

var(25, 'fan2', """
    float dy = {{px.get('xf.fan2_y')}};
    float dx = M_PI * {{px.get('xf.fan2_x')}} * {{px.get('xf.fan2_x')}};
    float dx2 = 0.5f * dx;
    float a = atan2f(tx, ty);
    float r = w * sqrtf(tx*tx + ty*ty);
    if (t > dx2)
        a -= dx2;
    else
        a += dx2;

    ox += r * sinf(a);
    oy += r * cosf(a);
    """)

var(26, 'rings2', """
    float dx = {{px.get('xf.rings2_val')}} * {{px.get('xf.rings2_val')}};
    float r = sqrtf(tx*tx + ty*ty);
    float a = atan2f(tx, ty);
    r += -2.0f * dx * (int)((r+dx)/(2.0f*dx)) + r * (1.0f - dx);
    ox += w * sinf(a) * r;
    oy += w * cosf(a) * r;
    """)

var(27, 'eyefish', """
    float r = 2.0f * w / (sqrtf(tx*tx + ty*ty) + 1.0f);
    ox += r * tx;
    oy += r * ty;
    """)

var(28, 'bubble', """
    float r = w / (0.25f * (tx*tx + ty*ty) + 1.0f);
    ox += r * tx;
    oy += r * ty;
    """)

var(29, 'cylinder', """
    ox += w * sinf(tx);
    oy += w * ty;
    """)

var(30, 'perspective', """
    float pdist = {{px.get('xf.perspective_dist')}};
    float pvsin = {{px.get('np.sin(xf.perspective_angle*np.pi/2)', 'pvsin')}};
    float pvfcos = {{px.get(
        'xf.perspective_dist*np.cos(xf.perspective_angle*np.pi/2)', 'pvfcos')}};

    float t = 1.0 / (pdist - ty * pvsin);
    ox += w * pdist * tx * t;
    oy += w * pvfcos * ty * t;
    """)

var(31, 'noise', """
    float tmpr = mwc_next_01(rctx) * 2.0f * M_PI;
    float r = w * mwc_next_01(rctx);
    ox += tx * r * cosf(tmpr);
    oy += ty * r * sinf(tmpr);
    """)

var(32, 'julian', """
    float power = {{px.get('xf.julian_power')}};
    float t_rnd = truncf(mwc_next_01(rctx) * fabsf(power));
    float a = atan2f(ty, tx);
    float tmpr = (a + 2.0f * M_PI * t_rnd) / power;
    float cn = {{px.get('xf.julian_dist / xf.julian_power / 2', 'julian_cn')}};
    float r = w * powf(tx * tx + ty * ty, cn);

    ox += r * cosf(tmpr);
    oy += r * sinf(tmpr);
    """)

var(33, 'juliascope', """
    float ang = atan2f(ty, tx);
    float power = {{px.get('xf.juliascope_power', 'juscope_power')}};
    float t_rnd = truncf(mwc_next_01(rctx) * fabsf(power));
    // TODO: don't draw the extra random number
    if (mwc_next(rctx) & 1) ang = -ang;
    float tmpr = (2.0f * M_PI * t_rnd + ang) / power;

    float cn = {{px.get('xf.juliascope_dist / xf.juliascope_power / 2',
                         'juscope_cn')}};
    float r = w * powf(tx * tx + ty * ty, cn);

    ox += r * cosf(tmpr);
    oy += r * sinf(tmpr);
    """)

var(34, 'blur', """
    float tmpr = mwc_next_01(rctx) * 2.0f * M_PI;
    float r = w * mwc_next_01(rctx);
    ox += r * cosf(tmpr);
    oy += r * sinf(tmpr);
    """)

var(35, 'gaussian', """
    float ang = mwc_next_01(rctx) * 2.0f * M_PI;
    float r = weight * ( mwc_next_01(rctx) + mwc_next_01(rctx)
                   + mwc_next_01(rctx) + mwc_next_01(rctx) - 2.0f );
    ox += r * cosf(ang);
    oy += r * sinf(ang);
    """)

var(36, 'radial_blur', """
    float blur_angle = {{px.get('xf.radial_blur_angle')}} * M_PI * 0.5f;
    float spinvar = sinf(blur_angle);
    float zoomvar = cosf(blur_angle);
    float r = weight * ( mwc_next_01(rctx) + mwc_next_01(rctx)
                   + mwc_next_01(rctx) + mwc_next_01(rctx) - 2.0f );
    float ra = sqrtf(tx*tx + ty*ty);
    float tmpa = atan2f(ty, tx) + spinvar * r;
    float rz = zoomvar * r - 1.0f;
    ox += ra*cosf(tmpa) + rz*tx;
    oy += ra*sinf(tmpa) + rz*ty;
    """)

var(37, 'pie', """
    float slices = {{px.get('xf.pie_slices')}};
    float sl = truncf(mwc_next_01(rctx) * slices + 0.5f);
    float a = {{px.get('xf.pie_rotation')}} +
                2.0f * M_PI * (sl + mwc_next_01(rctx) + {{px.get('xf.pie_thickness')}} / slices;
    float r = w * mwc_next_01(rctx);
    ox += r * cosf(a);
    oy += r * sinf(a);
    """)

var(38, 'ngon', """
    float power = {{px.get('xf.ngon_power')}} * 0.5f
    float b = 2.0f * M_PI / {{px.get('xf.ngon_sides')}}
    float corners = {{px.get('xf.ngon_corners')}}
    float circle = {{px.get('xf.ngon_circle')}}

    float r_factor = powf(tx*tx + ty*ty, power);
    float theta = atan2f(ty, tx);
    float phi = theta - b * floorf(theta/b);
    if (phi > b/2.0f) phi -= b;
    float amp = (corners * (1.0f / cosf(phi) - 1.0f) + circle) / r_factor;

    ox += w * tx * amp;
    oy += w * ty * amp;
    """}

var(39, 'curl', """
    float c1 = {{px.get('xf.curl_c1')}};
    float c2 = {{px.get('xf.curl_c2')}};

    float re = 1.0f + c1*tx + c2*(tx*tx - ty*ty);
    float im = c1*ty + 2.0f*c2*tx*ty;
    float r = w / (re*re + im*im);

    ox += r * (tx*re + ty*im);
    oy += r * (ty*re + tx*im);
    """)

var(40, 'rectangles', """
    float rx = {{px.get('xf.rectangles_x')}};
    float ry = {{px.get('xf.rectangles_y')}};
    
    ox += w * ( (rx==0.0f) ? tx : rx * (2.0f * floorf(tx/rx) + 1.0f) - tx);
    oy += w * ( (ry==0.0f) ? ty : ry * (2.0f * floorf(ty/ry) + 1.0f) - ty);
    """)

var(41, 'arch', """
    float ang = mwc_next_01(rctx) * w * M_PI;

    ox += w * sinf(ang);
    oy += w * sinf(ang) * sinf(ang) / cosf(ang);
    """)

var(42, 'tangent', """
    ox += w * sinf(tx) / cosf(ty);
    oy += w * tanf(ty);
    """)

var(43, 'square', """
    ox += w * (mwc_next_01(rctx) - 0.5f);
    oy += w * (mwc_next_01(rctx) - 0.5f);
    """)

var(44, 'rays', """
    float ang = w * mwc_next_01(rctx) * M_PI;
    float r = w / (tx*tx + ty*ty);
    float tanr = w * tanf(ang) * r;
    ox += tanr * cosf(tx);
    oy += tanr * sinf(ty);
    """)

var(45, 'blade', """
    float r = mwc_next_01(rctx) * w * sqrtf(tx*tx + ty*ty);
    ox += w * tx * (cosf(r) + sinf(r));
    oy += w * tx * (cosf(r) - sinf(r));
    """)

var(46, 'secant2', """
    float r = w * sqrtf(tx*tx + ty*ty);
    float cr = cosf(r);
    float icr = 1.0f / cr;
    icr += (cr < 0 ? 1 : -1);

    ox += w * tx;
    oy += w * icr;
    """)

# var 47 is twintrian, has a call to badvalue in it

var(48, 'cross', """
    float s = tx*tx - ty*ty;
    float r = w * sqrtf(1.0f / (s*s));

    ox += r * tx;
    oy += r * ty;
    """)

var(49, 'disc2', """
    float twist = {{px.get('xf.disc2_twist')}};
    float rotpi = {{px.get('xf.disc2_rot * M_PI', 'disc2_rotpi')}};

    float sintwist = sinf(twist);
    float costwist = cosf(twist) - 1.0f;

    if (twist > 2.0f * M_PI) {
        float k = (1.0f + twist - 2.0f * M_PI);
        sintwist *= k;
        costwist *= k;
    }

    if (twist < -2.0f * M_PI) {
        float k = (1.0f + twist + 2.0f * M_PI);
        sintwist *= k;
        costwist *= k;
    }

    float t = rotpi * (tx + ty);
    float r = w * atan2f(tx, ty) / M_PI;

    ox += r * (sinf(t) + costwist);
    oy += r * (cosf(t) + sintwist);
    """)

var(50, 'super_shape', """
    float ang = atan2f(ty, tx);
    float theta = 0.25f * ({{px.get('xf.super_shape_m')}} * ang + M_PI);
    float t1 = fabsf(cosf(theta));
    float t2 = fabsf(sinf(theta));
    t1 = powf(t1,{{px.get('xf.super_shape_n2')}});
    t2 = powf(t2,{{px.get('xf.super_shape_n3')}});   
    float myrnd = {{px.get('xf.super_shape_rnd')}};
    float d = sqrtf(tx*tx+ty*ty);

    float r = w * ((myrnd*mwc_next_01(rctx) + (1.0f-myrnd)*d) - {{px.get('xf.super_shape_holes')}})
                * powf(t1+t2, {{px.get('-1.0 / xf.super_shape_holes', 'super_shape_pneg')}}) / d;

    ox += r * tx;
    oy += r * ty;
    """)

var(51, 'flower', """
    float holes = {{px.get('xf.flower_holes')}};
    float petals = {{px.get('xf.flower_petals')}};

    float r = w * (mwc_next_01(rctx) - holes) * cosf(petals*atan2f(ty, tx)) / sqrtf(tx*tx + ty*ty);

    ox += r * tx;
    oy += r * ty;
    """)

var(52, 'conic', """
    float d = sqrtf(tx*tx + ty*ty);
    float ct = tx / d;
    float holes = {{px.get('xf.conic_holes')}};
    float eccen = {{px.get('xf.conic_eccentricity')}};

    float r = w * (mwc_next_01(rctx) - holes) * eccen / (1.0f + eccen*ct) / d;

    ox += r * tx;
    oy += r * ty;
    """)

var(53, 'parabola', """
    float r = sqrtf(tx*tx + ty*ty);
    float sr = sinf(r);
    float cr = cosf(r);

    ox += {{px.get('xf.parabola_height')}} * w * sr * sr * mwc_next_01(rctx);
    oy += {{px.get('xf.parabola_width')}} * w * cr * mwc_next_01(rctx);
    """)

var(54, 'bent2', """
    float nx = 1.0f;
    if (tx < 0.0f) nx = {{px.get('xf.bent2_x')}};
    float ny = 1.0f;
    if (ty < 0.0f) ny = {{px.get('xf.bent2_y')}};
    ox += w * nx * tx;
    oy += w * ny * ty;
    """)

var(55, 'bipolar', """
    float x2y2 = tx*tx + ty*ty;
    float t = x2y2 + 1.0f;
    float x2 = tx * 2.0f;
    float ps = -M_PI_2 * {{px.get('xf.bipolar_shift')}}
    float y = 0.5 * atan2f(2.0f * ty, x2y2 - 1.0f) + ps;
   
    if (y > M_PI_2)
        y = -M_PI_2 + fmodf(y + M_PI_2, M_PI);
    else if (y < -M_PI_2)
        y = M_PI_2 - fmodf(M_PI_2 - y, M_PI);

    ox += w * 0.25f * M_2_PI * logf( (t+x2) / (t-x2) );
    oy += w * M_2_PI * y;
    """)

var(56, 'boarders', """
    float roundX = rintf(tx);
    float roundY = rintf(ty);
    float offsetX = tx - roundX;
    float offsetY = ty - roundY;

    if (mwc_next_01(rctx) > 0.75f) {
        ox += w * (offsetX*0.5f + roundX);
        oy += w * (offsetY*0.5f + roundY);
    } else {
        if (fabsf(offsetX) >= fabsf(offsetY)) {
            if (offsetX >= 0.0f) {
                ox += w * (offsetX*0.5f + roundX + 0.25f);
                oy += w * (offsetY*0.5f + roundY + 0.25f * offsetY / offsetX);
            } else {
                ox += w * (offsetX*0.5f + roundX - 0.25f);
                oy += w * (offsetY*0.5f + roundY - 0.25f * offsetY / offsetX);
            }
        } else {
            if (offsetY >= 0.0f) {
                oy += w * (offsetY*0.5f + roundY + 0.25f);
                ox += w * (offsetX*0.5f + roundX + offsetX / offsetY * 0.25f);
            } else {
                oy += w * (offsetY*0.5f + roundY - 0.25f);
                ox += w * (offsetX*0.5f + roundX - offsetX / offsetY * 0.25f);
            }
        }
    }
    """)

var(57, 'butterfly', """
    /* wx is weight*4/sqrt(3*pi) */
    float wx = w * 1.3029400317411197908970256609023f;
    float y2 = ty * 2.0f
    float r = wx * sqrtf(fabsf(ty * tx)/(tx*tx + y2*y2));
    ox += r * tx;
    oy += r * y2;
    """)

