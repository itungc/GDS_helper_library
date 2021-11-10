import numpy as np
from math import pi
from gdshelpers.geometry.chip import Cell
from gdshelpers.parts.waveguide import Waveguide
from gdshelpers.parts.coupler import GratingCoupler
from gdshelpers.parts.resonator import RingResonator
from gdshelpers.layout import GridLayout
from gdshelpers.parts.marker import CrossMarker
from gdshelpers.parts.marker import SquareMarker
from gdshelpers.helpers.positive_resist import convert_to_positive_resist
from gdshelpers.parts.port import Port
from shapely.geometry import Polygon
from gdshelpers.geometry import geometric_union
from gdshelpers.helpers.under_etching import create_holes_for_under_etching
from gdshelpers.geometry.ebl_frame_generators import raith_marker_frame
from gdshelpers.parts.text import Text
#The grating ff is the maximum duty cycle of the grating coupler
#ap_max_ff is the minimum duty cycle of the grating coupler

#Visible
#minimum_duty = 0.85
#maximum_duty = [0.90, 0.91, 0.92, 0.93, 0.94]
#n_grats = 20
#grating_pitch = [0.54, 0.57, 0.60, 0.63, 0.66]

#1550nm (best performance max_duty=0.80 grating_pitch=0.76)
#maximum_duty = np.linspace(0.75, 0.82, num = 5)
#grating_pitch = np.linspace(0.75, 0.77, num= 10)


visible_coup_param = {
    'width': 0.22,
    'full_opening_angle': np.deg2rad(30),
    'grating_period': 0.60,
    'grating_ff': 0.85,
    'ap_max_ff': 0.92,
    'n_gratings': 20,
    'taper_length': 16,
    'n_ap_gratings': 20,
}


chang_min_coupler_params = {
    'width': 0.22,
    'full_opening_angle': np.deg2rad(30), #40
    'grating_period': 0.57,
    'grating_ff':0.85, #minigap = 30nm
    'ap_max_ff':0.92,
    'n_gratings': 0,    #20
    'taper_length': 10, #16um
    'n_ap_gratings':20, #20
}

def make_frequency_shifter_waveguide(GC_param, input_angle):
    # Create the Optical waveguide and GCs

    # Optical GC on the left---------------------------------------------------------------------------
    # The waveguide number from left to right "wg3-wg1-wg2-wg4"

    incident_waveguide_expand_width = 1
    incident_waveguide_width = 0.3
    output_waveguide_fin_width = incident_waveguide_width

    incident_angle = input_angle * np.pi / 180
    Initial_angle = np.pi - incident_angle


    wg1 = Waveguide.make_at_port(Port((-30, 150), angle=Initial_angle, width=[3, 5, 3]))
    wg1.add_straight_segment(length=100, final_width=[3, incident_waveguide_expand_width, 3])
    wg1.add_straight_segment(length=50, final_width=[3, incident_waveguide_width, 3])
    wg1.add_bend(-pi, radius=50)
    wg1.add_straight_segment(length=49) #Straight wg before bending up
    wg1.add_bend(pi / 2 + incident_angle, radius=50)
    wg1_to_GC = Waveguide.make_at_port(wg1.current_port, width=incident_waveguide_width)
    wg1_to_GC.add_straight_segment(length=5)
    wg1.add_straight_segment(length=5)
    GC2 = GratingCoupler.make_traditional_coupler_at_port(wg1.current_port, **GC_param)

    wg1_shapely = wg1.get_shapely_object()
    GC2_shapely = convert_to_positive_resist(GC2.get_shapely_object(), 5)
    wg1_to_GC = wg1_to_GC.get_shapely_object()
    Input_2 = wg1_shapely.union(GC2_shapely)
    Input_2 = Input_2.difference(wg1_to_GC)

    # -----------------------------------------------------------------------------------------------
    # Optical GC on the right-----------------------------------------------------------------------
    # left_coupler = GratingCoupler.make_traditional_coupler(origin, angle=0, **coupler_params)
    wg2 = Waveguide.make_at_port(Port((-30 + 250, 150), angle=incident_angle, width=[3, 15, 3]))
    wg2.add_straight_segment(length=100, final_width=[3, incident_waveguide_expand_width, 3])
    wg2.add_straight_segment(length=50, final_width=[3, incident_waveguide_width, 3])
    wg2.add_bend(pi, radius=50)
    wg2.add_straight_segment(length=50) #Straight wg before bending up
    wg2.add_bend(-pi / 2 - incident_angle, radius=49)
    wg2_to_GC = Waveguide.make_at_port(wg2.current_port, width=incident_waveguide_width)
    wg2_to_GC.add_straight_segment(length=5)
    wg2.add_straight_segment(length=5)
    GC3 = GratingCoupler.make_traditional_coupler_at_port(wg2.current_port, **GC_param)
    #
    wg2_shapely = wg2.get_shapely_object()
    GC3_shapely = convert_to_positive_resist(GC3.get_shapely_object(), 5)
    wg2_to_GC = wg2_to_GC.get_shapely_object()
    Input_3 = wg2_shapely.union(GC3_shapely)
    Input_3 = Input_3.difference(wg2_to_GC)

    # Extended waveguide for the other side's waveguide
    wg1_extend = Waveguide.make_at_port(Port((-30, 150), angle=-incident_angle, width=[3, 1.5, 3]))
    wg1_extend.add_straight_segment(length=250, final_width=[3, 15, 3])
    wg2_extend = Waveguide.make_at_port(Port((-30 + 250, 150), angle=np.pi + incident_angle, width=[3, 3, 3]))
    wg2_extend.add_straight_segment(length=250, final_width=[3, 5, 3])

    # WG on the bottom left
    wg3 = Waveguide.make_at_port(wg2_extend.current_port)
    wg3.add_straight_segment(length=188, final_width=[3, output_waveguide_fin_width, 3])
    wg3.add_bend(-pi / 2 - incident_angle, radius=63.5)
    wg3.add_straight_segment(length=248, final_width=[3, output_waveguide_fin_width, 3]) # LAST Straight to GC
    wg3_to_GC = Waveguide.make_at_port(wg3.current_port, width=output_waveguide_fin_width)
    wg3_to_GC.add_straight_segment(length=5)
    wg3.add_straight_segment(length=5)
    GC1 = GratingCoupler.make_traditional_coupler_at_port(wg3.current_port, **GC_param)

    wg3_shapely = wg3.get_shapely_object()
    GC1_shapely = convert_to_positive_resist(GC1.get_shapely_object(), 5)
    wg3_to_GC = wg3_to_GC.get_shapely_object()
    Input_1 = wg3_shapely.union(GC1_shapely)
    Input_1 = Input_1.difference(wg3_to_GC)

    # Driect transmission without deflection
    wg4 = Waveguide.make_at_port(wg1_extend.current_port)
    wg4.add_straight_segment(length=188, final_width=[3, output_waveguide_fin_width, 3])
    wg4.add_bend(pi / 2 + incident_angle, radius=63.5)
    wg4.add_straight_segment(length=248, final_width=[3, output_waveguide_fin_width, 3])
    wg4_to_GC = Waveguide.make_at_port(wg4.current_port, width=output_waveguide_fin_width)
    wg4_to_GC.add_straight_segment(length=5)
    wg4.add_straight_segment(length=5)
    GC4 = GratingCoupler.make_traditional_coupler_at_port(wg4.current_port, **GC_param)

    wg4_shapely = wg4.get_shapely_object()
    GC4_shapely = convert_to_positive_resist(GC4.get_shapely_object(), 5)
    wg4_to_GC = wg4_to_GC.get_shapely_object()
    Input_4 = wg4_shapely.union(GC4_shapely)
    Input_4 = Input_4.difference(wg4_to_GC)

    return Input_1, Input_2, Input_3, Input_4, wg1_extend, wg2_extend

def make_IDT_Fingers(figer_widths, number_of_period, IDT_Aperature, ZnO_Top_left):
    # Creat the IDT
    # Change parameter here:

    # Finger characteristics
    figer_width = figer_widths
    pitch = figer_width * 2.8
    Figer_gap_offset = (figer_width + pitch) / 2 + figer_width / 2

    # How many pairs of IDT fingers
    number_of_period = int(number_of_period)
    how_many_period = number_of_period
    radius = how_many_period / 1.7

    # Finger coordinate (correction of different IDT aperature)
    Finger_origin_x = ZnO_Top_left + 5 + 7  # last two term = figers offset (5um) + small_pad_width_with extended(10um)
    Finger_origin_y = -5

    # Finger offset on the other side of the horn structure
    Finger_left_offset = 298
    Finger_length = IDT_Aperature

    # Pad coordinate
    arm2_right_pad_Offset = Finger_length + 4.5
    pad_length = how_many_period * 2

    Right_IDT_final_Angel = np.pi / 4 + np.pi / 25  # angel decrease, the right exposed finger is shorter
    Left_IDT_final_angel = - np.pi / 4.7  # angle decress, the left exposed finger is shorter #Demominator has to bigger than 4
    top_right = -1 * Right_IDT_final_Angel
    top_left = -1 * Left_IDT_final_angel

    # Below DO NOT CHANGE ------------------------------------------------------------------------------
    one_period_arm2 = [figer_width, figer_width + pitch]

    Idt_finger_arm2 = []

    for i in range(how_many_period):
        Idt_finger_arm2.extend(one_period_arm2)

    # IDT ON THE "right" GRATING COUPLER
    # Finger_lower is lower idt fingers, Finger_upper is upper IDT finger (on the horn on the right)
    Finger_lower = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x - 5 + Finger_length, Finger_origin_y), angle=np.pi, width=Idt_finger_arm2))
    Finger_lower.add_straight_segment(length=Finger_length)

    Finger_upper = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + Finger_length, Finger_origin_y + Figer_gap_offset), angle=np.pi,
             width=Idt_finger_arm2))
    Finger_upper.add_straight_segment(length=Finger_length)

    # SAME IDT ON THE "left" GRATING COUPLER ---------------------------------------------------------------------------------------------------
    # Finger_lower_other_side is left IDT finger, wg_2 is right IDT finger
    # Finger_lower_other_side = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset , Finger_origin_y-5), angle=np.pi/2, width=Idt_finger_arm2))
    # Finger_lower_other_side.add_straight_segment(length = Finger_length)

    # Finger_upper_other_side = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset + Figer_gap_offset, Finger_origin_y ), angle=np.pi / 2, width=Idt_finger_arm2))
    # Finger_upper_other_side.add_straight_segment(length=Finger_length)

    # Make Small metal pad
    # outer_corners_arm2_1 = [
    #    (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset, Finger_origin_y - 10),
    #    (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset, Finger_origin_y - 5),
    #    (Finger_origin_x - pad_length * 1 * (figer_width + pitch) - Finger_left_offset, Finger_origin_y - 5),
    #    (Finger_origin_x - pad_length * 1 * (figer_width + pitch) - Finger_left_offset, Finger_origin_y - 10)]

    # outer_corners_arm2_2 = [(Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset,
    #                         Finger_origin_y + arm2_right_pad_Offset),
    #                        (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset,
    #                         Finger_origin_y + arm2_right_pad_Offset - 5),
    #                        (Finger_origin_x - pad_length * 1 * (figer_width + pitch) - Finger_left_offset,
    #                         Finger_origin_y + arm2_right_pad_Offset - 5),
    #                        (Finger_origin_x - pad_length * 1 * (figer_width + pitch) - Finger_left_offset,
    #                         Finger_origin_y + arm2_right_pad_Offset)]
    #
    #--------------------------------------------------------------------------------------------------------------
    #Left small pad------------------------------------------------------------------------------------------------
    outer_corners_arm1_1 = [(Finger_origin_x - 9, Finger_origin_y - pad_length * (figer_width + pitch) / 2 ), #Bot-left corner
                            (Finger_origin_x - 4, Finger_origin_y - pad_length * (figer_width + pitch) / 2 ), #Bot-Right corner
                            (Finger_origin_x - 4, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period-26) - 16 ), #Top-Right corner
                            (Finger_origin_x - 9, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period-26) - 16 ) #Top-left corner
                            ]
    #Left Big pad
    Outer_corners_Big_pad1_1 = [(Finger_origin_x - 9, Finger_origin_y - pad_length * (figer_width + pitch) / 2 ),                           #Bot-left corner
                            (Finger_origin_x - 4, Finger_origin_y - pad_length * (figer_width + pitch) / 2 ),                               #Bot-Right corner
                            (Finger_origin_x - 4, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period-26) - 16 ), #Top-Right corner
                            (Finger_origin_x - 9, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period-26) - 16 ) #Top-left corner
                            ]
    # --------------------------------------------------------------------------------------------------------------
    # Right small pad-----------------------------------------------------------------------------------------------
    outer_corners_arm1_2 = [
        (Finger_origin_x + arm2_right_pad_Offset - 0, Finger_origin_y - pad_length * (figer_width + pitch) / 2 ), #Bot-right corner
        (Finger_origin_x + arm2_right_pad_Offset - 5, Finger_origin_y - pad_length * (figer_width + pitch) / 2 ), #Bot-left corner
        (Finger_origin_x + arm2_right_pad_Offset - 5, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period-26) - 16 ), #Top-left corner
        (Finger_origin_x + arm2_right_pad_Offset - 0, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period-26) - 16 )] #Top-right corner

    # small_pad_arm2_1 = Polygon(outer_corners_arm2_1)
    # small_pad_arm2_2 = Polygon(outer_corners_arm2_2)
    small_pad_arm1_1 = Polygon(outer_corners_arm1_1)
    small_pad_arm1_2 = Polygon(outer_corners_arm1_2)



    return Finger_lower,  Finger_upper ,small_pad_arm1_1 ,small_pad_arm1_2

def make_IDT_Fingers_v2(figer_widths, number_of_pairs, IDT_Aperature, ZnO_Top_left):
    # Creat the IDT
    # Change parameter here:

    # How many pairs of IDT fingers
    number_of_pairs = int(number_of_pairs)
    how_many_period = number_of_pairs

    # Finger coordinate (correction of different IDT aperature)
    Finger_origin_x = ZnO_Top_left + 5 + 7  # last two term = figers offset (5um) + small_pad_width_with extended(10um)
    Finger_origin_y = -5

    # Finger offset on the other side of the horn structure
    Finger_left_offset = 298
    Finger_length = IDT_Aperature

    # Pad coordinate
    arm2_right_pad_Offset = Finger_length + 4.5
    pad_length = how_many_period * 2

    Right_IDT_final_Angel = np.pi / 4 + np.pi / 25  # angel decrease, the right exposed finger is shorter
    Left_IDT_final_angel = - np.pi / 4.7  # angle decress, the left exposed finger is shorter #Demominator has to bigger than 4

    # Below DO NOT CHANGE ------------------------------------------------------------------------------
    #one_period_arm2 = [finger_width, finger_width + pitch]

    Idt_finger_arm2 = []

    start_width =0.17
    end_width = 0.19
    chirp_widths = np.linspace(start_width, end_width, num= number_of_pairs )
    chirp_widths = chirp_widths[::-1]

    average_chirp_finger_width = (start_width + end_width)/2
    average_chirp_finger_pitch = average_chirp_finger_width*2.8
    Chirped_finger_gap_offsets =  (average_chirp_finger_width + average_chirp_finger_pitch)/2 + average_chirp_finger_width/2

    #for i in range(how_many_period):
    for chirp_width in chirp_widths:
        chirp_pitch = chirp_width*2.8
        one_period_chirp_arm = [chirp_width, chirp_width + chirp_pitch]
        Idt_finger_arm2.extend(one_period_chirp_arm)

    # IDT ON THE "right" GRATING COUPLER
    # Finger_lower is lower idt fingers, Finger_upper is upper IDT finger (on the horn on the right)

    Finger_lower = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x - 5 + Finger_length, Finger_origin_y), angle=np.pi, width=Idt_finger_arm2))
    Finger_lower.add_straight_segment(length=Finger_length)

    Finger_upper = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + Finger_length, Finger_origin_y + Chirped_finger_gap_offsets), angle=np.pi,
             width=Idt_finger_arm2))
    Finger_upper.add_straight_segment(length=Finger_length)


    # Left small pad------------------------------------------------------------------------------------------------
    finger_width = average_chirp_finger_width
    pitch = average_chirp_finger_pitch

    outer_corners_arm1_1 = [(Finger_origin_x - 9, Finger_origin_y - pad_length * (finger_width + pitch) / 2),
                            # Bot-left corner
                            (Finger_origin_x - 4, Finger_origin_y - pad_length * (finger_width + pitch) / 2),
                            # Bot-Right corner
                            (Finger_origin_x - 4,
                             Finger_origin_y + pad_length * (finger_width + pitch) / 1 - (number_of_pairs - 26) - 16),
                            # Top-Right corner
                            (Finger_origin_x - 9,
                             Finger_origin_y + pad_length * (finger_width + pitch) / 1 - (number_of_pairs - 26) - 16)
                            # Top-left corner
                            ]
    bot_right_y = Finger_origin_y - pad_length * (finger_width + pitch) / 2 + 20
    # Left Big pad
    X_tr = Finger_origin_x - 4
    Y_tr = bot_right_y # TOP_RIGHT

    X_tl = Finger_origin_x - 4 - 100
    Y_tl = bot_right_y # TOP_LEFT

    X_br = Finger_origin_x - 4
    Y_br = bot_right_y - 150 # BOT_RIGHT

    X_bl = Finger_origin_x - 4 - 100
    Y_bl = bot_right_y - 150 # BOT_LEFT:

    Outer_corners_Big_pad1_1 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl, Y_bl),
                                (X_br, Y_br)
                                ]

    # Right small pad-----------------------------------------------------------------------------------------------
    outer_corners_arm1_2 = [
        (Finger_origin_x + arm2_right_pad_Offset - 0, Finger_origin_y - pad_length * (finger_width + pitch) / 2),
        # Bot-right corner
        (Finger_origin_x + arm2_right_pad_Offset - 5, Finger_origin_y - pad_length * (finger_width + pitch) / 2),
        # Bot-left corner
        (Finger_origin_x + arm2_right_pad_Offset - 5,
         Finger_origin_y + pad_length * (finger_width + pitch) / 1 - (number_of_pairs - 26) - 16),  # Top-left corner
        (Finger_origin_x + arm2_right_pad_Offset - 0,
         Finger_origin_y + pad_length * (finger_width + pitch) / 1 - (number_of_pairs - 26) - 16)]  # Top-right corner

    #Right big pad--------------------------------------------------------------------------------------------------
    bot_right_y = Finger_origin_y - pad_length * (finger_width + pitch) / 2 + 20
    # Left Big pad
    X_tl = Finger_origin_x + arm2_right_pad_Offset - 5
    Y_tl = bot_right_y  # TOP_RIGHT

    X_tr = Finger_origin_x + arm2_right_pad_Offset - 5 + 300
    Y_tr = bot_right_y  # TOP_LEFT

    X_br = Finger_origin_x + arm2_right_pad_Offset - 5 + 300
    Y_br = bot_right_y - 150  # BOT_RIGHT

    X_bl = Finger_origin_x + arm2_right_pad_Offset - 5
    Y_bl = bot_right_y - 150  # BOT_LEFT:

    Outer_corners_Big_pad1_2 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl, Y_bl),
                                (X_br, Y_br)
                                ]


    small_pad_arm1_1 = Polygon(outer_corners_arm1_1)
    Big_pad1_1 = Polygon(Outer_corners_Big_pad1_1)
    small_pad_arm1_2 = Polygon(outer_corners_arm1_2)
    Big_pad1_2 = Polygon(Outer_corners_Big_pad1_2)

    return Finger_lower, Finger_upper, small_pad_arm1_1, small_pad_arm1_2, Big_pad1_1, Big_pad1_2

def make_IDT_Fingers_pairs(figer_widths, number_of_pairs, IDT_Aperature, ZnO_Top_left, prop_length):
    # Creat the IDT
    # Change parameter here:

    # Finger characteristics
    figer_width = figer_widths
    pitch = figer_width * 2.8
    Figer_gap_offset = (figer_width + pitch) / 2 + figer_width / 2

    # How many pairs of IDT fingers
    number_of_pairs = int(number_of_pairs)
    how_many_period = number_of_pairs
    radius = how_many_period / 1.7

    # Finger coordinate (correction of different IDT aperature)
    Finger_origin_x = ZnO_Top_left + 5 + 7  # last two term = figers offset (5um) + small_pad_width_with extended(10um)
    Finger_origin_y = -5

    # Finger offset on the other side of the horn structure
    Finger_left_offset = prop_length
    Finger_length = IDT_Aperature

    # Pad coordinate
    arm2_right_pad_Offset = Finger_length + 4.5
    pad_length = how_many_period * 2

    Right_IDT_final_Angel = np.pi / 4 + np.pi / 25  # angel decrease, the right exposed finger is shorter
    Left_IDT_final_angel = - np.pi / 4.7  # angle decress, the left exposed finger is shorter #Demominator has to bigger than 4
    top_right = -1 * Right_IDT_final_Angel
    top_left = -1 * Left_IDT_final_angel

    # Below DO NOT CHANGE ------------------------------------------------------------------------------
    #one_period_arm2 = [figer_width, figer_width + pitch]
    Idt_finger_arm2 = []

    start_width = 0.17
    end_width = 0.19
    chirp_widths = np.linspace(start_width, end_width, num=number_of_pairs)
    chirp_widths = chirp_widths[::-1]

    average_chirp_finger_width = (start_width + end_width) / 2
    average_chirp_finger_pitch = average_chirp_finger_width * 2.8
    Chirped_finger_gap_offsets = (average_chirp_finger_width + average_chirp_finger_pitch) / 2 + average_chirp_finger_width / 2

    # for i in range(how_many_period):
    for chirp_width in chirp_widths:
        chirp_pitch = chirp_width * 2.8
        one_period_chirp_arm = [chirp_width, chirp_width + chirp_pitch]
        Idt_finger_arm2.extend(one_period_chirp_arm)

    # IDT ON THE "right" GRATING COUPLER
    # Finger_lower is lower idt fingers, Finger_upper is upper IDT finger (on the horn on the right)
    Finger_lower = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x , Finger_origin_y - 5), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_lower.add_straight_segment(length=Finger_length)

    Finger_upper = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + Chirped_finger_gap_offsets, Finger_origin_y ), angle=np.pi/2,
             width=Idt_finger_arm2))
    Finger_upper.add_straight_segment(length=Finger_length)

    # SAME IDT ON THE "left" GRATING COUPLER ---------------------------------------------------------------------------------------------------
    # Finger_lower_other_side is left IDT finger, wg_2 is right IDT finger
    Finger_lower_other_side = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset , Finger_origin_y-5), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_lower_other_side.add_straight_segment(length = Finger_length)

    Finger_upper_other_side = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset + Chirped_finger_gap_offsets, Finger_origin_y ), angle=np.pi / 2, width=Idt_finger_arm2))
    Finger_upper_other_side.add_straight_segment(length=Finger_length)

    # Make Small metal pad
    shift_2 = 10
    outer_corners_arm2_1 = [
        (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset - (number_of_pairs - 34) + shift_2 , Finger_origin_y - 10),
        (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset - (number_of_pairs - 34) + shift_2 , Finger_origin_y - 5),
        (Finger_origin_x - pad_length * (figer_width + pitch) / 2 - Finger_left_offset + shift_2, Finger_origin_y - 5),
        (Finger_origin_x - pad_length * (figer_width + pitch) / 2 - Finger_left_offset + shift_2, Finger_origin_y - 10)]

    outer_corners_arm2_2 = [(Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset - (number_of_pairs - 34) + shift_2 ,
                             Finger_origin_y + arm2_right_pad_Offset),
                            (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset - (number_of_pairs - 34) + shift_2,
                             Finger_origin_y + arm2_right_pad_Offset - 5),
                            (Finger_origin_x - pad_length * (figer_width + pitch) / 2 - Finger_left_offset+ shift_2,
                             Finger_origin_y + arm2_right_pad_Offset - 5),
                            (Finger_origin_x - pad_length * (figer_width + pitch) / 2 - Finger_left_offset+ shift_2,
                             Finger_origin_y + arm2_right_pad_Offset)]

    # --------------------------------------------------------------------------------------------------------------
    # Right_bot small pad------------------------------------------------------------------------------------------------
    shift = -10
    outer_corners_arm1_1 = [(Finger_origin_x - pad_length * (figer_width + pitch) / 2 - shift, Finger_origin_y - 9),
                            # Bot-left corner
                            (Finger_origin_x - pad_length * (figer_width + pitch) / 2 - shift, Finger_origin_y - 4),
                            # Bot-Right corner
                            (Finger_origin_x + pad_length * (figer_width + pitch) / 1.3 - (number_of_pairs - 26) - 16 - shift, Finger_origin_y - 4) ,
                            # Top-Right corner
                            (Finger_origin_x + pad_length * (figer_width + pitch) / 1.3 - (number_of_pairs - 26) - 16 - shift, Finger_origin_y - 9)
                            # Top-left corner
                            ]
    # Right_top small pad-----------------------------------------------------------------------------------------------
    outer_corners_arm1_2 = [
        (Finger_origin_x - pad_length * (figer_width + pitch) / 2 - shift, Finger_origin_y + arm2_right_pad_Offset - 0),
        # Bot-right corner
        (Finger_origin_x - pad_length * (figer_width + pitch) / 2 - shift, Finger_origin_y + arm2_right_pad_Offset - 5),
        # Bot-left corner
        (Finger_origin_x + pad_length * (figer_width + pitch) / 1.3 - (number_of_pairs - 26) - 16 - shift,
         Finger_origin_y + arm2_right_pad_Offset - 5),  # Top-left corner
        (Finger_origin_x + pad_length * (figer_width + pitch) / 1.3 - (number_of_pairs - 26) - 16 - shift,
         Finger_origin_y + arm2_right_pad_Offset - 0)]  # Top-right corner
    # Left Big pad
    Outer_corners_Big_pad1_1 = [(Finger_origin_x - 9, Finger_origin_y - pad_length * (figer_width + pitch) / 2),
                                # Bot-left corner
                                (Finger_origin_x - 4, Finger_origin_y - pad_length * (figer_width + pitch) / 2),
                                # Bot-Right corner
                                (Finger_origin_x - 4, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (
                                        number_of_pairs - 26) - 16),  # Top-Right corner
                                (Finger_origin_x - 9, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (
                                        number_of_pairs - 26) - 16)  # Top-left corner
                                ]
    # --------------------------------------------------------------------------------------------------------------


    small_pad_arm2_1 = Polygon(outer_corners_arm2_1)
    small_pad_arm2_2 = Polygon(outer_corners_arm2_2)
    small_pad_arm1_1 = Polygon(outer_corners_arm1_1)
    small_pad_arm1_2 = Polygon(outer_corners_arm1_2)

    return Finger_lower, Finger_upper, Finger_lower_other_side, Finger_upper_other_side, small_pad_arm1_1, small_pad_arm1_2 ,small_pad_arm2_1, small_pad_arm2_2

def make_Split_IDT_Fingers_pairs(figer_widths, number_of_pairs, IDT_Aperature, ZnO_Top_left, prop_length):
    # Creat the IDT
    # Change parameter here:

    # Finger characteristics
    figer_width = figer_widths
    pitch = figer_width * 7
    Figer_gap_offset = (figer_width + pitch) / 2

    # How many pairs of IDT fingers
    number_of_pairs = int(number_of_pairs)
    how_many_period = number_of_pairs
    radius = how_many_period / 1.7

    # Finger coordinate (correction of different IDT aperature)
    Finger_origin_x = ZnO_Top_left + 5 + 7  # last two term = figers offset (5um) + small_pad_width_with extended(10um)
    Finger_origin_y = -5

    # Finger offset on the other side of the horn structure
    Finger_left_offset = prop_length
    Finger_length = IDT_Aperature

    # Pad coordinate
    arm2_right_pad_Offset = Finger_length + 4.5
    pad_length = how_many_period * 2

    Right_IDT_final_Angel = np.pi / 4 + np.pi / 25  # angel decrease, the right exposed finger is shorter
    Left_IDT_final_angel = - np.pi / 4.7  # angle decress, the left exposed finger is shorter #Demominator has to bigger than 4
    top_right = -1 * Right_IDT_final_Angel
    top_left = -1 * Left_IDT_final_angel

    # Below DO NOT CHANGE ------------------------------------------------------------------------------
    #one_period_arm2 = [figer_width, figer_width + pitch]
    Idt_finger_arm2 = []

    one_period_arm2 = [figer_width, pitch]
    for i in range(how_many_period):
        Idt_finger_arm2.extend(one_period_arm2)

    # IDT ON THE "right" GRATING COUPLER
    # Finger_lower1 is lower idt fingers, Finger_upper1 is upper IDT finger (on the horn on the right)
    Finger_lower1 = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x , Finger_origin_y - 5), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_lower1.add_straight_segment(length=Finger_length)

    Finger_lower2 = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + 2*figer_width, Finger_origin_y - 5), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_lower2.add_straight_segment(length=Finger_length)

    Finger_upper1 = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + Figer_gap_offset, Finger_origin_y ), angle=np.pi/2,
             width=Idt_finger_arm2))
    Finger_upper1.add_straight_segment(length=Finger_length)

    Finger_upper2 = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + Figer_gap_offset + 2*figer_width, Finger_origin_y), angle=np.pi / 2,
             width=Idt_finger_arm2))
    Finger_upper2.add_straight_segment(length=Finger_length)

    # SAME IDT ON THE "left" GRATING COUPLER ---------------------------------------------------------------------------------------------------
    # Finger_lower_other_side is left IDT finger, wg_2 is right IDT finger
    Finger_lower_other_side1 = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset , Finger_origin_y-5), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_lower_other_side1.add_straight_segment(length = Finger_length)

    Finger_lower_other_side2 = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + 2*figer_width - Finger_left_offset, Finger_origin_y - 5), angle=np.pi / 2,
             width=Idt_finger_arm2))
    Finger_lower_other_side2.add_straight_segment(length=Finger_length)

    Finger_upper_other_side1 = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset + Figer_gap_offset, Finger_origin_y ), angle=np.pi / 2, width=Idt_finger_arm2))
    Finger_upper_other_side1.add_straight_segment(length=Finger_length)

    Finger_upper_other_side2 = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + 2*figer_width - Finger_left_offset + Figer_gap_offset, Finger_origin_y), angle=np.pi / 2,
             width=Idt_finger_arm2))
    Finger_upper_other_side2.add_straight_segment(length=Finger_length)

    # Make Small metal pad
    shift_2 = number_of_pairs*(pitch)/1.5
    right_small_pad_right_offset = shift_2 / 10
    left_small_pad_left_offset = right_small_pad_right_offset
    #Left_bot
    outer_corners_arm2_1 = [
        (Finger_origin_x + shift_2 - Finger_left_offset - left_small_pad_left_offset, Finger_origin_y - 10),
        (Finger_origin_x + shift_2 - Finger_left_offset - left_small_pad_left_offset, Finger_origin_y - 5),
        (Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset, Finger_origin_y - 5),
        (Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset, Finger_origin_y - 10)]
    # Left_top
    outer_corners_arm2_2 = [(Finger_origin_x + shift_2 - Finger_left_offset - left_small_pad_left_offset ,Finger_origin_y + arm2_right_pad_Offset),
                            (Finger_origin_x + shift_2 - Finger_left_offset - left_small_pad_left_offset ,Finger_origin_y + arm2_right_pad_Offset - 5),
                            (Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset ,Finger_origin_y + arm2_right_pad_Offset - 5),
                            (Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset ,Finger_origin_y + arm2_right_pad_Offset)]

    # --------------------------------------------------------------------------------------------------------------
    # Right_bot small pad------------------------------------------------------------------------------------------------

    outer_corners_arm1_1 = [(Finger_origin_x - shift_2 + right_small_pad_right_offset, Finger_origin_y - 9),
                            # Bot-left corner
                            (Finger_origin_x - shift_2 + right_small_pad_right_offset, Finger_origin_y - 4),
                            # Bot-left corner
                            (Finger_origin_x + shift_2 + right_small_pad_right_offset, Finger_origin_y - 4) ,
                            # Top-Right corner
                            (Finger_origin_x + shift_2 + right_small_pad_right_offset, Finger_origin_y - 9)
                            # Top-left corner
                            ]
    # Right_top small pad-----------------------------------------------------------------------------------------------
    outer_corners_arm1_2 = [
        (Finger_origin_x - shift_2 + right_small_pad_right_offset, Finger_origin_y + arm2_right_pad_Offset - 0),
        # Bot-right corner
        (Finger_origin_x - shift_2 + right_small_pad_right_offset, Finger_origin_y + arm2_right_pad_Offset - 5),
        # Bot-left corner
        (Finger_origin_x + shift_2 + right_small_pad_right_offset, Finger_origin_y + arm2_right_pad_Offset - 5),  # Top-left corner
        (Finger_origin_x + shift_2 + right_small_pad_right_offset, Finger_origin_y + arm2_right_pad_Offset - 0)]  # Top-right corner

    # Left Big pad bot
    bot_left_y = Finger_origin_y - 5
    bot_left_x = Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset

    X_tr = bot_left_x
    Y_tr = bot_left_y  # TOP_RIGHT

    X_tl = X_tr - 300
    Y_tl = Y_tr  # TOP_LEFT

    X_bl_ext1 = X_tl
    Y_bl_ext1 = Y_tl - 50  # BOT_left extend to middle upper point

    X_bl_ext2 = X_bl_ext1 + 120
    Y_bl_ext2 = Y_bl_ext1  # BOT_RIGHT extend to middle lower point

    X_bl = X_bl_ext2
    Y_bl = Y_bl_ext2 - 150  # BOT_LEFT:

    X_br = X_tr
    Y_br = Y_bl  # BOT_RIGHT

    buffer_cord_x = X_tl
    buffer_cord_y = Y_tl
    buffer_cord_x2 = X_bl_ext2
    buffer_cord_y2 = Y_bl_ext1


    Outer_corners_Big_pad1_1 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_bl, Y_bl),
                                (X_br, Y_br)
                                ]
    # Left Big pad top
    top_right_y = Finger_origin_y + arm2_right_pad_Offset
    top_right_x = Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset

    X_tr = top_right_x
    Y_tr = top_right_y  # TOP_RIGHT

    X_tl = buffer_cord_x - 50
    Y_tl = Y_tr  # TOP_LEFT

    X_bl_ext1 = X_tl
    Y_bl_ext1 = buffer_cord_y2 - 150  # BOT_left extend to middle upper point

    X_bl_ext2 = buffer_cord_x2 - 10
    Y_bl_ext2 = Y_bl_ext1  # BOT_RIGHT extend to middle lower point

    X_bl_ext3 = X_bl_ext2
    Y_bl_ext3 = buffer_cord_y2 - 10  # BOT_RIGHT extend to middle lower point

    X_bl_ext4 = buffer_cord_x - 10
    Y_bl_ext4 = Y_bl_ext3

    X_bl = X_bl_ext4
    Y_bl = buffer_cord_y + 10  # BOT_LEFT:

    X_br = X_tr
    Y_br = Y_bl  # BOT_RIGHT

    Outer_corners_Big_pad1_2 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_bl_ext3, Y_bl_ext3),
                                (X_bl_ext4, Y_bl_ext4),
                                (X_bl, Y_bl),
                                (X_br, Y_br)
                                ]
    #-----Right big pad bot
    bot_right_x = Finger_origin_x + shift_2 + right_small_pad_right_offset
    bot_right_y = Finger_origin_y - 4

    X_tr = bot_right_x
    Y_tr = bot_right_y  # TOP_RIGHT

    X_tl = X_tr + 300
    Y_tl = Y_tr  # TOP_LEFT

    X_bl_ext1 = X_tl
    Y_bl_ext1 = Y_tl - 50  # BOT_left extend to middle upper point

    X_bl_ext2 = X_bl_ext1 - 120
    Y_bl_ext2 = Y_bl_ext1  # BOT_RIGHT extend to middle lower point

    X_bl = X_bl_ext2
    Y_bl = Y_bl_ext2 - 150  # BOT_LEFT:

    X_br = X_tr
    Y_br = Y_bl  # BOT_RIGHT

    buffer_cord_x = X_tl
    buffer_cord_y = Y_tl
    buffer_cord_x2 = X_bl_ext2
    buffer_cord_y2 = Y_bl_ext1

    Outer_corners_Big_pad2_1 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_bl, Y_bl),
                                (X_br, Y_br)
                                ]
    #Right top big pad
    top_right_y = Finger_origin_y + arm2_right_pad_Offset - 0
    top_right_x = bot_right_x

    X_tr = top_right_x
    Y_tr = top_right_y  # TOP_RIGHT

    X_tl = buffer_cord_x + 50
    Y_tl = Y_tr  # TOP_LEFT

    X_bl_ext1 = X_tl
    Y_bl_ext1 = buffer_cord_y2 - 150  # BOT_left extend to middle upper point

    X_bl_ext2 = buffer_cord_x2 + 10
    Y_bl_ext2 = Y_bl_ext1  # BOT_RIGHT extend to middle lower point

    X_bl_ext3 = X_bl_ext2
    Y_bl_ext3 = buffer_cord_y2 - 10  # BOT_RIGHT extend to middle lower point

    X_bl_ext4 = buffer_cord_x + 10
    Y_bl_ext4 = Y_bl_ext3

    X_bl = X_bl_ext4
    Y_bl = buffer_cord_y + 10  # BOT_LEFT:

    X_br = X_tr
    Y_br = Y_bl  # BOT_RIGHT

    Outer_corners_Big_pad2_2 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_bl_ext3, Y_bl_ext3),
                                (X_bl_ext4, Y_bl_ext4),
                                (X_bl, Y_bl),
                                (X_br, Y_br)
                                ]

    # --------------------------------------------------------------------------------------------------------------


    small_pad_arm2_1 = Polygon(outer_corners_arm2_1)
    small_pad_arm2_2 = Polygon(outer_corners_arm2_2)
    small_pad_arm1_1 = Polygon(outer_corners_arm1_1)
    small_pad_arm1_2 = Polygon(outer_corners_arm1_2)

    Big_pad1_1 = Polygon(Outer_corners_Big_pad1_1)
    Big_pad1_2 = Polygon(Outer_corners_Big_pad1_2)
    Big_pad2_1 = Polygon(Outer_corners_Big_pad2_1)
    Big_pad2_2 = Polygon(Outer_corners_Big_pad2_2)

    return Finger_lower1, Finger_lower2, Finger_upper1, Finger_upper2, \
           Finger_lower_other_side1, Finger_lower_other_side2, Finger_upper_other_side1, Finger_upper_other_side2, \
           small_pad_arm1_1, small_pad_arm1_2 ,small_pad_arm2_1, small_pad_arm2_2, \
           Big_pad1_1, Big_pad1_2, Big_pad2_1, Big_pad2_2

def make_Chirp_IDT_Fingers_pairs(figer_widths, number_of_pairs, IDT_Aperature, prop_length):
    # Creat the IDT
    # Change parameter here:

    # How many pairs of IDT fingers
    number_of_pairs = int(number_of_pairs)
    how_many_period = number_of_pairs

    # Finger coordinate (correction of different IDT aperature)
    Finger_origin_x = 0  # last two term = figers offset (5um) + small_pad_width_with extended(10um)
    Finger_origin_y = 0

    # Finger offset on the other side of the horn structure
    Finger_length = IDT_Aperature
    Finger_left_offset = prop_length
    # Pad coordinate
    arm2_right_pad_Offset = Finger_length + 4.5
    pad_length = how_many_period * 2

    # Below DO NOT CHANGE ------------------------------------------------------------------------------
    # one_period_arm2 = [finger_width, finger_width + pitch]

    Idt_finger_arm1 = []
    Idt_finger_arm2 = []
    number_of_widths = 5

    start_width = 0.17
    end_width = 0.17
    litho_corrected_width = 0.005 #0.2 for 1um
    chirp_widths = np.linspace(start_width,end_width,number_of_widths)
    chirp_widths = chirp_widths[::-1]


    for index, width in enumerate(chirp_widths):
        pitch = 3 * width


        one_period_arm1 = [width - litho_corrected_width, pitch + litho_corrected_width]
        one_period_arm2 = one_period_arm1

        # Make sure the number of pairs can be equally devided into number of widths
        if (number_of_pairs / number_of_widths).is_integer() == True:
            devided_pairs = int(number_of_pairs / number_of_widths)
            for i in range(devided_pairs):

                # Change the period of the last pair in this pair group to the next pair's period
                if i == devided_pairs - 1 and index != len(chirp_widths) - 1:
                    pitch1 = chirp_widths[index + 1] * 3  # pitch for the last ending finger
                    pitch2 = width * 2 + chirp_widths[index + 1] * 1  # pitch for the second last finger

                    one_period_arm1 = [width - litho_corrected_width, pitch1 + litho_corrected_width]
                    one_period_arm2 = [width - litho_corrected_width, pitch2 + litho_corrected_width]

                    Idt_finger_arm1.extend(one_period_arm1)
                    Idt_finger_arm2.extend(one_period_arm2)

                else:
                    Idt_finger_arm1.extend(one_period_arm1)
                    Idt_finger_arm2.extend(one_period_arm2)
        else:
            print("%0.1f pairs can not be evenly devided into %0.1f different widths" % (
            number_of_pairs, number_of_widths))
            break
    # Below DO NOT CHANGE ------------------------------------------------------------------------------

    # IDT ON THE "right" GRATING COUPLER
    # Finger_lower1 is lower idt fingers, Finger_upper1 is upper IDT finger (on the horn on the right)
    # If you want to make chirp fingers, add 0.02 to the finger_upper1 line e.g.  Finger_origin_x + 2*(chirp_widths[-1]) +0.02
    # Funger_upper_other_side1 = Finger_origin_x - Finger_left_offset - 2*(chirp_widths[-1]) - 0.02

    Finger_lower1 = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x , Finger_origin_y - 5 + IDT_Aperature), angle=-np.pi/2, width=Idt_finger_arm1))
    Finger_lower1.add_straight_segment(length=Finger_length)


    Finger_upper1 = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + 2*(chirp_widths[-1]) , Finger_origin_y + IDT_Aperature), angle=-np.pi/2,
             width=Idt_finger_arm2))
    Finger_upper1.add_straight_segment(length=Finger_length)


    # SAME IDT ON THE "left" side ---------------------------------------------------------------------------------------------------
    # Finger_lower_other_side is left IDT finger, wg_2 is right IDT finger
    Finger_lower_other_side1 = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset , Finger_origin_y-5), angle=np.pi/2, width=Idt_finger_arm1))
    Finger_lower_other_side1.add_straight_segment(length = Finger_length)


    Finger_upper_other_side1 = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset - 2*(chirp_widths[-1]), Finger_origin_y ), angle=np.pi / 2, width=Idt_finger_arm2))
    Finger_upper_other_side1.add_straight_segment(length=Finger_length) #+ - 0.4 for 1um finger


    # Make Small metal pad
    average_chirp_finger_width = (start_width + end_width) / 2
    average_chirp_finger_pitch = average_chirp_finger_width * 4
    Chirped_finger_gap_offsets = (average_chirp_finger_width + average_chirp_finger_pitch) / 2 + average_chirp_finger_width / 2

    shift_2 = number_of_pairs*(average_chirp_finger_pitch)/1.5
    right_small_pad_right_offset = shift_2 / 10
    left_small_pad_left_offset = right_small_pad_right_offset
    #Left_bot
    outer_corners_arm2_1 = [
        (Finger_origin_x + shift_2 - Finger_left_offset - left_small_pad_left_offset, Finger_origin_y - 10),
        (Finger_origin_x + shift_2 - Finger_left_offset - left_small_pad_left_offset, Finger_origin_y - 5),
        (Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset, Finger_origin_y - 5),
        (Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset, Finger_origin_y - 10)]
    # Left_top
    outer_corners_arm2_2 = [(Finger_origin_x + shift_2 - Finger_left_offset - left_small_pad_left_offset ,Finger_origin_y + arm2_right_pad_Offset),
                            (Finger_origin_x + shift_2 - Finger_left_offset - left_small_pad_left_offset ,Finger_origin_y + arm2_right_pad_Offset - 5),
                            (Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset ,Finger_origin_y + arm2_right_pad_Offset - 5),
                            (Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset ,Finger_origin_y + arm2_right_pad_Offset)]

    # --------------------------------------------------------------------------------------------------------------
    # Right_bot small pad------------------------------------------------------------------------------------------------

    outer_corners_arm1_1 = [(Finger_origin_x - shift_2 + right_small_pad_right_offset, Finger_origin_y - 9),
                            # Bot-left corner
                            (Finger_origin_x - shift_2 + right_small_pad_right_offset, Finger_origin_y - 4),
                            # Bot-left corner
                            (Finger_origin_x + shift_2 + right_small_pad_right_offset, Finger_origin_y - 4) ,
                            # Top-Right corner
                            (Finger_origin_x + shift_2 + right_small_pad_right_offset, Finger_origin_y - 9)
                            # Top-left corner
                            ]
    # Right_top small pad-----------------------------------------------------------------------------------------------
    outer_corners_arm1_2 = [
        (Finger_origin_x - shift_2 + right_small_pad_right_offset, Finger_origin_y + arm2_right_pad_Offset - 0),
        # Bot-right corner
        (Finger_origin_x - shift_2 + right_small_pad_right_offset, Finger_origin_y + arm2_right_pad_Offset - 5),
        # Bot-left corner
        (Finger_origin_x + shift_2 + right_small_pad_right_offset, Finger_origin_y + arm2_right_pad_Offset - 5),  # Top-left corner
        (Finger_origin_x + shift_2 + right_small_pad_right_offset, Finger_origin_y + arm2_right_pad_Offset - 0)]  # Top-right corner

    y_mid_IDT = Finger_origin_y + arm2_right_pad_Offset/2
    right_top_small_pad_TL_X = Finger_origin_x - shift_2 + right_small_pad_right_offset
    right_top_small_pad_TL_Y = Finger_origin_y + arm2_right_pad_Offset - 0

    #Make big metal pads
    # Left Big pad bot
    bot_left_y = Finger_origin_y - 5
    bot_left_x = Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset + 2


    X_tr = bot_left_x + 50
    Y_tr = bot_left_y  # TOP_RIGHT

    X_tl = X_tr - 300
    Y_tl = Y_tr  # TOP_LEFT

    X_bl_ext1 = X_tl
    Y_bl_ext1 = Y_tl - 60  # BOT_left extend to middle upper point

    X_bl_ext2 = X_bl_ext1 + 290
    Y_bl_ext2 = Y_bl_ext1  # BOT_RIGHT extend to middle lower point

    X_bl = X_bl_ext2
    Y_bl = Y_bl_ext2 - 150  # BOT_LEFT:

    X_br = X_tr + 70
    Y_br = Y_bl  # BOT_RIGHT

    X_br_ext1 = X_br
    Y_br_ext1 = Y_br + 100

    buffer_cord_x = X_tl
    buffer_cord_y = Y_tl
    buffer_cord_x2 = X_bl_ext2
    buffer_cord_y2 = Y_bl_ext1
    buffer_cord_x3 = X_br

    Outer_corners_Big_pad1_1 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_bl, Y_bl),
                                (X_br, Y_br),
                                (X_br_ext1, Y_br_ext1)
                                ]
    # Left Big pad top
    top_right_y = Finger_origin_y + arm2_right_pad_Offset
    top_right_x = Finger_origin_x - shift_2 - Finger_left_offset - left_small_pad_left_offset + 2

    X_tr = top_right_x
    Y_tr = top_right_y  # TOP_RIGHT

    X_tl = buffer_cord_x - 50
    Y_tl = Y_tr  # TOP_LEFT

    X_bl_ext1 = X_tl
    Y_bl_ext1 = buffer_cord_y2 - 150  # BOT_left extend to middle upper point

    X_bl_ext2 = buffer_cord_x2 - 10
    Y_bl_ext2 = Y_bl_ext1  # BOT_RIGHT extend to middle lower point

    X_bl_ext3 = X_bl_ext2
    Y_bl_ext3 = buffer_cord_y2 - 10  # BOT_RIGHT extend to middle lower point

    X_bl_ext4 = buffer_cord_x - 10
    Y_bl_ext4 = Y_bl_ext3

    X_bl = X_bl_ext4
    Y_bl = buffer_cord_y + 10  # BOT_LEFT:

    X_br = X_tr
    Y_br = Y_bl  # BOT_RIGHT

    Outer_corners_Big_pad1_2 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_bl_ext3, Y_bl_ext3),
                                (X_bl_ext4, Y_bl_ext4),
                                (X_bl, Y_bl),
                                (X_br, Y_br)
                                ]
    #-----Right big pad bot
    bot_right_x = Finger_origin_x + shift_2 + right_small_pad_right_offset - 2
    bot_right_y = Finger_origin_y - 4

    X_tr = bot_right_x - 50
    Y_tr = bot_right_y  # TOP_RIGHT

    X_tl = X_tr + 300
    Y_tl = Y_tr  # TOP_LEFT

    X_bl_ext1 = X_tl
    Y_bl_ext1 = Y_tl - 60  # BOT_left extend to middle upper point

    X_bl_ext2 = X_bl_ext1 - 290
    Y_bl_ext2 = Y_bl_ext1  # BOT_RIGHT extend to middle lower point

    X_bl = X_bl_ext2
    Y_bl = Y_bl_ext2 - 151  # BOT_LEFT:

    X_br = buffer_cord_x3 + 10
    Y_br = Y_bl  # BOT_RIGHT

    X_br_ext1 = X_br
    Y_br_ext1 = Y_br + 100

    buffer_cord_x = X_tl
    buffer_cord_y = Y_tl
    buffer_cord_x2 = X_bl_ext2
    buffer_cord_y2 = Y_bl_ext1

    Outer_corners_Big_pad2_1 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_bl, Y_bl),
                                (X_br, Y_br),
                                (X_br_ext1, Y_br_ext1)
                                ]
    #Right top big pad
    top_right_y = Finger_origin_y + arm2_right_pad_Offset - 0
    top_right_x = bot_right_x

    X_tr = top_right_x
    Y_tr = top_right_y  # TOP_RIGHT

    X_tl = buffer_cord_x + 50
    Y_tl = Y_tr  # TOP_LEFT

    X_bl_ext1 = X_tl
    Y_bl_ext1 = buffer_cord_y2 - 151  # BOT_left extend to middle upper point

    X_bl_ext2 = buffer_cord_x2 + 10
    Y_bl_ext2 = Y_bl_ext1  # BOT_RIGHT extend to middle lower point

    X_bl_ext3 = X_bl_ext2
    Y_bl_ext3 = buffer_cord_y2 - 10  # BOT_RIGHT extend to middle lower point

    X_bl_ext4 = buffer_cord_x + 10
    Y_bl_ext4 = Y_bl_ext3

    X_bl = X_bl_ext4
    Y_bl = buffer_cord_y + 10  # BOT_LEFT:

    X_br = X_tr
    Y_br = Y_bl  # BOT_RIGHT

    Outer_corners_Big_pad2_2 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_bl_ext3, Y_bl_ext3),
                                (X_bl_ext4, Y_bl_ext4),
                                (X_bl, Y_bl),
                                (X_br, Y_br)
                                ]

    # --------------------------------------------------------------------------------------------------------------


    small_pad_arm2_1 = Polygon(outer_corners_arm2_1)
    small_pad_arm2_2 = Polygon(outer_corners_arm2_2)
    small_pad_arm1_1 = Polygon(outer_corners_arm1_1)
    small_pad_arm1_2 = Polygon(outer_corners_arm1_2)

    Big_pad1_1 = Polygon(Outer_corners_Big_pad1_1)
    Big_pad1_2 = Polygon(Outer_corners_Big_pad1_2)
    Big_pad2_1 = Polygon(Outer_corners_Big_pad2_1)
    Big_pad2_2 = Polygon(Outer_corners_Big_pad2_2)

    return Finger_lower1, Finger_upper1, \
           Finger_lower_other_side1, Finger_upper_other_side1, \
           small_pad_arm1_1, small_pad_arm1_2 ,small_pad_arm2_1, small_pad_arm2_2, \
           Big_pad1_1, Big_pad1_2, Big_pad2_1, Big_pad2_2, \
           top_right_x, y_mid_IDT, shift_2, \
           right_top_small_pad_TL_X, right_top_small_pad_TL_Y

def make_Acoustic_waveguides(init_width, fin_width, prop_length, top_right_x, y_mid_IDT, L_IDT_area ):
    phononicWG_initial_width = init_width
    phononicWG_fin_width = fin_width
    Wg_x_offset = 1.5
    L_initial_width = L_IDT_area * 1.8
    # Create the Acoustic waveguide
    # left_coupler = GratingCoupler.make_traditional_coupler(origin, angle=0, **coupler_params)
    Aco_wg = Waveguide.make_at_port(Port((top_right_x - Wg_x_offset, y_mid_IDT - 5 ), angle=-np.pi, width=phononicWG_initial_width))
    Aco_wg.add_straight_segment(length=L_initial_width)
    Aco_wg.add_straight_segment(length=20, final_width=phononicWG_fin_width) # Ini to trans _90um
    # wg1.add_bend(-pi/2, radius=50)
    Aco_wg.add_straight_segment(length=prop_length - 0.93*L_initial_width - 40  )    #Constant width for prop_length distance
    Aco_wg.add_straight_segment(length=20, final_width=phononicWG_initial_width) #trans to ini _ 90um
    Aco_wg.add_straight_segment(length=L_initial_width)
    # ring_res = RingResonator.make_at_port(Aco_wg.current_port, gap=resonator_gap, radius=resonator_radius)

    # right_coupler = GratingCoupler.make_traditional_coupler_at_port(wg2.current_port, **coupler_params)
    return Aco_wg

def make_ZnO_pad(Finger_length, right_top_small_pad_TL_X, right_top_small_pad_TL_Y):
    # Create ZnO

    # ZnO Expand
    ZnO_expand_x = 2
    ZnO_expand_y = 1
    ZnO_pad_width = 65
    Left_ZnO_OFFSET_X = 203

    # Make_ZnO_Pad
    Outer_corner_ZnO_pad_R = [(right_top_small_pad_TL_X - ZnO_expand_x,  right_top_small_pad_TL_Y + ZnO_expand_y ), #Bot Right
                              (right_top_small_pad_TL_X + Finger_length + ZnO_expand_x,  right_top_small_pad_TL_Y + ZnO_expand_y), #Top Right
                              (right_top_small_pad_TL_X + Finger_length + ZnO_expand_x,  right_top_small_pad_TL_Y -ZnO_pad_width - ZnO_expand_y), #Top Left
                              (right_top_small_pad_TL_X - ZnO_expand_x,  right_top_small_pad_TL_Y -ZnO_pad_width - ZnO_expand_y)] #Bot Left

    Outer_corner_ZnO_pad_L = [(right_top_small_pad_TL_X - ZnO_expand_x - Left_ZnO_OFFSET_X, right_top_small_pad_TL_Y + ZnO_expand_y),
                              # Bot Right
                              (right_top_small_pad_TL_X + Finger_length + ZnO_expand_x - Left_ZnO_OFFSET_X, right_top_small_pad_TL_Y + ZnO_expand_y),  # Top Right
                              (right_top_small_pad_TL_X + Finger_length + ZnO_expand_x - Left_ZnO_OFFSET_X, right_top_small_pad_TL_Y - ZnO_pad_width - ZnO_expand_y),  # Top Left
                              (right_top_small_pad_TL_X - ZnO_expand_x - Left_ZnO_OFFSET_X, right_top_small_pad_TL_Y - ZnO_pad_width - ZnO_expand_y)]  # Bot Left

    ZnO_pad_R = Polygon(Outer_corner_ZnO_pad_R)
    ZnO_pad_L = Polygon(Outer_corner_ZnO_pad_L)


    return ZnO_pad_R, ZnO_pad_L

def make_EBL_markers(layout_cell):
    # change marker dimension
    cross_l = 20
    croww_w = 5
    paddle_l = 5
    paddle_w = 5
    square_marker_size = 10
    top_marker_y = 3400
    right_most_marker_x = 6000
    X_Position_list = [0, right_most_marker_x / 4, right_most_marker_x / 2, right_most_marker_x * 3 / 4,
                       right_most_marker_x]
    Y_Position_list = [0, top_marker_y / 2, top_marker_y]
    Layer_list = [1, 2]
    # Make Global Marker
    for x_position in X_Position_list:
        for y_position in Y_Position_list:
            for layer in Layer_list:
                if layer == 1:
                    layout_cell.add_ebl_marker(layer=layer,
                                               marker=CrossMarker(origin=(x_position, y_position), cross_length=cross_l,
                                                                  cross_width=croww_w,
                                                                  paddle_length=paddle_l, paddle_width=paddle_w))
                else:
                    layout_cell.add_ebl_marker(layer=layer,
                                               marker=SquareMarker(
                                                   (x_position + square_marker_size, y_position + square_marker_size),
                                                   square_marker_size))
                    layout_cell.add_ebl_marker(layer=layer,
                                               marker=SquareMarker(
                                                   (x_position + square_marker_size, y_position - square_marker_size),
                                                   square_marker_size))
                    layout_cell.add_ebl_marker(layer=layer,
                                               marker=SquareMarker(
                                                   (x_position - square_marker_size, y_position + square_marker_size),
                                                   square_marker_size))
                    layout_cell.add_ebl_marker(layer=layer,
                                               marker=SquareMarker(
                                                   (x_position - square_marker_size, y_position - square_marker_size),
                                                   square_marker_size))

def generate_device_cell( sweep1, sweep2, cell_name):




    #Make the IDT fingers
    Finger_lower1, Finger_upper1, \
    Finger_lower_other_side1, Finger_upper_other_side1,\
    small_pad_arm1_1, small_pad_arm1_2, \
    small_pad_arm2_1, small_pad_arm2_2,\
    Big_pad1_1, Big_pad1_2, Big_pad2_1, Big_pad2_2, \
    top_right_x, y_mid_IDT, shift_2, \
    right_top_small_pad_TL_X, right_top_small_pad_TL_Y  = make_Chirp_IDT_Fingers_pairs(figer_widths=1,
                                                                number_of_pairs=55,
                                                                IDT_Aperature=50,
                                                                prop_length = 200
                                                                 )
    # Make ZnO pads
    ZnO_pad_R, ZnO_pad_L = make_ZnO_pad(Finger_length=50,
                            right_top_small_pad_TL_X = right_top_small_pad_TL_X,
                            right_top_small_pad_TL_Y= right_top_small_pad_TL_Y)

    # Make Acoustic waveguide
    Aco_wg = make_Acoustic_waveguides(init_width = sweep1,
                                      fin_width = sweep2,
                                      prop_length= 200,
                                      top_right_x= top_right_x,
                                      y_mid_IDT= y_mid_IDT, L_IDT_area= shift_2 )

    Fingers = geometric_union([Finger_lower1, Finger_upper1,
                               Finger_lower_other_side1, Finger_upper_other_side1,
                               small_pad_arm1_1, small_pad_arm1_2,
                               small_pad_arm2_1, small_pad_arm2_2
                               ])

    Pads = geometric_union([Big_pad1_1, Big_pad1_2, Big_pad2_1, Big_pad2_2])

    pads = geometric_union([ZnO_pad_R, ZnO_pad_L, Big_pad1_1, Big_pad1_2, Big_pad2_1, Big_pad2_2])

    ZnO_under_pad_and_fingers = pads.buffer(1)

    # Add name to cell
    text = Text(origin=[-500, -300], height=50, text=str(cell_name), alignment='left-bottom')


    #Add Cell
    cell = Cell('SIMPLE_RES_DEVICE r={:.4f} g={:.4f}'.format(sweep1, sweep2))

    cell.add_to_layer(1, convert_to_positive_resist([Aco_wg],30), text)
    cell.add_to_layer(2, ZnO_under_pad_and_fingers)
    cell.add_to_layer(3, Fingers)
    cell.add_to_layer(4, Pads)
    #cell.add_to_layer(5, holes)
    #cell.add_to_layer(5, left_coupler)

    #cell.add_ebl_marker(layer=1, marker=CrossMarker(origin=(-500,-300 ), cross_length=10 , cross_width=5, paddle_length=5, paddle_width=5))




    return cell

if __name__ == "__main__":
    layout = GridLayout(title='Phononic Waveguides', frame_layer=0, text_layer=3, region_layer_type=None, horizontal_spacing=100, vertical_spacing=0)

    #Parameters wanted to scan-------------------------------------------
    #1550nm (best performance max_duty=0.80 grating_pitch=0.76)
    maximum_duty = np.linspace(0.75, 0.82, num = 2)
    grating_pitch = np.linspace(0.75, 0.77, num= 2)
    step =12
    #number_of_finger_pairs = np.linspace(30, 90, num= int( (90-30) / step ) +1)
    #IDT_Aperatures = np.linspace(50, 200, num=6)
    number_of_finger_pairs = [55]
    IDT_Aperatures = [50]
    #Acoustic waveguide parameters
    initial_acoustic_width = [10, 20, 30 ,40 ,50]
    final_acoustic_width = [1, 5, 10, 20, 50]


    Parameters_scan_1 = initial_acoustic_width
    Parameters_scan_2 = final_acoustic_width

    print('Scan1 =', initial_acoustic_width)
    print('Scan2 =', final_acoustic_width)

    #--------------------------------------------------------------------
    total = len(Parameters_scan_1) * len(Parameters_scan_2)
    count = 0
    #--------------------------------------------------------------------
    #Get input from user to see if they want show or save
    answer = input('Show or Save Layout?\n Input (save/show):')

    if answer == 'show':
        show = True
    if answer == 'save':
        show = False
    else:
        show = True

    #--------------------------------------------------------------------
    #Show or save running procedure
    if show == True:

        # Add column labels
        layout.add_column_label_row(('G_P= %0.2f' % 0.7 ), row_label='')
        layout.add_to_row(generate_device_cell(  sweep1=55, sweep2=50, cell_name = '1' ))
        layout_cell, mapping = layout.generate_layout()
        layout_cell.show()

    if show == False:
        #Start looping over the scanned parameters
        #Add column labels
        layout.add_column_label_row(('W_fin= %0.1f' % param_2 for param_2 in Parameters_scan_2), row_label='')

        for param_1 in Parameters_scan_1:
            layout.begin_new_row('W_ini=\n%0.1f' % param_1)
            for param_2 in Parameters_scan_2:
                count =  count + 1
                complete = count/total
                print("Number of cell generated / Total cell = %0.1f/%0.1f (%0.2f%% complete) " %(count ,total,complete*100) )
                layout.add_to_row(generate_device_cell( sweep1= param_1, sweep2=param_2, cell_name=count), alignment='center-center' , realign=True)

        layout_cell, mapping = layout.generate_layout()
        layout_cell.add_ebl_frame(layer=1, size=40, frame_generator=raith_marker_frame, n=2)

        # Show and then save the layout!
        make_EBL_markers(layout_cell)
        print('saving........')
        layout_cell.show()
        layout_cell.save('Phononic_v0.gds', parallel=True)
        print('saved!!!')