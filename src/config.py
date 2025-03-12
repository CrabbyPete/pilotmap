from  dataclasses import dataclass, asdict, fields

@dataclass
class LEDColors:
    vfr: tuple           = (0, 255, 0)
    mvfr: tuple          = (0, 0, 255)
    ifr: tuple           = (255, 0, 0)
    lifr: tuple          = (255, 0, 255)
    nowx: tuple          = (80, 80, 80)
    black: tuple         = (0, 0, 0)
    lightning: tuple     = (255, 255, 0)
    snow: tuple          = (255, 255, 255)
    snow2: tuple         = (100, 100, 100)
    rain: tuple          = (4, 0, 54)
    rain2: tuple         = (0, 0, 255)
    freezing_rain: tuple = (199, 156, 219)
    freezing_rain2: tuple = (152, 0, 199)
    dust_and_ash: tuple   = (157, 111, 88)
    fog: tuple           = (80, 80, 80)
    homeport: tuple      = (214, 14, 52)

    def dict(self, value):
        try:
            return getattr(self, value)
        except AttributeError:
            return None

    def __iter__(self):
        for k,v in asdict(self).items():
            yield k,v

color = LEDColors()


# Conditions as defined by
conditions = {
    'lightning': ["TS", "TSRA", "TSGR", "+TSRA", "TSRG", "FC", "SQ", "VCTS", "VCTSRA", "VCTSDZ", "LTG"],
    'snow': ["BLSN", "DRSN", "-RASN", "RASN", "+RASN", "-SN", "SN", "+SN", "SG", "IC", "PE", "PL", "-SHRASN", "SHRASN",
             "+SHRASN", "-SHSN", "SHSN", "+SHSN"],
    'rain': ["-DZ", "DZ", "+DZ", "-DZRA", "DZRA", "-RA", "RA", "+RA", "-SHRA", "SHRA", "+SHRA", "VIRGA", "VCSH"],
    'freezing_rain': ["-FZDZ", "FZDZ", "+FZDZ", "-FZRA", "FZRA", "+FZRA"],
    'dust_and_ash': ["DU", "SA", "HZ", "FU", "VA", "BLDU", "BLSA", "PO", "VCSS", "SS", "+SS"],
    'fog': ["BR", "MIFG", "VCFG", "BCFG", "PRFG", "FG", "FZFG"]
}
