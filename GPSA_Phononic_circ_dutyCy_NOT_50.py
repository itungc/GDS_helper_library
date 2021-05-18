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

from gdshelpers.geometry.ebl_frame_generators import raith_marker_frame




#The grating ff is the maximum duty cycle of the grating coupler
#ap_max_ff is the minimum duty cycle of the grating coupler
minimum_duty = 0.850
maximum_duty = 0.870

coupler_params = {
    'width': 1,
    'full_opening_angle': np.deg2rad(5.5),
    'grating_period': 0,
    'grating_ff':minimum_duty ,
    'ap_max_ff':maximum_duty,
    'n_gratings': 0,
    'taper_length': 70,
    'n_ap_gratings':0,

}
def generate_device_cell(resonator_radius, resonator_gap, prop_length,IDT_aperature, origin=(0, 0)):
    #Creat the Acoustic waveguide
    left_coupler = GratingCoupler.make_traditional_coupler(origin, angle=0, **coupler_params)
    wg1 = Waveguide.make_at_port(left_coupler.port)
    wg1.add_straight_segment(length=50)
    #wg1.add_bend(-pi/2, radius=50)
    wg1.add_straight_segment(length=50)

    ring_res = RingResonator.make_at_port(wg1.current_port, gap=resonator_gap, radius=resonator_radius)

    wg2 = Waveguide.make_at_port(ring_res.port)
    wg2.add_straight_segment(length=50)
    #wg2.add_bend(-pi/2, radius=50)
    wg2.add_straight_segment(length=50)
    right_coupler = GratingCoupler.make_traditional_coupler_at_port(wg2.current_port, **coupler_params)

    #Creat the IDT

    #Change parameter here:
        #Finger characteristics
    figer_width = 0.250
    pitch = figer_width*2.8
    Figer_gap_offset = (figer_width + pitch )/2 + figer_width/2
        #How many pairs of IDT fingers
    how_many_period = 30
    radius = how_many_period / 1.7
        #Finger coordinate
    Finger_origin_x = 49
    Finger_origin_y = -8
        #Finger offset on the other side of the horn structure
    Finger_left_offset = 298
    Finger_length = 20

        #Pad coordinate
    arm2_right_pad_Offset = Finger_length + 4.5
    pad_length = how_many_period * 2

    Right_IDT_final_Angel = np.pi / 4 + np.pi / 25 #angel decrease, the right exposed finger is shorter
    Left_IDT_final_angel = - np.pi / 4.7 #angle decress, the left exposed finger is shorter #Demominator has to bigger than 4
    top_right = -1 * Right_IDT_final_Angel
    top_left = -1 * Left_IDT_final_angel

    # ZnO Expand
    ZnO_expand_x = 10
    ZnO_expand_y = 15

    #Below DO NOT CHANGE ------------------------------------------------------------------------------
    one_period_arm2 = [figer_width, figer_width + pitch  ]

    Idt_finger_arm2 = []


    for i in range(how_many_period ):
        Idt_finger_arm2.extend(one_period_arm2)

    #IDT ON THE "right" GRATING COUPLER
    #Finger_lower is lower idt fingers, Finger_upper is upper IDT finger (on the horn on the right)
    Finger_lower = Waveguide.make_at_port(Port(origin=(Finger_origin_x , Finger_origin_y-5), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_lower.add_straight_segment(length=Finger_length)

    Finger_upper = Waveguide.make_at_port(Port(origin=(Finger_origin_x + Figer_gap_offset , Finger_origin_y), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_upper.add_straight_segment(length=Finger_length)


    #SAME IDT ON THE "left" GRATING COUPLER ---------------------------------------------------------------------------------------------------
    #Finger_lower_other_side is left IDT finger, wg_2 is right IDT finger
    Finger_lower_other_side = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset , Finger_origin_y-5), angle=np.pi/2, width=Idt_finger_arm2))
    Finger_lower_other_side.add_straight_segment(length = Finger_length)

    Finger_upper_other_side = Waveguide.make_at_port(Port(origin=(Finger_origin_x - Finger_left_offset + Figer_gap_offset, Finger_origin_y ), angle=np.pi / 2, width=Idt_finger_arm2))
    Finger_upper_other_side.add_straight_segment(length=Finger_length)

    #Make Small metal pad
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

    outer_corners_arm1_1 = [(Finger_origin_x - pad_length * (figer_width + pitch) / 2, Finger_origin_y - 10),
                            (Finger_origin_x - pad_length * (figer_width + pitch) / 2, Finger_origin_y - 5),
                            (Finger_origin_x + pad_length * 1 * (figer_width + pitch), Finger_origin_y - 5),
                            (Finger_origin_x + pad_length * 1 * (figer_width + pitch), Finger_origin_y - 10)]

    outer_corners_arm1_2 = [
        (Finger_origin_x - pad_length * (figer_width + pitch) / 2, Finger_origin_y + arm2_right_pad_Offset),
        (Finger_origin_x - pad_length * (figer_width + pitch) / 2, Finger_origin_y + arm2_right_pad_Offset - 5),
        (Finger_origin_x + pad_length * 1 * (figer_width + pitch), Finger_origin_y + arm2_right_pad_Offset - 5),
        (Finger_origin_x + pad_length * 1 * (figer_width + pitch), Finger_origin_y + arm2_right_pad_Offset)]

    small_pad_arm2_1 = Polygon(outer_corners_arm2_1)
    small_pad_arm2_2 = Polygon(outer_corners_arm2_2)
    small_pad_arm1_1 = Polygon(outer_corners_arm1_1)
    small_pad_arm1_2 = Polygon(outer_corners_arm1_2)

    # Make_ZnO_Pad
    Outer_corner_ZnO_pad_R = [(100 + ZnO_expand_x, -15 - ZnO_expand_y),
                              (100 + ZnO_expand_x, -15 + IDT_aperature + 10 + ZnO_expand_y),
                              (100 - pad_length - ZnO_expand_x, -15 + IDT_aperature + 10 + ZnO_expand_y),
                              (100 - pad_length - ZnO_expand_x, -15 - ZnO_expand_y)]

    Outer_corner_ZnO_pad_L = [(-prop_length - ZnO_expand_x, -15 - ZnO_expand_y),
                              (-prop_length - ZnO_expand_x, -15 + IDT_aperature + 10 + ZnO_expand_y),
                              (-prop_length + pad_length + ZnO_expand_x, -15 + IDT_aperature + 10 + ZnO_expand_y),
                              (-prop_length + pad_length + ZnO_expand_x, -15 - ZnO_expand_y)]

    ZnO_pad_R = Polygon(Outer_corner_ZnO_pad_R)
    ZnO_pad_L = Polygon(Outer_corner_ZnO_pad_L)

    #Add Cell
    cell = Cell('SIMPLE_RES_DEVICE r={:.1f} g={:.1f}'.format(resonator_radius, resonator_gap))

    cell.add_to_layer(1, convert_to_positive_resist([left_coupler, wg1, ring_res, wg2, right_coupler],10 ))
    cell.add_to_layer(2, ZnO_pad_R, ZnO_pad_L)
    cell.add_to_layer(3, Finger_lower,  Finger_upper, Finger_lower_other_side, Finger_upper_other_side,
                                                             small_pad_arm2_1,small_pad_arm2_2,
                                                             small_pad_arm1_1,small_pad_arm1_2)
    


    cell.add_ebl_marker(layer=1, marker=CrossMarker(origin=(-500,-300 ), cross_length=10 , cross_width=5, paddle_length=5, paddle_width=5))


    return cell



layout = GridLayout(title='ITGAP11', frame_layer=0, text_layer=2, region_layer_type=None, horizontal_spacing=100, vertical_spacing=0)
radii = np.linspace(5, 70, 8)
gaps = np.linspace(0.1, 0.9, 7)
total = len(radii) * len(gaps)
count = 0
# Add column labels
layout.add_column_label_row( (''),row_label='')
#('Gap %0.2f' % gap for gap in gaps)

#True if you just want to see!!
show = False


if show == True:
    layout.add_to_row(generate_device_cell(50, 0.5))

if show == False:
    for radius in radii:
        layout.begin_new_row()
        for gap in gaps:
            count =  count + 1
            complete = count/total
            print("Number of cell generated / Total cell = %0.1f/%0.1f (%0.2f%% complete) " %(count ,total,complete*100) )
            layout.add_to_row(generate_device_cell(radius, gap, prop_length = 298, IDT_aperature = 20 ), alignment='center-center' , realign=True)
#'R=\n%0.2f' % radius

layout_cell, mapping = layout.generate_layout()
#change marker dimension
cross_l = 20
croww_w = 5
paddle_l = 5
paddle_w = 5
square_marker_size = 10
top_marker_y =4400
right_most_marker_x = 6400
X_Position_list = [0, right_most_marker_x/4, right_most_marker_x/2, right_most_marker_x*3/4, right_most_marker_x]
Y_Position_list = [0, top_marker_y/4, top_marker_y/2, top_marker_y*3/4, top_marker_y]
Layer_list = [1,4]
#Make Global Marker
for x_position in X_Position_list:
    for y_position in Y_Position_list:
        for layer in Layer_list:
            if layer == 1:
                layout_cell.add_ebl_marker(layer=layer,
                                   marker=CrossMarker(origin=(x_position, y_position), cross_length=cross_l, cross_width=croww_w,
                                                      paddle_length=paddle_l, paddle_width=paddle_w))
            else:
                layout_cell.add_ebl_marker(layer=layer,
                                          marker=SquareMarker((x_position + square_marker_size, y_position + square_marker_size), square_marker_size))
                layout_cell.add_ebl_marker(layer=layer,
                                           marker=SquareMarker((x_position + square_marker_size, y_position - square_marker_size), square_marker_size))
                layout_cell.add_ebl_marker(layer=layer,
                                           marker=SquareMarker((x_position - square_marker_size, y_position + square_marker_size), square_marker_size))
                layout_cell.add_ebl_marker(layer=layer,
                                           marker=SquareMarker((x_position - square_marker_size, y_position - square_marker_size), square_marker_size))


#Uncomment this if you just want to see
if show == True:
    layout_cell.show()

# Create the GDS file, un-comment if want to save!
if show == False:
    print('saving........')
    layout_cell.save('IDT_DC40_PHON_circ.gds')
    print('saved!!!')