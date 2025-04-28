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
        d = asdict(self)
        for k,v in d.items():
            yield k,v


color = LEDColors()


# Conditions as defined by
conditions = {
    'lightning': ["TS", "TSRA", "TSGR", "+TSRA", "TSRG", "FC", "SQ", "VCTS", "VCTSRA", "VCTSDZ", "LTG"],
    'snow': ["BLSN", "DRSN", "-RASN", "RASN", "+RASN", "-SN", "SN", "+SN", "SG", "IC", "PE", "PL", "-SHRASN", "SHRASN",
             "+SHRASN", "-SHSN", "SHSN", "+SHSN"],
    'rain': ["-DZ", "DZ", "+DZ", "-DZRA", "DZRA", "-RA", "RA", "+RA", "-SHRA", "SHRA", "+SHRA", "VIRGA", "VCSH", "UP"],
    'freezing_rain': ["-FZDZ", "FZDZ", "+FZDZ", "-FZRA", "FZRA", "+FZRA"],
    'dust_and_ash': ["DU", "SA", "HZ", "FU", "VA", "BLDU", "BLSA", "PO", "VCSS", "SS", "+SS"],
    'fog': ["BR", "MIFG", "VCFG", "BCFG", "PRFG", "FG", "FZFG"]
}

class Configuration():
    updated = False

    def __init__(self):
        super().__init__()
        self.autorun = 1
        self.LED_COUNT = 183
        self.legend = 1
        self.max_wind_speed = 15
        self.update_interval = 15
        self.metar_age = 2.5
        self.data_sw0 = 1
        self.time_sw0 = 1
        self.usetimer = 1
        self.offhour = 21
        self.offminutes = 30
        self.onhour = 6
        self.onminutes = 30
        self.tempsleepon = 5
        self.sleepmsg = 1
        self.displayused = 1
        self.oledused = 1
        self.lcddisplay = 0
        self.numofdisplays = 8
        self.loglevel = 1
        self.hiwindblink = 1
        self.lghtnflash = 1
        self.rainshow = 1
        self.frrainshow = 1
        self.snowshow = 1
        self.dustsandashshow = 1
        self.fogshow = 1
        self.homeport = 1
        self.homeport_pin = 170
        self.homeport_display = 0
        self.dim_value = 75
        self.rgb_grb = 1
        self.rev_rgb_grb = []
        self.dimmed_value = 30
        self.bright_value = 255
        self.colors = dict(
            vfr = color.vfr,
            mvfr = color.mvfr,
            ifr = color.ifr,
            lifr = color.ifr,
            nowx = color.nowx,
            black = color.black,
            lghtn = color.lightning,
            snow1 = color.snow,
            snow2 = color.snow2,
            rain1 = color.rain,
            rain2 = color.rain2,
            frrain1 = color.freezing_rain,
            frrain2 = color.freezing_rain2,
            dustsandash1 = color.dust_and_ash,
            dustsandash2 = color.dust_and_ash,
            fog1 = color.fog,
            fog2 = color.fog,
            homeport = color.homeport,
            homeport_colors = [(55,55,55), (200,200,200), (50,50,50), (150,150,150), (25,25,25), (0,0,0)]
        )
        self.legend_hiwinds = 1
        self.legend_lghtn = 1
        self.legend_snow = 0
        self.legend_rain = 0
        self.legend_frrain = 0
        self.legend_dustsandash = 0
        self.legend_fog = 0
        self.leg_pin_vfr = 7
        self.leg_pin_mvfr = 9
        self.leg_pin_ifr = 8
        self.leg_pin_lifr = 4
        self.leg_pin_nowx = 11
        self.leg_pin_hiwinds = 12
        self.leg_pin_lghtn = 10
        self.leg_pin_snow = 0
        self.leg_pin_rain = 0
        self.leg_pin_frrain = 0
        self.leg_pin_dustsandash = 0
        self.leg_pin_fog = 0
        self.num2display = 10
        self.exclusive_flag = 0
        self.exclusive_list = ['KFLG', 'KPRC', 'KIGM', 'KONT',  'KPHX', 'KTUS']
        self.abovekts = 0
        self.lcdpause = .3
        self.rotyesno = 0
        self.oledposorder = 0
        self.oledpause = 1.7
        self.fontsize = 24
        self.offset = 3
        self.wind_numorarrow = 1
        self.boldhiap = 1
        self.blankscr = 1
        self.border = 0
        self.dimswitch = 0
        self.dimmin = 50
        self.dimmax = 255
        self.invert = 0
        self.toginv = 0
        self.scrolldis = 0
        self.usewelcome = 1
        self.welcome = "Welcome to Live Sectional V4"
        self.displaytime = 1
        self.displayIP = 1
        self.data_sw1 = 0
        self.time_sw1 = 1
        self.data_sw2 = 0
        self.time_sw2 = 2
        self.data_sw3 = 0
        self.time_sw3 = 3
        self.data_sw4 = 2
        self.time_sw4 = 1
        self.data_sw5 = 2
        self.time_sw5 = 2
        self.data_sw6 = 2
        self.time_sw6 = 3
        self.data_sw7 = 3
        self.time_sw7 = 1
        self.data_sw8 = None
        self.time_sw8 = 1
        self.data_sw9 = None
        self.time_sw9 = 1
        self.data_sw10 = None
        self.time_sw10 = 1
        self.data_sw11 = None
        self.time_sw11 = 1
        self.hour_to_display = 1
        self.prob = 50
        self.bin_grad = 1
        self.use_homeap = 1
        self.fade_yesno = 1
        self.fade_delay = .005
        self.usewipes = 1
        self.rand = 1
        self.wait = .002
        self.num_rainbow = 1
        self.num_fade = 0
        self.fade_color1 = (0, 255, 0)
        self.num_allsame = 0
        self.allsame_color1 = (20, 5, 207)
        self.allsame_color2 = (0, 0, 0)
        self.num_shuffle = 0
        self.shuffle_color1 = (250, 0, 242)
        self.shuffle_color2 = (225, 255, 0)
        self.num_radar = 3
        self.radar_color1 = (75, 73, 73)
        self.radar_color2 = (46, 43, 253)
        self.num_circle = 0
        self.circle_color1 = (249, 1, 1)
        self.circle_color2 = (0, 0, 0)
        self.num_square = 0
        self.square_color1 = (223, 100, 64)
        self.square_color2 = (0, 0, 0)
        self.num_updn = 0
        self.updn_color1 = (255, 0, 0)
        self.updn_color2 = (0, 0, 0)
        self.num_morse = 0
        self.morse_msg = "LiveSectional"
        self.morse_color1 = (0, 0, 255)
        self.morse_color2 = (0, 0, 0)
        self.num_rabbit = 0
        self.rabbit_color1 = (255, 0, 0)
        self.rabbit_color2 = (0, 50, 250)
        self.num_checker = 0
        self.checker_color1 = (0, 255, 0)
        self.checker_color2 = (0, 0, 0)



