def focused_idt(fw, frequency, wavelength, periods, angle, surface_velocity, distance_to_idt,
                finger_layer, pad_layer, align_layer, origin, label):
    # fw should be entered as 0 for f or 1 for w, depending on whether you would like to specify wavelength or frequency
    # if specifying wavelength, enter 1 for frequency and surface velocity (should be in um)
    # origin is center of focus; origin = (x,y)
    # periods is number of wavelengths within the IDT
    # angle is in degrees, should be angle of the IDT (typically 30 degrees)
    # a 2.5 degree offset will be introduced to contact fingers with electrodes
    # this can be altered by changing oa below
    # surface velocity is parameter of material that you are writing on
    # distance to idt is radius from focus to first finger (typically 30um)

    # for now, max period is 46, not sure why this is but I will try to resolve it soon

    from gdshelpers.geometry.chip import Cell
    from shapely.geometry import Polygon
    import numpy as np
    from shapely.geometry import Point, LineString
    from shapely.ops import split
    from gdshelpers.parts.marker import CrossMarker
    from gdshelpers.parts.text import Text

    offset = 2.5*np.pi/180
    overlap = 2.5*np.pi/180
    max_periods = 50
    idt = Cell('idt')
    if fw==0:
        wavelength = (surface_velocity / frequency)*10**6
    width = wavelength / 4
    angle = angle*np.pi/180

    for i in range(periods):
        p = Point(origin)
        circle_lo = p.buffer(distance_to_idt + i*wavelength + width/2)
        circle_li = p.buffer(distance_to_idt + i * wavelength - width / 2)
        la = origin[0] + (distance_to_idt + 2*periods*wavelength) * np.cos(angle/2-offset)
        lb = origin[1]-(distance_to_idt + 2*periods*wavelength) * np.sin(angle/2-offset)
        lc = origin[0]+(distance_to_idt + 2*periods * wavelength) * np.cos(angle/2+offset+overlap)
        ld = origin[1]+(distance_to_idt + 2*periods*wavelength) * np.sin(angle/2+offset+overlap)
        lalb = LineString([origin, (la,lb)])
        lcld = LineString([origin, (lc,ld)])

        circle_uo = p.buffer(distance_to_idt + 2*width + i*wavelength + width / 2)
        circle_ui = p.buffer(distance_to_idt + 2*width + i*wavelength - width / 2)
        ua = origin[0] + (distance_to_idt + 2*periods * wavelength) * np.cos(angle / 2 + offset+overlap)
        ub = origin[1] + -(distance_to_idt + 2*periods * wavelength) * np.sin(angle / 2+offset+overlap)
        uc = origin[0] + (distance_to_idt + 2*periods * wavelength) * np.cos(angle / 2-offset)
        ud = origin[1] + (distance_to_idt + 2*periods * wavelength) * np.sin(angle / 2-offset)
        uaub = LineString([origin, (ua, ub)])
        ucud = LineString([origin, (uc, ud)])

        splitter_l = LineString([*lalb.coords, *lcld.coords[::-1]])
        sector_lo = split(circle_lo, splitter_l)[0]
        sector_li = split(circle_li, splitter_l)[0]
        splitter_u = LineString([*uaub.coords, *ucud.coords[::-1]])
        sector_uo = split(circle_uo, splitter_u)[0]
        sector_ui = split(circle_ui, splitter_u)[0]
        lower_finger = sector_lo.difference(sector_li)
        upper_finger = sector_uo.difference(sector_ui)
        idt.add_to_layer(finger_layer, lower_finger, upper_finger)

    # defining pad region
    circle_p = p.buffer(distance_to_idt + (max_periods+4) * wavelength + width / 2)
    pa = origin[0] + (distance_to_idt + 2 * (max_periods+4) * wavelength) * np.cos(angle / 2)
    pb = origin[1] - (distance_to_idt + 2 * (max_periods+4) * wavelength) * np.sin(angle / 2)
    pc = origin[0] + (distance_to_idt + 2 * (max_periods+4) * wavelength) * np.cos(angle / 2)
    pd = origin[1] + (distance_to_idt + 2 * (max_periods+4) * wavelength) * np.sin(angle / 2)
    papb = LineString([origin, (pa, pb)])
    pcpd = LineString([origin, (pc, pd)])
    splitter_p = LineString([*papb.coords, *pcpd.coords[::-1]])
    sector_p = split(circle_p, splitter_p)[0]
    pad_height = 150 + pd-pb
    pad_length = pa + 100
    block = Polygon([(origin[0]+distance_to_idt - wavelength, origin[1]+pad_height/2),
                     (origin[0]+distance_to_idt - wavelength, origin[1]-pad_height/2),
                     (origin[0]+distance_to_idt - wavelength + pad_length, origin[1]-pad_height/2),
                     (origin[0]+distance_to_idt - wavelength + pad_length, origin[1]+pad_height/2)])
    wg = Polygon([(origin[0]+distance_to_idt + (periods-1)*wavelength, origin[1]+10),
                  (origin[0]+distance_to_idt + (periods-1)*wavelength, origin[1]-10),
                  (origin[0]+distance_to_idt + (periods-1)*wavelength + pad_length, origin[1]-10),
                  (origin[0]+distance_to_idt + (periods-1)*wavelength + pad_length, origin[1]+10)])
    neg_region = sector_p.union(wg)
    pad2 = block.difference(neg_region)
    u_tri = Polygon([(origin[0]+distance_to_idt - wavelength, origin[1]+pad_height/2),
                     (origin[0]+distance_to_idt + 10*wavelength, origin[1]+pad_height/2),
                     (origin[0]+distance_to_idt - wavelength, (origin[1]+distance_to_idt - wavelength)*np.sin(angle/2)/np.cos(angle/2))])
    l_tri = Polygon([(origin[0]+distance_to_idt - wavelength, origin[1]-pad_height/2),
                     (origin[0]+distance_to_idt + 10*wavelength, origin[1]-pad_height/2),
                     (origin[0]+distance_to_idt - wavelength, -(origin[1]+distance_to_idt - wavelength)*np.sin(angle/2)/np.cos(angle/2))])
    pad1 = pad2.difference(u_tri)
    pad = pad1.difference(l_tri)
    idt.add_to_layer(pad_layer, pad)

    cross_p = CrossMarker(origin=(origin[0]+distance_to_idt-wavelength-100, origin[1]+250),
                          cross_length=12.5, cross_width=2.5, paddle_length=12.5, paddle_width=2.5)
    cross_q = CrossMarker(origin=(origin[0] + distance_to_idt - wavelength - 100, origin[1] - 250),
                          cross_length=12.5, cross_width=2.5, paddle_length=12.5, paddle_width=2.5)
    cross_r = CrossMarker(origin=(origin[0] + distance_to_idt - wavelength + 400, origin[1] + 250),
                          cross_length=12.5, cross_width=2.5, paddle_length=12.5, paddle_width=2.5)
    cross_s = CrossMarker(origin=(origin[0] + distance_to_idt - wavelength + 400, origin[1] - 250),
                          cross_length=12.5, cross_width=2.5, paddle_length=12.5, paddle_width=2.5)
    tag = Text(origin=[origin[0]+distance_to_idt-wavelength-60,  origin[1] - 250], height=40, text=label, alignment='left-center')
    idt.add_to_layer(align_layer, cross_p, cross_q, cross_r, cross_s, tag)

    return idt


cell = focused_idt(fw=1, frequency=1, wavelength=4, periods=42, angle=30, surface_velocity=1,
                   distance_to_idt=30, finger_layer=1, pad_layer=2, align_layer=3, origin=(0, 0),label="A1")
cell.save("sIDT.gds")





