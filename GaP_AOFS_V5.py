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


    wg1 = Waveguide.make_at_port(Port((10, 150), angle=Initial_angle, width=[3, 5, 3]))
    wg1.add_straight_segment(length=125, final_width=[3, incident_waveguide_expand_width, 3])
    wg1.add_straight_segment(length=100, final_width=[3, incident_waveguide_width, 3])
    wg1.add_bend(-pi, radius=50)
    wg1.add_straight_segment(length=64) #Straight wg before bending up
    wg1.add_bend(pi / 2 + incident_angle, radius=50)
    wg1_to_GC = Waveguide.make_at_port(wg1.current_port, width=incident_waveguide_width)
    wg1_to_GC.add_straight_segment(length=20)
    wg1.add_straight_segment(length=10)
    GC2 = GratingCoupler.make_traditional_coupler_at_port(wg1.current_port, **GC_param)

    wg1_shapely = wg1.get_shapely_object()
    GC2_shapely = convert_to_positive_resist(GC2.get_shapely_object(), 5)
    wg1_to_GC = wg1_to_GC.get_shapely_object()
    Input_2 = wg1_shapely.union(GC2_shapely)
    Input_2 = Input_2.difference(wg1_to_GC)

    # -----------------------------------------------------------------------------------------------
    # Optical GC on the right-----------------------------------------------------------------------
    # left_coupler = GratingCoupler.make_traditional_coupler(origin, angle=0, **coupler_params)
    wg2 = Waveguide.make_at_port(Port((10 + 180, 150), angle=incident_angle, width=[3, 50, 3]))
    wg2.add_straight_segment(length=130, final_width=[3, incident_waveguide_expand_width, 3])
    wg2.add_straight_segment(length=100, final_width=[3, incident_waveguide_width, 3])
    wg2.add_bend(pi, radius=50)
    wg2.add_straight_segment(length=58) #Straight wg before bending up
    wg2.add_bend(-pi / 2 - incident_angle, radius=49)
    wg2_to_GC = Waveguide.make_at_port(wg2.current_port, width=incident_waveguide_width)
    wg2_to_GC.add_straight_segment(length=10)
    wg2.add_straight_segment(length=10)
    GC3 = GratingCoupler.make_traditional_coupler_at_port(wg2.current_port, **GC_param)
    #
    wg2_shapely = wg2.get_shapely_object()
    GC3_shapely = convert_to_positive_resist(GC3.get_shapely_object(), 5)
    wg2_to_GC = wg2_to_GC.get_shapely_object()
    Input_3 = wg2_shapely.union(GC3_shapely)
    Input_3 = Input_3.difference(wg2_to_GC)

    # Extended waveguide for the other side's waveguide
    wg1_extend = Waveguide.make_at_port(Port((10, 150), angle=-incident_angle, width=[3, 3, 3]))
    wg1_extend.add_straight_segment(length=190, final_width=[3, 50, 3])
    wg1_ext_2 = Waveguide.make_at_port(Port((10, 150), angle=-incident_angle, width=[3, 3, 3]))
    wg1_ext_2.add_straight_segment(length=190, final_width=[3, 20, 3])

    wg2_extend = Waveguide.make_at_port(Port((10 + 180, 150), angle=np.pi + incident_angle, width=[3, 40, 3]))
    wg2_extend.add_straight_segment(length=195, final_width=[3, 10, 3])

    # WG on the bottom left
    wg3 = Waveguide.make_at_port(wg2_extend.current_port)
    wg3.add_straight_segment(length=215, final_width=[3, output_waveguide_fin_width, 3])
    wg3.add_bend(-pi / 2 - incident_angle, radius=63.5)
    wg3.add_straight_segment(length=307, final_width=[3, output_waveguide_fin_width, 3]) # LAST Straight to GC
    wg3_to_GC = Waveguide.make_at_port(wg3.current_port, width=output_waveguide_fin_width)
    wg3_to_GC.add_straight_segment(length=30)
    wg3.add_straight_segment(length=30)
    GC1 = GratingCoupler.make_traditional_coupler_at_port(wg3.current_port, **GC_param)

    wg3_shapely = wg3.get_shapely_object()
    GC1_shapely = convert_to_positive_resist(GC1.get_shapely_object(), 5)
    wg3_to_GC = wg3_to_GC.get_shapely_object()
    Input_1 = wg3_shapely.union(GC1_shapely)
    Input_1 = Input_1.difference(wg3_to_GC)

    # Driect transmission without deflection
    wg4 = Waveguide.make_at_port(wg1_extend.current_port)
    wg4.add_straight_segment(length=230, final_width=[3, output_waveguide_fin_width, 3])
    wg4.add_bend(pi / 2 + incident_angle, radius=63.5)
    wg4.add_straight_segment(length=338, final_width=[3, output_waveguide_fin_width, 3])
    wg4_to_GC = Waveguide.make_at_port(wg4.current_port, width=output_waveguide_fin_width)
    wg4_to_GC.add_straight_segment(length=5)
    wg4.add_straight_segment(length=5)
    GC4 = GratingCoupler.make_traditional_coupler_at_port(wg4.current_port, **GC_param)

    wg4_shapely = wg4.get_shapely_object()
    GC4_shapely = convert_to_positive_resist(GC4.get_shapely_object(), 5)
    wg4_to_GC = wg4_to_GC.get_shapely_object()
    Input_4 = wg4_shapely.union(GC4_shapely)
    Input_4 = Input_4.difference(wg4_to_GC)

    return Input_1, Input_2, Input_3, Input_4, wg1_extend, wg2_extend, wg1_ext_2, \
           GC1_shapely, wg1, \
           GC2_shapely, wg2, \
           GC3_shapely, wg3, \
           GC4_shapely, wg4


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

def make_Chirp_IDT_Fingers(number_of_pairs, IDT_Aperature, ZnO_Top_left):
    # Creat the IDT
    # Change parameter here:

    # How many pairs of IDT fingers
    number_of_pairs = int(number_of_pairs)
    how_many_period = number_of_pairs

    # Finger coordinate (correction of different IDT aperature)
    Finger_origin_x = ZnO_Top_left + 5 + 7  # last two term = figers offset (5um) + small_pad_width_with extended(10um)
    Finger_origin_y = 0

    # Finger offset on the other side of the horn structure
    Finger_length = IDT_Aperature

    # Pad coordinate
    arm2_right_pad_Offset = Finger_length + 4.5
    pad_length = how_many_period * 2

    # Below DO NOT CHANGE ------------------------------------------------------------------------------
    #one_period_arm2 = [finger_width, finger_width + pitch]

    Idt_finger_arm1 = []
    Idt_finger_arm2 = []
    number_of_widths = 5

    start_width =0.16
    end_width = 0.18
    litho_corrected_width = 0.005
    chirp_widths = np.linspace(start_width, end_width, num= number_of_widths )
    chirp_widths = chirp_widths[::-1]

    for index, width in enumerate(chirp_widths):
        pitch = 3 * width

        one_period_arm1 = [width - litho_corrected_width, pitch + litho_corrected_width]
        one_period_arm2 = one_period_arm1

        # Make sure the number of pairs can be equally devided into number of widths
        if (number_of_pairs/number_of_widths).is_integer() == True:
            devided_pairs = int(number_of_pairs/number_of_widths)
            for i in range(devided_pairs):

                #Change the period of the last pair in this pair group to the next pair's period
                if i == devided_pairs-1 and index != len(chirp_widths)-1 :
                    pitch1 = chirp_widths[index+1] * 3 #pitch for the last ending finger
                    pitch2 = width * 2 + chirp_widths[index+1] * 1 #pitch for the second last finger

                    one_period_arm1 = [width - litho_corrected_width, pitch1 + litho_corrected_width]
                    one_period_arm2 = [width - litho_corrected_width, pitch2 + litho_corrected_width]

                    Idt_finger_arm1.extend(one_period_arm1)
                    Idt_finger_arm2.extend(one_period_arm2)

                else:
                    Idt_finger_arm1.extend(one_period_arm1)
                    Idt_finger_arm2.extend(one_period_arm2)
        else:
            print("%0.1f pairs can not be evenly devided into %0.1f different widths" %(number_of_pairs ,number_of_widths) )
            break

    average_chirp_finger_width = (start_width + end_width)/2
    average_chirp_finger_pitch = average_chirp_finger_width* 4
    Chirped_finger_gap_offsets =  (average_chirp_finger_width + average_chirp_finger_pitch)/2 + average_chirp_finger_width/2


    # IDT ON THE "right" GRATING COUPLER
    # Finger_lower is lower idt fingers, Finger_upper is upper IDT finger (on the horn on the right)

    Finger_lower = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x - 5 + Finger_length, Finger_origin_y), angle=np.pi, width=Idt_finger_arm1))
    Finger_lower.add_straight_segment(length=Finger_length)

    Finger_upper = Waveguide.make_at_port(
        Port(origin=(Finger_origin_x + Finger_length, Finger_origin_y - 2*chirp_widths[0]+0.02 ), angle=np.pi,
             width=Idt_finger_arm2))

    Finger_upper.add_straight_segment(length=Finger_length)


    # Left small pad------------------------------------------------------------------------------------------------
    finger_width = average_chirp_finger_width
    pitch = average_chirp_finger_pitch
    shift = number_of_pairs * pitch / 1.5
    down_offset = number_of_pairs * pitch/10

    outer_corners_arm1_1 = [(Finger_origin_x - 9, Finger_origin_y - shift - down_offset),
                            # Bot-left corner
                            (Finger_origin_x - 4, Finger_origin_y - shift - down_offset),
                            # Bot-Right corner
                            (Finger_origin_x - 4, Finger_origin_y + shift - down_offset),
                            # Top-Right corner
                            (Finger_origin_x - 9, Finger_origin_y + shift - down_offset)
                            # Top-left corner
                            ]
    overlape = 10
    bot_right_y = Finger_origin_y - shift + overlape

    # Left Big pad
    X_tr = Finger_origin_x - 4
    Y_tr = bot_right_y # TOP_RIGHT

    X_tl = X_tr - 110
    Y_tl = Y_tr # TOP_LEFT

    X_br = X_tr
    Y_br = Y_tr - 100 # BOT_RIGHT

    X_br_ext1 = X_tr + arm2_right_pad_Offset/2
    Y_br_ext1 = Y_br # BOT_RIGHT extend to middle upper point

    X_br_ext2 = X_br_ext1
    Y_br_ext2 = Y_br_ext1 - 170 # BOT_RIGHT extend to middle lower point

    X_bl = X_tl
    Y_bl = Y_br_ext2 # BOT_LEFT:

    Outer_corners_Big_pad1_1 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl, Y_bl),
                                (X_br_ext2, Y_br_ext2),
                                (X_br_ext1, Y_br_ext1),
                                (X_br, Y_br)
                                ]
    X_br_ext1_left_buff = X_br_ext1
    Y_br_ext2_left_buff = Y_br_ext2
    # Right small pad-----------------------------------------------------------------------------------------------
    outer_corners_arm1_2 = [
        (Finger_origin_x + arm2_right_pad_Offset - 0, Finger_origin_y - shift - down_offset),
        # Bot-right corner
        (Finger_origin_x + arm2_right_pad_Offset - 5, Finger_origin_y - shift - down_offset),
        # Bot-left corner
        (Finger_origin_x + arm2_right_pad_Offset - 5, Finger_origin_y + shift - down_offset),  # Top-left corner
        (Finger_origin_x + arm2_right_pad_Offset - 0, Finger_origin_y + shift - down_offset)]  # Top-right corner

    #Right big pad--------------------------------------------------------------------------------------------------
    bot_right_y = Finger_origin_y - shift + overlape
    # Left Big pad
    X_tl = Finger_origin_x + arm2_right_pad_Offset - 5
    Y_tl = bot_right_y  # TOP_RIGHT

    X_tr = X_tl + 110
    Y_tr = Y_tl  # TOP_LEFT

    X_bl = X_tl
    Y_bl = Y_tl - 100  # BOT_LEFT:

    X_bl_ext1 = X_br_ext1_left_buff  + 10
    Y_bl_ext1 = Y_bl # BOT_left extend to middle upper point

    X_bl_ext2 = X_bl_ext1
    Y_bl_ext2 = Y_br_ext2_left_buff  # BOT_left extend to middle lower point

    X_br = X_tr
    Y_br = Y_bl_ext2  # BOT_RIGHT

    Outer_corners_Big_pad1_2 = [(X_tr, Y_tr),
                                (X_tl, Y_tl),
                                (X_bl, Y_bl),
                                (X_bl_ext1, Y_bl_ext1),
                                (X_bl_ext2, Y_bl_ext2),
                                (X_br, Y_br)
                                ]


    small_pad_arm1_1 = Polygon(outer_corners_arm1_1)
    Big_pad1_1 = Polygon(Outer_corners_Big_pad1_1)
    small_pad_arm1_2 = Polygon(outer_corners_arm1_2)
    Big_pad1_2 = Polygon(Outer_corners_Big_pad1_2)

    return Finger_lower, Finger_upper, small_pad_arm1_1, small_pad_arm1_2, Big_pad1_1, Big_pad1_2

def make_IDT_Fingers_pairs(figer_widths, number_of_period, IDT_Aperature, ZnO_Top_left):
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
    #Finger_lower_other_side is left IDT finger, wg_2 is right IDT finger
    Finger_lower_other_side = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset , Finger_origin_y-5), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_lower_other_side.add_straight_segment(length = Finger_length)

    Finger_upper_other_side = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset + Figer_gap_offset, Finger_origin_y ), angle=np.pi / 2, width=Idt_finger_arm2))
    Finger_upper_other_side.add_straight_segment(length=Finger_length)

    # Make Small metal pad
    outer_corners_arm2_1 = [
        (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset, Finger_origin_y - 10),
        (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset, Finger_origin_y - 5),
        (Finger_origin_x - pad_length * 1 * (figer_width + pitch) - Finger_left_offset, Finger_origin_y - 5),
        (Finger_origin_x - pad_length * 1 * (figer_width + pitch) - Finger_left_offset, Finger_origin_y - 10)]

    outer_corners_arm2_2 = [(Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset,
                             Finger_origin_y + arm2_right_pad_Offset),
                            (Finger_origin_x + pad_length * (figer_width + pitch) / 2 - Finger_left_offset,
                             Finger_origin_y + arm2_right_pad_Offset - 5),
                            (Finger_origin_x - pad_length * 1 * (figer_width + pitch) - Finger_left_offset,
                             Finger_origin_y + arm2_right_pad_Offset - 5),
                            (Finger_origin_x - pad_length * 1 * (figer_width + pitch) - Finger_left_offset,
                             Finger_origin_y + arm2_right_pad_Offset)]

    # --------------------------------------------------------------------------------------------------------------
    # Left small pad------------------------------------------------------------------------------------------------
    outer_corners_arm1_1 = [(Finger_origin_x - 9, Finger_origin_y - pad_length * (figer_width + pitch) / 2),
                            # Bot-left corner
                            (Finger_origin_x - 4, Finger_origin_y - pad_length * (figer_width + pitch) / 2),
                            # Bot-Right corner
                            (Finger_origin_x - 4,
                             Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period - 26) - 16),
                            # Top-Right corner
                            (Finger_origin_x - 9,
                             Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period - 26) - 16)
                            # Top-left corner
                            ]
    # Left Big pad
    Outer_corners_Big_pad1_1 = [(Finger_origin_x - 9, Finger_origin_y - pad_length * (figer_width + pitch) / 2),
                                # Bot-left corner
                                (Finger_origin_x - 4, Finger_origin_y - pad_length * (figer_width + pitch) / 2),
                                # Bot-Right corner
                                (Finger_origin_x - 4, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (
                                            number_of_period - 26) - 16),  # Top-Right corner
                                (Finger_origin_x - 9, Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (
                                            number_of_period - 26) - 16)  # Top-left corner
                                ]
    # --------------------------------------------------------------------------------------------------------------
    # Right small pad-----------------------------------------------------------------------------------------------
    outer_corners_arm1_2 = [
        (Finger_origin_x + arm2_right_pad_Offset - 0, Finger_origin_y - pad_length * (figer_width + pitch) / 2),
        # Bot-right corner
        (Finger_origin_x + arm2_right_pad_Offset - 5, Finger_origin_y - pad_length * (figer_width + pitch) / 2),
        # Bot-left corner
        (Finger_origin_x + arm2_right_pad_Offset - 5,
         Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period - 26) - 16),  # Top-left corner
        (Finger_origin_x + arm2_right_pad_Offset - 0,
         Finger_origin_y + pad_length * (figer_width + pitch) / 1.3 - (number_of_period - 26) - 16)]  # Top-right corner

    small_pad_arm2_1 = Polygon(outer_corners_arm2_1)
    small_pad_arm2_2 = Polygon(outer_corners_arm2_2)
    small_pad_arm1_1 = Polygon(outer_corners_arm1_1)
    small_pad_arm1_2 = Polygon(outer_corners_arm1_2)

    return Finger_lower, Finger_upper, small_pad_arm1_1, small_pad_arm1_2 ,small_pad_arm2_1, small_pad_arm2_2

def make_ZnO_pad(Finger_length, number_of_pairs):
    # Create ZnO
    start_f_w = 0.19
    end_f_w = 0.17
    average_f_w = (start_f_w + end_f_w)/2
    average_p = 4 * average_f_w
    ZnO_Y_length = number_of_pairs * average_p

    # ZnO Expand
    ZnO_expand_x = 10
    ZnO_expand_y = 5
    ZnO_Original = 98
    ZnO_Original_L = 30

    # Make_ZnO_Pad
    Outer_corner_ZnO_pad_R = [(ZnO_Original + Finger_length / 2 + ZnO_expand_x,  - ZnO_Y_length/2 - ZnO_expand_y ), #Bot Right
                              (ZnO_Original + Finger_length / 2 + ZnO_expand_x,  + ZnO_Y_length/2 + ZnO_expand_y ), #Top Right
                              (ZnO_Original - Finger_length / 2 - ZnO_expand_x,  + ZnO_Y_length/2 + ZnO_expand_y ), #Top Left
                              (ZnO_Original - Finger_length / 2 - ZnO_expand_x,  - ZnO_Y_length/2 - ZnO_expand_y )] #Bot Left
    #Buffer coordinates
    zno_pad_right_x = ZnO_Original + Finger_length / 2 + ZnO_expand_x
    zno_pad_top_y = + ZnO_Y_length/2 + ZnO_expand_y
    zno_pad_left_x = ZnO_Original - Finger_length / 2 - ZnO_expand_x
    zno_pad_bot_y = - ZnO_Y_length / 2 - ZnO_expand_y

    #Get the cordinate of ZnO Top left corner
    ZnO_Top_left = ZnO_Original - Finger_length / 2 - ZnO_expand_x

    #Make_ZnO_Extended for under etched part
    extended_y = 150
    extended_x = 35
    Outer_corner_ZnO_extended = [(zno_pad_right_x + extended_x, zno_pad_bot_y - extended_y),
                              (zno_pad_right_x + extended_x,  zno_pad_top_y + extended_y),
                              (zno_pad_left_x - extended_x,  zno_pad_top_y + extended_y),
                              (zno_pad_left_x - extended_x,  zno_pad_bot_y - extended_y)]

    #Make SAW propagation area suspended
    Outer_corner_SAW_Prop = [(ZnO_Original + Finger_length / 2, - ZnO_expand_y - 15),
                                 (ZnO_Original + Finger_length / 2, 20 + ZnO_expand_y - 25 + 200 ),
                                 (ZnO_Original - Finger_length / 2, 20 + ZnO_expand_y - 25 + 200 ),
                                 (ZnO_Original - Finger_length / 2, - ZnO_expand_y - 15)]

    #Make a etch window behind IDT to reflect power

    # reference y coordinate for IDT etch window

    idt_start_y = zno_pad_bot_y - 5  # 5 um is the distance of zno pad to idt window
    Idt_window_length = 10
    window_offset_x = 5



    Outer_corner_IDT_window= [(ZnO_Original + Finger_length / 2 - window_offset_x, idt_start_y), #Top right
                                 (ZnO_Original + Finger_length / 2 - window_offset_x, idt_start_y - Idt_window_length), #bot right
                                 (ZnO_Original - Finger_length / 2 + window_offset_x,  idt_start_y - Idt_window_length), #bot left
                                 (ZnO_Original - Finger_length / 2 + window_offset_x, idt_start_y)] #top left

    idt_start_y_top = zno_pad_bot_y + 220
    window_offset_x_top = 10
    pos_offset_x_top = 10
    windows_length =65

    Outer_corner_IDT_window_top_1 = [(ZnO_Original - window_offset_x_top -  pos_offset_x_top, idt_start_y_top),  # Top right
                               (ZnO_Original - window_offset_x_top -  pos_offset_x_top, idt_start_y_top - Idt_window_length),
                               # bot right
                               (ZnO_Original - windows_length -  pos_offset_x_top , idt_start_y_top - Idt_window_length),
                               # bot left
                               (ZnO_Original - windows_length -  pos_offset_x_top , idt_start_y_top)]  # top left

    Outer_corner_IDT_window_top_2 = [(ZnO_Original + windows_length  -  pos_offset_x_top, idt_start_y_top),  # Top right
                                     (ZnO_Original + windows_length  -  pos_offset_x_top, idt_start_y_top - Idt_window_length),
                                     # bot right
                                     (ZnO_Original + window_offset_x_top -  pos_offset_x_top,  idt_start_y_top - Idt_window_length),
                                     # bot left
                                     (ZnO_Original + window_offset_x_top -  pos_offset_x_top, idt_start_y_top)]  # top left


    side_window_width = 5
    left_side_window_TR_x = zno_pad_left_x - 5
    left_side_window_BR_x = left_side_window_TR_x
    left_side_window_TR_y = zno_pad_top_y -2
    left_side_window_BR_y = zno_pad_bot_y + 20

    Outer_corner_IDT_window_left = [(left_side_window_TR_x, left_side_window_TR_y), #Top right
                                 (left_side_window_BR_x, left_side_window_BR_y), #bot right
                                 (left_side_window_BR_x - side_window_width,  left_side_window_BR_y), #bot left
                                 (left_side_window_TR_x - side_window_width, left_side_window_TR_y)] #top left

    right_side_window_TR_x = zno_pad_right_x + 5
    right_side_window_BR_x = right_side_window_TR_x
    right_side_window_TR_y = zno_pad_top_y -2
    right_side_window_BR_y = zno_pad_bot_y + 20
    Outer_corner_IDT_window_right = [(right_side_window_TR_x, right_side_window_TR_y),  # Top left
                                    (right_side_window_BR_x, right_side_window_BR_y),  # bot left
                                    (right_side_window_BR_x + side_window_width, right_side_window_BR_y),  # bot right
                                    (right_side_window_TR_x + side_window_width, right_side_window_TR_y)]  # top right

    # Outer_corner_ZnO_pad_L = [(ZnO_Original_L - prop_length - pad_length / 2 - ZnO_expand_x, -15 - ZnO_expand_y),
    #                          (ZnO_Original_L - prop_length - pad_length / 2 - ZnO_expand_x, -15 + IDT_aperature + 10 + ZnO_expand_y),
    #                          (ZnO_Original_L - prop_length + pad_length / 2 + ZnO_expand_x, -15 + IDT_aperature + 10 + ZnO_expand_y),
    #                          (ZnO_Original_L - prop_length + pad_length / 2 + ZnO_expand_x, -15 - ZnO_expand_y)]

    ZnO_pad_R = Polygon(Outer_corner_ZnO_pad_R)
    # ZnO_pad_L = Polygon(Outer_corner_ZnO_pad_L)
    IDT_window_top_1 = Polygon(Outer_corner_IDT_window_top_1)
    IDT_window_top_2 = Polygon(Outer_corner_IDT_window_top_2)
    ZnO_extended = Polygon(Outer_corner_ZnO_extended)
    Saw_prop_area = Polygon(Outer_corner_SAW_Prop)
    IDT_window = Polygon(Outer_corner_IDT_window)
    left_IDT_window = Polygon(Outer_corner_IDT_window_left)
    right_IDT_window = Polygon(Outer_corner_IDT_window_right)

    return ZnO_pad_R, ZnO_extended, Saw_prop_area, ZnO_Top_left, IDT_window, left_IDT_window, right_IDT_window, IDT_window_top_1, IDT_window_top_2

def make_EBL_markers(layout_cell):
    # change marker dimension
    cross_l = 20
    croww_w = 5
    paddle_l = 5
    paddle_w = 5
    square_marker_size = 10
    top_marker_y = 6800
    right_most_marker_x = 7400
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

    fifteenfifty_coup_param = {
        'width': 0.3,
        'full_opening_angle': np.deg2rad(30),
        'grating_period': 0.76,
        'grating_ff': 0.75,
        'ap_max_ff': 0.80,
        'n_gratings': 20,
        'taper_length': 16,
        'n_ap_gratings': 20,
    }

    fifteenfifty_coup_param_gap_sapp = {
        'width': 0.3,
        'full_opening_angle': np.deg2rad(30),
        'grating_period': 0.76,
        'grating_ff': 0.79,
        'ap_max_ff': 0.84,
        'n_gratings': 20,
        'taper_length': 16,
        'n_ap_gratings': 20,
    }

    #Make the frequency shifter
    Input_1, Input_2, Input_3, Input_4, wg1_extended, wg2_extended, wg1_ext_2, \
    GC1_shapely, wg1, \
    GC2_shapely, wg2, \
    GC3_shapely, wg3, \
    GC4_shapely, wg4  = make_frequency_shifter_waveguide( GC_param= fifteenfifty_coup_param , input_angle=26)

    # Make ZnO pads
    ZnO_pad_R, ZnO_extended, \
    Saw_prop_area, ZnO_Top_left, \
    IDT_window, left_IDT_window, right_IDT_window, \
    IDT_window_top_1, IDT_window_top_2= make_ZnO_pad(Finger_length= sweep2, number_of_pairs=sweep1)

    #Make the IDT fingers
    Finger_lower, Finger_upper, small_pad_arm1_1, small_pad_arm1_2, Big_pad1_1, Big_pad1_2 = make_Chirp_IDT_Fingers(
                                                                                         number_of_pairs=sweep1,
                                                                                         IDT_Aperature=sweep2,
                                                                                         ZnO_Top_left=ZnO_Top_left)
    #Make the underetched part
    underetching_parts = geometric_union([wg1, wg2, wg3, wg4]) #, wg1_extended, wg2_extended
    complete_structure = geometric_union([ ZnO_extended, Big_pad1_1, Big_pad1_2, wg1_ext_2,
                                           GC1_shapely, GC2_shapely, GC3_shapely, GC4_shapely ])

    underetching_parts_GC = geometric_union([GC1_shapely, GC2_shapely, GC3_shapely, GC4_shapely])
    complete_structure_GC = geometric_union([wg1, wg2, wg3, wg4])


    holes = create_holes_for_under_etching(underetch_parts=underetching_parts,
                                           complete_structure=complete_structure,
                                           hole_radius=5,
                                           hole_distance=15.8,
                                           hole_spacing=50, #org 35
                                           hole_length=29.7,
                                           cap_style='square')

    holes_GC = create_holes_for_under_etching(underetch_parts=underetching_parts_GC,
                                           complete_structure=complete_structure_GC,
                                           hole_radius=8,
                                           hole_distance=20,
                                           hole_spacing=67,  # org 58
                                           hole_length=0,
                                           cap_style='square')


        # Add name to cell
    text = Text(origin=[-500, -300], height=50, text=str(cell_name), alignment='left-bottom')

    #Add Cell
    cell = Cell('SIMPLE_RES_DEVICE r={:.4f} g={:.4f}'.format(sweep1, sweep2))

    cell.add_to_layer(1, Input_1, Input_2, Input_3,Input_4, text)
    cell.add_to_layer(2, ZnO_pad_R)
    cell.add_to_layer(3, Finger_lower,  Finger_upper ,small_pad_arm1_1 ,small_pad_arm1_2)
    cell.add_to_layer(4, Big_pad1_1, Big_pad1_2)
    cell.add_to_layer(5, holes, holes_GC, IDT_window, left_IDT_window, right_IDT_window, IDT_window_top_1, IDT_window_top_2)

    #cell.add_to_layer(5, left_coupler)

    #cell.add_ebl_marker(layer=1, marker=CrossMarker(origin=(-500,-300 ), cross_length=10 , cross_width=5, paddle_length=5, paddle_width=5))

    return cell

if __name__ == "__main__":

    layout = GridLayout(title='AOFS5', frame_layer=0, text_layer=1, region_layer_type=None, horizontal_spacing=100, vertical_spacing=0)

    #Parameters wanted to scan-------------------------------------------
    #1550nm (best performance max_duty=0.80 grating_pitch=0.76)
    maximum_duty = np.linspace(0.75, 0.82, num = 2)
    grating_pitch = np.linspace(0.75, 0.77, num= 2)
    step = 10 #10
    number_of_finger_pairs = np.linspace(30, 90, num= int( (90-30) / step ) +1)
    IDT_Aperatures = np.linspace(50, 150, num= 5) #5

    Parameters_scan_1 = number_of_finger_pairs
    Parameters_scan_2 = IDT_Aperatures

    print('Scan1 =', Parameters_scan_1)
    print('Scan2 =', Parameters_scan_2)

    #--------------------------------------------------------------------
    total = len(Parameters_scan_1) * len(Parameters_scan_2)
    count = 0
    #--------------------------------------------------------------------
    #Get input from user to see if they want show or save
    answer = input('Show or Save Layout?\n Input (show/save):')

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
        layout.add_to_row(generate_device_cell(  sweep1=90, sweep2=150, cell_name=7 ))
        layout_cell, mapping = layout.generate_layout()
        layout_cell.show()

    if show == False:
        #Start looping over the scanned parameters
        #Add column labels
        layout.add_column_label_row(('AP= %0.2f' % param_2 for param_2 in Parameters_scan_2), row_label='')

        for param_1 in Parameters_scan_1:
            layout.begin_new_row('Num=\n%0.2f' % param_1)
            for param_2 in Parameters_scan_2:
                count =  count + 1
                complete = count/total
                print("Number of cell generated / Total cell = %0.1f/%0.1f (%0.2f%% complete) " %(count ,total,complete*100) )
                layout.add_to_row(generate_device_cell( sweep1= param_1, sweep2=param_2, cell_name=count), alignment='center-center' , realign=True)

        layout_cell, mapping = layout.generate_layout()

        # Show and then save the layout!
        make_EBL_markers(layout_cell)
        layout_cell.add_ebl_frame(layer=1,size=40, frame_generator=raith_marker_frame, n=2)
        print('Showing........')
        layout_cell.show()
        print('Showing.... DONE')
        print('SAVING....')
        layout_cell.save('AOFS_V5_param_test.gds', parallel=True)
        print('SAVED!!!')