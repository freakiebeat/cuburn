"""
Fr0st's pyflam3 bindings omit the ctypes fields for the xform structure.
This lets a given fr0st release be compatible with a much larger range
of flam3 versions, but we need access to that data.

Importing this module monkey-patches the fr0st module to include those
fields, and also provides a few other functions not needed in fr0st.
If flam3 or smoulder eventually includes padded xform structuress for
wider compatibility, or I bother to write a parser for flam3.h,
this may become unnecessary.
"""

from ctypes import *
from fr0stlib.pyflam3 import constants
from fr0stlib.pyflam3._flam3 import *

flam3_nvariations = constants.flam3_nvariations = 99

BaseXForm._fields_ = [('var', c_double * flam3_nvariations)
               , ('c', (c_double * 2) * 3) # TODO: ctypes 2D arrays?
               , ('post', (c_double * 2) * 3)
               , ('density', c_double)
               , ('color', c_double)
               , ('color_speed', c_double)
               , ('animate', c_double)
               , ('opacity', c_double)
               , ('vis_adjusted', c_double)
               , ('padding', c_int)
               , ('wind', c_double * 2)
               , ('precalc_angles_flag', c_int)
               , ('precalc_atan_xy_flag', c_int)
               , ('precalc_atan_yx_flag', c_int)
               , ('has_preblur', c_double)
               , ('has_post', c_int)
               , ('blob_low', c_double)
               , ('blob_high', c_double)
               , ('blob_waves', c_double)
               , ('pdj_a', c_double)
               , ('pdj_b', c_double)
               , ('pdj_c', c_double)
               , ('pdj_d', c_double)
               , ('fan2_x', c_double)
               , ('fan2_y', c_double)
               , ('rings2_val', c_double)
               , ('perspective_angle', c_double)
               , ('perspective_dist', c_double)
               , ('julian_power', c_double)
               , ('julian_dist', c_double)
               , ('juliascope_power', c_double)
               , ('juliascope_dist', c_double)
               , ('radial_blur_angle', c_double)
               , ('pie_slices', c_double)
               , ('pie_rotation', c_double)
               , ('pie_thickness', c_double)
               , ('ngon_sides', c_double)
               , ('ngon_power', c_double)
               , ('ngon_circle', c_double)
               , ('ngon_corners', c_double)
               , ('curl_c1', c_double)
               , ('curl_c2', c_double)
               , ('rectangles_x', c_double)
               , ('rectangles_y', c_double)
               , ('amw_amp', c_double)
               , ('disc2_rot', c_double)
               , ('disc2_twist', c_double)
               , ('super_shape_rnd', c_double)
               , ('super_shape_m', c_double)
               , ('super_shape_n1', c_double)
               , ('super_shape_n2', c_double)
               , ('super_shape_n3', c_double)
               , ('super_shape_holes', c_double)
               , ('flower_petals', c_double)
               , ('flower_holes', c_double)
               , ('conic_eccentricity', c_double)
               , ('conic_holes', c_double)
               , ('parabola_height', c_double)
               , ('parabola_width', c_double)
               , ('bent2_x', c_double)
               , ('bent2_y', c_double)
               , ('bipolar_shift', c_double)
               , ('cell_size', c_double)
               , ('cpow_r', c_double)
               , ('cpow_i', c_double)
               , ('cpow_power', c_double)
               , ('curve_xamp', c_double)
               , ('curve_yamp', c_double)
               , ('curve_xlength', c_double)
               , ('curve_ylength', c_double)
               , ('escher_beta', c_double)
               , ('lazysusan_spin', c_double)
               , ('lazysusan_space', c_double)
               , ('lazysusan_twist', c_double)
               , ('lazysusan_x', c_double)
               , ('lazysusan_y', c_double)
               , ('modulus_x', c_double)
               , ('modulus_y', c_double)
               , ('oscope_separation', c_double)
               , ('oscope_frequency', c_double)
               , ('oscope_amplitude', c_double)
               , ('oscope_damping', c_double)
               , ('popcorn2_x', c_double)
               , ('popcorn2_y', c_double)
               , ('popcorn2_c', c_double)
               , ('separation_x', c_double)
               , ('separation_xinside', c_double)
               , ('separation_y', c_double)
               , ('separation_yinside', c_double)
               , ('split_xsize', c_double)
               , ('split_ysize', c_double)
               , ('splits_x', c_double)
               , ('splits_y', c_double)
               , ('stripes_space', c_double)
               , ('stripes_warp', c_double)
               , ('wedge_angle', c_double)
               , ('wedge_hole', c_double)
               , ('wedge_count', c_double)
               , ('wedge_swirl', c_double)
               , ('wedge_julia_angle', c_double)
               , ('wedge_julia_count', c_double)
               , ('wedge_julia_power', c_double)
               , ('wedge_julia_dist', c_double)
               , ('wedge_sph_angle', c_double)
               , ('wedge_sph_count', c_double)
               , ('wedge_sph_hole', c_double)
               , ('wedge_sph_swirl', c_double)
               , ('whorl_inside', c_double)
               , ('whorl_outside', c_double)
               , ('waves2_freqx', c_double)
               , ('waves2_scalex', c_double)
               , ('waves2_freqyx', c_double)
               , ('waves2_scaley', c_double)
               , ('auger_sym', c_double)
               , ('auger_weight', c_double)
               , ('auger_freq', c_double)
               , ('auger_scale', c_double)
               , ('flux_spread', c_double)
               , ('mobius_re_a', c_double)
               , ('mobius_im_a', c_double)
               , ('mobius_re_b', c_double)
               , ('mobius_im_b', c_double)
               , ('mobius_re_c', c_double)
               , ('mobius_im_c', c_double)
               , ('persp_vsin', c_double)
               , ('persp_vfcos', c_double)
               , ('julian_rN', c_double)
               , ('julian_cN', c_double)
               , ('juliascope_rN', c_double)
               , ('juliascope_cN', c_double)
               , ('wedgeJulia_rN', c_double)
               , ('wedgeJulia_cn', c_double)
               , ('wedgeJulia_cf', c_double)
               , ('radialBlur_spinvar', c_double)
               , ('radialBlur_zoomvar', c_double)
               , ('waves_dx2', c_double)
               , ('waves_dy2', c_double)
               , ('disc2_sinadd', c_double)
               , ('disc2_cosadd', c_double)
               , ('disc2_timespi', c_double)
               , ('super_shape_pm_4', c_double)
               , ('super_shape_pneg1_n1', c_double)
               , ('num_active_vars', c_int)
               , ('active_var_weights', c_double * flam3_nvariations)
               , ('varFunc', c_int * flam3_nvariations)
               , ('motion_freq', c_int)
               , ('motion_func', c_int)
               , ('motion', POINTER(BaseXForm))
               , ('num_motion', c_int)
               # It seems I'm missing something in the current version.
               , ('mysterious_padding', c_double * 2) ]

