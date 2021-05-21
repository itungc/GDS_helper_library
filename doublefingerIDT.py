def double_finger_idt(fw, frequency, wavelength, periods, height, surface_velocity, offset, layer, coords):
    # f_or_w should be entered as 0 for f or 1 for w, depending on whether you would like to specify wavelength or frequency
    # if specifying wavelength, enter 1 for frequency and surface velocity (should be in um)
    # pads will be finger overlap x length of IDT, width can be easily changed by changing the values,
    # length should be changed by adding an additional waveguide in a separate function
    # overlap with fingers is set by 2um, this can also be changed below if desired
    # coords will be location of lower left corner
    # coords = (x, y)

    from gdshelpers.geometry.chip import Cell
    from shapely.geometry import Polygon
    from gdshelpers.parts.marker import CrossMarker

    finger_overlap = 2
    pad_height = finger_overlap
    shift = pad_height - finger_overlap
    idt = Cell('fingers')

    if fw == 0:
        wavelength = (surface_velocity/frequency)*10**6

    width = wavelength/8
    ox = coords[0]
    oy = coords[1]

    upper_coord = [(ox+2*width+wavelength/2, oy+offset+pad_height),
                   (ox+2*width+wavelength/2, oy+offset+height+pad_height+finger_overlap),
                   (ox+2*width+wavelength/2+width, oy+offset+height+pad_height+finger_overlap),
                   (ox+2*width+wavelength/2+width, oy+offset+pad_height)]
    lower_coord = [(ox+2*width, oy+shift), (ox+2*width, oy+height+pad_height),
                   (ox+2*width+width, oy+height+pad_height), (ox+2*width+width, oy+shift)]
    pad_width = 0
    pu_coord = 0

    for i in range(periods):
        uc1 = [(upper_coord[0][0] + i*wavelength, upper_coord[0][1]),
               (upper_coord[1][0] + i*wavelength, upper_coord[1][1]),
               (upper_coord[2][0] + i*wavelength, upper_coord[2][1]),
               (upper_coord[3][0] + i*wavelength, upper_coord[3][1])]

        uc2 = [(upper_coord[0][0] + 2*width + i * wavelength, upper_coord[0][1]),
               (upper_coord[1][0] + 2*width + i * wavelength, upper_coord[1][1]),
               (upper_coord[2][0] + 2*width + i * wavelength, upper_coord[2][1]),
               (upper_coord[3][0] + 2*width + i * wavelength, upper_coord[3][1])]

        lc1 = [(lower_coord[0][0] + i*wavelength, lower_coord[0][1]),
               (lower_coord[1][0] + i*wavelength, lower_coord[1][1]),
               (lower_coord[2][0] + i*wavelength, lower_coord[2][1]),
               (lower_coord[3][0] + i*wavelength, lower_coord[3][1])]

        lc2 = [(lower_coord[0][0] + 2*width + i * wavelength, lower_coord[0][1]),
               (lower_coord[1][0] + 2*width + i * wavelength, lower_coord[1][1]),
               (lower_coord[2][0] + 2*width + i * wavelength, lower_coord[2][1]),
               (lower_coord[3][0] + 2*width + i * wavelength, lower_coord[3][1])]

        pad_width = uc2[2][0]
        pu_coord = uc2[2][1]

        u_rect1 = Polygon(uc1)
        u_rect2 = Polygon(uc2)
        l_rect1 = Polygon(lc1)
        l_rect2 = Polygon(lc2)
        idt.add_to_layer(layer, u_rect1, l_rect1, u_rect2, l_rect2)

    pl = [(ox, oy), (ox, oy + pad_height), (4 * width + pad_width, oy + pad_height), (4 * width + pad_width, oy)]
    pu = [(ox, pu_coord - finger_overlap), (ox, pu_coord - finger_overlap + pad_height),
          (4 * width + pad_width, pu_coord - finger_overlap + pad_height),
          (4 * width + pad_width, pu_coord - finger_overlap)]

    pad_lower = Polygon(pl)
    pad_upper = Polygon(pu)
    idt.add_to_layer(layer, pad_lower, pad_upper)

    return idt


cell = double_finger_idt(fw=1, frequency=1,wavelength=4, periods=48, height=20, surface_velocity=1,
                         offset=1, layer=1, coords=(1,1))
cell.save("dfIDT.gds")
