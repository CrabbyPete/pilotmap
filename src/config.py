from  dataclasses import dataclass

@dataclass
class Colors:
    vfr =           (0, 255, 0)
    mvfr =          (0, 0, 255)
    ifr =           (255, 0, 0)
    lifr =          (255, 0, 255)
    nowx =          (80, 80, 80)
    black =         (0, 0, 0)
    lghtn =         (255, 255, 0)
    snow1 =         (255, 255, 255)
    snow2 =         (100, 100, 100)
    rain1 =         (4, 0, 54)
    rain2 =         (0, 0, 255)
    frrain1 =       (199, 156, 219)
    frrain2 =       (152, 0, 199)
    dustsandash =   (157, 111, 88)
    fog1 =          (80, 80, 80)
    homeport =      (214, 14, 52)

color = Colors