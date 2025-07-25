#these are corners or the ROIs for the center and ports of the arena. arbitrary ROIs can be added here
#center and ports also have a correxponding center point.
#the center point is used to calculate the distance to the ports.
ARENA = {'center_roi': ((1245, 585), (1245, 475), (1330, 480), (1330, 580)), 
            'port0_roi': ((400, 500), (400, 600), (500, 600), (500, 500)), 
            'port1_roi': ((400, 0), (400, 100), (500, 100), (500, 0)), 
            'center':(1245, 580),
            'port0':(1245, 580), 
            'port1':(1330, 580),}

ARENA_VERTICES = (
            (100, 310),
            (275, 10),
            (450, 10),
            (625, 10),
            (800, 310),
            (625, 620),
            (450, 620),
            (275, 620)
)
inner_vertices = ((138.24, 310.0),
                  (289.71, 40.29),
                  (450.0, 60.0),
                  (610.29, 40.29),
                  (761.76, 310.0),
                  (610.29, 589.71),
                  (450.0, 570.0),
                  (289.71, 589.71),
                  (289.71, 589.71))


TRIAL_LENGTH = 60  # seconds##

DEVICE = r'F:/social_sniffing'
OUTPUT_EXPANDER = r'F:/social_sniffing/output_expander'