from  dataclasses import dataclass, asdict
LED_COUNT = 13

@dataclass
class LEDColors:
    vfr =           (0, 255, 0)
    mvfr =          (0, 0, 255)
    ifr =           (255, 0, 0)
    lifr =          (255, 0, 255)
    nowx =          (80, 80, 80)
    black =         (0, 0, 0)
    lightning =     (255, 255, 0)
    snow  =         (255, 255, 255)
    snow2 =         (100, 100, 100)
    rain  =         (4, 0, 54)
    rain2 =         (0, 0, 255)
    freezing_rain  =(199, 156, 219)
    freezing_rain2 =(152, 0, 199)
    dust_and_ash =  (157, 111, 88)
    fog  =          (80, 80, 80)
    homeport =      (214, 14, 52)

    def dict(self, value):
        try:
            return getattr(self, value)
        except AttributeError:
            return None


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
