# 2 double finger unfocused IDTs set to create standing wave with pads and align marks

def double_finger_idt_wp(fw, frequency, wavelength, periods, height, surface_velocity, offset, finger_layer,
                      pad_layer, align_layer, coords, label):
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
    from gdshelpers.parts.text import Text

    finger_overlap = 2
    pad_height = finger_overlap
    shift = pad_height - finger_overlap
    idt = Cell(label)

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
        idt.add_to_layer(finger_layer, u_rect1, l_rect1, u_rect2, l_rect2)

    pl00 = min(4 * width + pad_width - 80, ox)
    pl = [(pl00, oy), (pl00, oy + pad_height), (4 * width + pad_width, oy + pad_height), (4 * width + pad_width, oy)]
    pu = [(pl00 - 50, pu_coord - finger_overlap), (pl00 - 50, pu_coord - finger_overlap + pad_height),
          (4 * width + pad_width, pu_coord - finger_overlap + pad_height),
          (4 * width + pad_width, pu_coord - finger_overlap)]
    pu1 = [(pl00 - 50, pu_coord - finger_overlap + pad_height),
           (pl00 - 20, pu_coord - finger_overlap + pad_height),
           (pl00 - 20, oy + pad_height - 100),
           (pl00 - 50, oy + pad_height - 100)]
    pu2 = [(pl00 - 50, oy + pad_height - 100), (pl00 - 50, oy + pad_height - 70),
           (4 * width + pad_width - 150, oy + pad_height - 70), (4 * width + pad_width - 150, oy + pad_height - 100)]
    pua = Polygon(pu1)
    pub = Polygon(pu2)
    pud = pua.union(pub)
    short_lower = Polygon(pl)
    short_upper = Polygon(pu)
    pla1 = [(4 * width + pad_width, oy + pad_height), (4 * width + pad_width - 30, oy + pad_height),
            (4 * width + pad_width - 30, oy + pad_height - 75), (4 * width + pad_width, oy + pad_height - 75)]
    bl = [(4 * width + pad_width + 20, oy + pad_height - 50), (4 * width + pad_width + 20, oy + pad_height - 200),
          (4 * width + pad_width - 80, oy + pad_height - 200), (4 * width + pad_width - 80, oy + pad_height - 50)]
    bu = [(4 * width + pad_width - 100, oy + pad_height - 200),
          (4 * width + pad_width - 100, oy + pad_height - 50),
          (4 * width + pad_width - 200, oy + pad_height - 50),
          (4 * width + pad_width - 200, oy + pad_height - 200)]
    plc = Polygon(bl)
    pla = Polygon(pla1)
    puc = Polygon(bu)
    pad_upper = puc.union(pud)
    pad_lower = plc.union(pla)
    idt.add_to_layer(pad_layer, short_lower, short_upper, pad_lower, pad_upper)

    ox1 = coords[0] + pad_width + 60

    upper_coord1 = [(ox1 + 2 * width + 2 * width, oy + offset + shift + pad_height),
                    (ox1 + 2 * width + 2 * width, oy + offset + height + shift + finger_overlap + pad_height),
                    (ox1 + 3 * width + 2 * width, oy + offset + height + shift + finger_overlap + pad_height),
                    (ox1 + 3 * width + 2 * width, oy + offset + shift + pad_height)]
    lower_coord1 = [(ox1 + 2 * width, oy + shift), (ox1 + 2 * width, oy + finger_overlap + height),
                    (ox1 + width + 2 * width, oy + finger_overlap + height), (ox1 + width + 2 * width, oy + shift)]
    pad_width1 = 0
    pu_coord1 = 0
    for i in range(periods):
        uc1 = [(upper_coord1[0][0] + 2*width + i*wavelength, upper_coord1[0][1]),
               (upper_coord1[1][0] + 2*width + i*wavelength, upper_coord1[1][1]),
               (upper_coord1[2][0] + 2*width + i*wavelength, upper_coord1[2][1]),
               (upper_coord1[3][0] + 2*width + i*wavelength, upper_coord1[3][1])]

        uc2 = [(upper_coord1[0][0] + 4*width + i * wavelength, upper_coord1[0][1]),
               (upper_coord1[1][0] + 4*width + i * wavelength, upper_coord1[1][1]),
               (upper_coord1[2][0] + 4*width + i * wavelength, upper_coord1[2][1]),
               (upper_coord1[3][0] + 4*width + i * wavelength, upper_coord1[3][1])]

        lc1 = [(lower_coord1[0][0] + i*wavelength, lower_coord1[0][1]),
               (lower_coord1[1][0] + i*wavelength, lower_coord1[1][1]),
               (lower_coord1[2][0] + i*wavelength, lower_coord1[2][1]),
               (lower_coord1[3][0] + i*wavelength, lower_coord1[3][1])]

        lc2 = [(lower_coord1[0][0] + 2*width + i * wavelength, lower_coord1[0][1]),
               (lower_coord1[1][0] + 2*width + i * wavelength, lower_coord1[1][1]),
               (lower_coord1[2][0] + 2*width + i * wavelength, lower_coord1[2][1]),
               (lower_coord1[3][0] + 2*width + i * wavelength, lower_coord1[3][1])]

        pad_width1 = uc2[2][0]
        pu_coord1 = uc2[2][1]

        u_rect1 = Polygon(uc1)
        u_rect2 = Polygon(uc2)
        l_rect1 = Polygon(lc1)
        l_rect2 = Polygon(lc2)
        idt.add_to_layer(finger_layer, u_rect1, l_rect1, u_rect2, l_rect2)

    ql = [(ox1, oy), (ox1, oy + pad_height), (4 * width + pad_width1, oy + pad_height), (4 * width + pad_width1, oy)]
    qu = [(ox1, pu_coord1 - finger_overlap), (ox1, pu_coord1 - finger_overlap + pad_height),
          (4 * width + pad_width1 + 50, pu_coord1 - finger_overlap + pad_height),
          (4 * width + pad_width1 + 50, pu_coord1 - finger_overlap)]
    qu1a = [(4 * width + pad_width1 + 50, pu_coord1 - finger_overlap + pad_height),
            (4 * width + pad_width1 + 20, pu_coord1 - finger_overlap + pad_height),
            (4 * width + pad_width1 + 20, oy + pad_height - 75),
            (4 * width + pad_width1 + 50, oy + pad_height - 75)]
    qua = Polygon(qu1a)
    qu1b = [(4 * width + pad_width1 + 20, oy + pad_height - 75),
            (4 * width + pad_width1 + 20, oy + pad_height - 45),
            (ox1 + 100, oy + pad_height - 45), (ox1 + 100, oy + pad_height - 75)]
    qub = Polygon(qu1b)
    qum = qua.union(qub)
    short_lower1 = Polygon(ql)
    short_upper1 = Polygon(qu)
    pla10 = [(ox1, oy + pad_height), (ox1 + 30, oy + pad_height),
             (ox1 + 30, oy + pad_height - 75), (ox1, oy + pad_height - 75)]
    pla0 = Polygon(pla10)
    bl1 = [(ox1 - 20, oy + pad_height - 50), (ox1 + 80, oy + pad_height - 50),
           (ox1 + 80, oy + pad_height - 200), (ox1 - 20, oy + pad_height - 200)]
    plc1 = Polygon(bl1)
    pad_lower1 = pla0.union(plc1)
    bu1 = [(ox1 + 100, oy + pad_height - 50), (ox1 + 200, oy + pad_height - 50),
           (ox1 + 200, oy + pad_height - 200), (ox1 + 100, oy + pad_height - 200)]
    puc1 = Polygon(bu1)
    pad_upper1 = qum.union(puc1)
    idt.add_to_layer(pad_layer, short_lower1, short_upper1, pad_lower1, pad_upper1)

    cross_p = CrossMarker(origin=(ox - 100, oy + pad_height - 250),
                          cross_length=12.5, cross_width=2.5, paddle_length=12.5, paddle_width=2.5)
    cross_q = CrossMarker(origin=(ox - 100, oy + pad_height + 250),
                          cross_length=12.5, cross_width=2.5, paddle_length=12.5, paddle_width=2.5)
    cross_r = CrossMarker(origin=(ox + 400, oy + pad_height - 250),
                          cross_length=12.5, cross_width=2.5, paddle_length=12.5, paddle_width=2.5)
    tag = Text(origin=(ox - 50, oy + pad_height - 250), height=40, text=label,
               alignment='left-center')
    idt.add_to_layer(align_layer, cross_p, cross_q, cross_r, tag)

    return idt


cell = double_finger_idt_wp(fw=1, frequency=1,wavelength=4, periods=48, height=20, surface_velocity=1,
                         offset=1, finger_layer=1, pad_layer=2, align_layer=3, coords=(0,0), label="A1")
cell.save("dfwpIDT.gds")
