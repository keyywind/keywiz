from typing import Iterator, Union, Tuple, List
from .wizard_utils import WizardUtils
import numpy, json, cv2, os
class WizardSettings:
        
    def __init__(self, configurations_filename : str = "./wizard_config.json") -> None:
        
        self.configurations_filename = configurations_filename
        
        self.configurations = None
    
    def initialize_configurations(self) -> "WizardSettings":
        self.configurations = {
            "book" : {
                "size"  : (100, 100),
                "coord" : (698, 498)
            },
            "pass" : {
                "size"  : (100, 100),
                "coord" : (206, 326)
            },
            "deck" : {
                "size"  : (480, 100),
                "coord" : (163, 250)
            },
            "panel" : {
                "size"  : (430,  70),
                "coord" : ( 26,  16),
                "slot"  : [
                    [ (220, 0) ],
                    [ (194, 0), (247, 0) ],
                    [ (166, 0), (220, 0), (273, 0) ],
                    [ (140, 0), (194, 0), (247, 0), (301, 0) ],
                    [ (113, 0), (166, 0), (220, 0), (273, 0), (327, 0) ],
                    [ ( 86, 0), (141, 0), (193, 0), (247, 0), (301, 0), (354, 0) ],
                    [ ( 58, 0), (113, 0), (167, 0), (220, 0), (274, 0), (327, 0), (381, 0) ]
                ]
            },
            "card" : {
                "size" : (45, 72)    
            },
            "orbs" : {
                "size"  : (128, 128),
                "coord" : (  1, 472)
            },
            "window" : {
                "size"  : (800, 600),
                "coord" : (100, 100)
            },
            "health_panel" : {
                 "size"  : (65, 24),
                 "coord" : (15, 44)
            },
            "mana_panel" : {
                 "size"  : (45, 24),
                 "coord" : (69, 69)
            },
            "digit" : {
                 "size" : (13, 18)   
            },
            "health_digit_panel" : {
                 "size"  : (65, 18),
                 "coord" : ( 0,  3),
                 "slot"  : [
                     [  (26, 0)  ],
                     [  (20, 0), (33, 0)  ],
                     [  (12, 0), (26, 0), (39, 0)  ],
                     [  ( 6, 0), (19, 0), (33, 0), (48, 0)  ]
                 ]
            },
            "mana_digit_panel" : {
                 "size"  : (45, 18),
                 "coord" : ( 0,  3),
                 "slot"  : [
                     [  (15, 0)  ],
                     [  (10, 0), (23, 0)  ],   
                     [  ( 5, 0), (18, 0), (31, 0)  ], 
                 ]
            },
            "runtime" : {
                "heal_rate"      : 0.50,
                "book_rate"      : 0.30,
                "wait_interval"  :    1,
                "full_mana"      :  668,
                "fill_mana"      :   40,
                "max_potions"    :    4,
                "heal_mana"      :    2,
                "attack_mana"    :    4,
                "heal_thresh"    :    2,
                "potion_thresh"  :    0,
                "card_predictor" :    0,
                "full_health"    : 4937,
                "detect_digits"  :    0,
                "fill_patience"  :    3
            }
        }
        return self
    
    def save(self) -> "WizardSettings":
        
        if (self.configurations is None):
            raise Exception("Configurations has yet been set")
            
        with open(self.configurations_filename, "w") as write_file:
            write_file.write(json.dumps(self.configurations, indent = 4))
            
        return self
            
    def load(self) -> bool:
        
        if (os.path.isfile(self.configurations_filename)):
            with open(self.configurations_filename, 'r') as read_file:
                self.configurations = json.loads(read_file.read())
            return True
        return False
    
    def center_target_mask(self, target_mask : numpy.ndarray, x : int, y : int, shape : Union[ numpy.ndarray, Tuple[ int ] ]) -> numpy.ndarray:
        
        # centroids of smaller mask : FORMAT[ (x, y) ]
        center_coordinates = (target_mask.shape[1] // 2, target_mask.shape[0] // 2)
        
        # upper left corner : FORMAT[ (x, y) ]
        upper_left = (
            (x - center_coordinates[0]), 
            (y - center_coordinates[1])
        )
        
        # lower right corner : FORMAT[ (x, y) ] ( exclusive )
        lower_right = (
            min(shape[1], upper_left[0] + target_mask.shape[1]), 
            min(shape[0], upper_left[1] + target_mask.shape[0])
        )
        
        upper_left = (
            max(0, upper_left[0]), 
            max(0, upper_left[1])
        )
        
        # empty (all zero) mask
        result_mask = numpy.zeros(shape = shape, dtype = numpy.uint8)
        
        if ((numpy.prod(target_mask.shape[:2])) == ((lower_right[0] - upper_left[0]) * (lower_right[1] - upper_left[1]))):
            
            result_mask[ upper_left[1] : lower_right[1], upper_left[0] : lower_right[0] ] = target_mask
            
        return result_mask
    
    @staticmethod
    def get_colored_mask(channel : Union[ numpy.ndarray, List[ int ], Tuple[ int ] ], height : int, width : int) -> numpy.ndarray:
        
        return numpy.uint8([ channel ]).repeat(width, axis = 0).reshape((1, width, channel.__len__())).repeat(height, axis = 0)
    
    def configure_window(self, window_name : str) -> bool:
        
        resize_ratio = 0.5
        
        def read_screenshot() -> Iterator[ numpy.ndarray ]:
            
            while True:
                yield WizardUtils.take_screenshot(resize_ratio, cv2.COLOR_RGB2BGR)
                
        def mouse_callback(event : int, x : int, y : int, * args, ** kwargs) -> None:
            
            nonlocal cur_x, cur_y, should_save 
            if (event == cv2.EVENT_LBUTTONDOWN):
                cur_x, cur_y, should_save = x, y, True
            elif not (should_save):
                if  (event == cv2.EVENT_LBUTTONUP):
                    pass
                elif (event == cv2.EVENT_MOUSEMOVE):
                    cur_x, cur_y = x, y
        
        cur_x, cur_y, should_save = -1, -1, False
        
        target_mask = numpy.zeros(shape = (*self.configurations["window"]["size"][::-1], 3), dtype = numpy.uint8)
        target_mask = cv2.rectangle(target_mask, (0, 0), 
            tuple((i - 1) for i in self.configurations["window"]["size"]), (255, 255, 255), 1)
        
        target_mask = cv2.resize(target_mask, None, None, fx = resize_ratio, fy = resize_ratio)
        
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, mouse_callback)
        
        for frame in read_screenshot():
            
            mouse_mask   = self.center_target_mask(target_mask, cur_x, cur_y, frame.shape)
            colored_mask = self.get_colored_mask([ 0, 0, 255 ], *frame.shape[:2])
            
            display_frame = numpy.where((mouse_mask), colored_mask, frame)
            
            cv2.imshow(window_name, display_frame)
            
            wait_key = cv2.waitKey(1)
            
            if (wait_key == 27):
                break
            elif (wait_key == ord('r')):
                should_save = False
        
        cv2.destroyWindow(window_name)
        
        if (should_save):
            self.configurations["window"]["coord"] = (
                int((cur_x - target_mask.shape[1] // 2) / resize_ratio), 
                int((cur_y - target_mask.shape[0] // 2) / resize_ratio)
            )
            
        return should_save
    
    def configure_book(self, window_name : str) -> bool:
        return self.__configure_basic(window_name, "book")
    
    def configure_pass(self, window_name : str) -> bool:
        return self.__configure_basic(window_name, "pass")
    
    """
    def configure_orbss(self, window_name : str) -> bool:
        return self.__configure_basic(window_name, "orbs")
    """
    
    def __configure_basic(self, window_name : str, target_key : str) -> bool:
        
        resize_ratio = 1
        
        def read_screenshot() -> Iterator[ numpy.ndarray ]:
            
            while True:
                yield WizardUtils.take_screenshot(resize_ratio, cv2.COLOR_RGB2BGR)
                
        def mouse_callback(event : int, x : int, y : int, * args, ** kwargs) -> None:
            
            nonlocal cur_x, cur_y, should_save 
            if (event == cv2.EVENT_LBUTTONDOWN):
                cur_x, cur_y, should_save = x, y, True
            elif not (should_save):
                if  (event == cv2.EVENT_LBUTTONUP):
                    pass
                elif (event == cv2.EVENT_MOUSEMOVE):
                    cur_x, cur_y = x, y
                    
        window_b = (window_x, window_y, window_w, window_h) \
            = WizardUtils.fetch_relative_bounding_box(self.configurations, "window")
                         
        target_b = (target_x, target_y, target_w, target_h) \
            = WizardUtils.fetch_relative_bounding_box(self.configurations, target_key)
        
        cur_x, cur_y, should_save = -1, -1, False
        
        target_mask = numpy.zeros(shape = (target_h, target_w, 3), dtype = numpy.uint8)
        
        target_mask = cv2.rectangle(target_mask, (0, 0), 
            tuple((i - 1) for i in target_b[ 2:4 ]), (255, 255, 255), 1)
        
        target_mask = cv2.resize(target_mask, None, None, fx = resize_ratio, fy = resize_ratio)
        
        cv2.namedWindow(window_name)
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        for frame in read_screenshot():
            
            frame = WizardUtils.crop_image(frame, window_b[ 0:2 ], window_b[ 2:4 ])
            
            mouse_mask   = self.center_target_mask(target_mask, cur_x, cur_y, frame.shape)
            
            colored_mask = self.get_colored_mask([ 0, 0, 255 ], *frame.shape[:2])
            
            display_frame = numpy.where((mouse_mask), colored_mask, frame)
            
            cv2.imshow(window_name, display_frame)
            
            wait_key = cv2.waitKey(1)
            
            if (wait_key == 27):
                break
            elif (wait_key == ord('r')):
                should_save = False
        
        cv2.destroyWindow(window_name)
        
        if (should_save):
            self.configurations[target_key]["coord"] = (
                int((cur_x - target_mask.shape[1] // 2) / resize_ratio), 
                int((cur_y - target_mask.shape[0] // 2) / resize_ratio)
            )
            
        return should_save
        
    def configure_deck(self, window_name : str) -> bool:
        
        resize_ratio = 1
        
        def read_screenshot() -> Iterator[ numpy.ndarray ]:
            
            while True:
                yield WizardUtils.take_screenshot(resize_ratio, cv2.COLOR_RGB2BGR)
                
        def mouse_callback(event : int, x : int, y : int, * args, ** kwargs) -> None:
            
            nonlocal cur_x, cur_y, should_save 
            if (event == cv2.EVENT_LBUTTONDOWN):
                cur_x, cur_y, should_save = x, y, True
            elif not (should_save):
                if  (event == cv2.EVENT_LBUTTONUP):
                    pass
                elif (event == cv2.EVENT_MOUSEMOVE):
                    cur_x, cur_y = x, y
                    
        window_b = (window_x, window_y, window_w, window_h) \
            = WizardUtils.fetch_relative_bounding_box(self.configurations, "window")
        
        cur_x, cur_y, should_save = -1, -1, False
        
        deck_b = (deck_x, deck_y, deck_w, deck_h) = WizardUtils.fetch_relative_bounding_box(self.configurations, "deck")
        
        target_mask = numpy.zeros(shape = (deck_h, deck_w, 3), dtype = numpy.uint8)
        
        panel_b = (panel_x, panel_y, panel_w, panel_h) = WizardUtils.fetch_relative_bounding_box(self.configurations, "panel")
                
        card_w, card_h = self.configurations["card"]["size"]
        
        for i in range(7):
            
            card_x, card_y = (
                panel_x + self.configurations["panel"]["slot"][6][i][0],
                panel_y + self.configurations["panel"]["slot"][6][i][1]
            )
            
            target_mask = cv2.rectangle(target_mask, (card_x, card_y), (card_x + card_w, card_y + card_h), (255, 255, 255), 1)
        
        target_mask = cv2.rectangle(target_mask, (deck_x, deck_y), (deck_x + deck_w, deck_y + deck_h), (255, 255, 255), 2)
        
        target_mask = cv2.resize(target_mask, None, None, fx = resize_ratio, fy = resize_ratio)
        
        cv2.namedWindow(window_name)
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        for frame in read_screenshot():
            
            frame = WizardUtils.crop_image(frame, window_b[ 0:2 ], window_b[ 2:4 ])
            
            mouse_mask   = self.center_target_mask(target_mask, cur_x, cur_y, frame.shape)
            
            colored_mask = self.get_colored_mask([ 0, 0, 255 ], *frame.shape[:2])
            
            display_frame = numpy.where((mouse_mask), colored_mask, frame)
            
            cv2.imshow(window_name, display_frame)
            
            wait_key = cv2.waitKey(1)
            
            if (wait_key == 27):
                break
            elif (wait_key == ord('r')):
                should_save = False
        
        cv2.destroyWindow(window_name)
        
        if (should_save):
            self.configurations["deck"]["coord"] = (
                int((cur_x - target_mask.shape[1] // 2) / resize_ratio), 
                int((cur_y - target_mask.shape[0] // 2) / resize_ratio)
            )
            
        return should_save
    
    def configure_orbs(self, window_name : str) -> bool:
        
        resize_ratio = 1
        
        def read_screenshot() -> Iterator[ numpy.ndarray ]:
            
            while True:
                yield WizardUtils.take_screenshot(resize_ratio, cv2.COLOR_RGB2BGR)
                
        def mouse_callback(event : int, x : int, y : int, * args, ** kwargs) -> None:
            
            nonlocal cur_x, cur_y, should_save 
            if (event == cv2.EVENT_LBUTTONDOWN):
                cur_x, cur_y, should_save = x, y, True
            elif not (should_save):
                if  (event == cv2.EVENT_LBUTTONUP):
                    pass
                elif (event == cv2.EVENT_MOUSEMOVE):
                    cur_x, cur_y = x, y
                    
        window_b = (window_x, window_y, window_w, window_h) \
            = WizardUtils.fetch_relative_bounding_box(self.configurations, "window")
        
        cur_x, cur_y, should_save = -1, -1, False
        
        orbs_b = (orbs_x, orbs_y, orbs_w, orbs_h) = WizardUtils.fetch_relative_bounding_box(self.configurations, "orbs")
        
        target_mask = numpy.zeros(shape = (orbs_h, orbs_w, 3), dtype = numpy.uint8)
        
        health_panel_b = (health_panel_x, health_panel_y, health_panel_w, health_panel_h) = WizardUtils.fetch_relative_bounding_box(self.configurations, "health_panel")
        mana_panel_b   = (  mana_panel_x,   mana_panel_y,   mana_panel_w,   mana_panel_h) = WizardUtils.fetch_relative_bounding_box(self.configurations,   "mana_panel")
        
        health_digit_panel_b = (health_digit_panel_x, health_digit_panel_y, health_digit_panel_w, health_digit_panel_h) \
            = WizardUtils.fetch_relative_bounding_box(self.configurations, "health_digit_panel")
            
        mana_digit_panel_b   = (mana_digit_panel_x, mana_digit_panel_y, mana_digit_panel_w, mana_digit_panel_h) \
            = WizardUtils.fetch_relative_bounding_box(self.configurations, "mana_digit_panel")
        
        digit_w, digit_h = self.configurations["digit"]["size"]
        
        for i in range(4):
            
            digit_x, digit_y = (
                health_panel_x + health_digit_panel_x + self.configurations["health_digit_panel"]["slot"][3][i][0],
                health_panel_y + health_digit_panel_y + self.configurations["health_digit_panel"]["slot"][3][i][1]
            )
            
            target_mask = cv2.rectangle(target_mask, (digit_x, digit_y), (digit_x + digit_w, digit_y + digit_h), (255, 255, 255), 1)
            
        for i in range(3):
            
            digit_x, digit_y = (
                mana_panel_x + mana_digit_panel_x + self.configurations["mana_digit_panel"]["slot"][2][i][0],
                mana_panel_y + mana_digit_panel_y + self.configurations["mana_digit_panel"]["slot"][2][i][1]
            )
            
            target_mask = cv2.rectangle(target_mask, (digit_x, digit_y), (digit_x + digit_w, digit_y + digit_h), (255, 255, 255), 1)
        
        target_mask = cv2.rectangle(target_mask, (orbs_x, orbs_y), (orbs_x + orbs_w, orbs_y + orbs_h), (255, 255, 255), 2)
        
        target_mask = cv2.resize(target_mask, None, None, fx = resize_ratio, fy = resize_ratio)
        
        cv2.namedWindow(window_name)
        
        cv2.setMouseCallback(window_name, mouse_callback)
        
        for frame in read_screenshot():
            
            frame = WizardUtils.crop_image(frame, window_b[ 0:2 ], window_b[ 2:4 ])
            
            mouse_mask   = self.center_target_mask(target_mask, cur_x, cur_y, frame.shape)
            
            colored_mask = self.get_colored_mask([ 0, 0, 255 ], *frame.shape[:2])
            
            display_frame = numpy.where((mouse_mask), colored_mask, frame)
            
            cv2.imshow(window_name, display_frame)
            
            wait_key = cv2.waitKey(1)
            
            if (wait_key == 27):
                break
            elif (wait_key == ord('r')):
                should_save = False
        
        cv2.destroyWindow(window_name)
        
        if (should_save):
            self.configurations["orbs"]["coord"] = (
                int((cur_x - target_mask.shape[1] // 2) / resize_ratio), 
                int((cur_y - target_mask.shape[0] // 2) / resize_ratio)
            )
            
        return should_save    
    
    def generate_mask(self, frame_shape         : Tuple[ int        ]    , 
                          card_quantity         :        int          = 7, 
                          resize_ratio          : Union[ int, float ] = 1,
                          health_digit_quantity :        int          = 4,
                          mana_digit_quantity   :        int          = 3) -> numpy.ndarray:
        
        """
            frame_shape : FORMAT[ (rows, cols, channels) ]
        """
        
        target_mask = numpy.zeros(shape = frame_shape, dtype = numpy.uint8)
        
        window_b = (window_x, window_y, window_w, window_h) \
            = WizardUtils.fetch_absolute_bounding_box(self.configurations, "window")
            
        deck_b = (deck_x, deck_y, deck_w, deck_h) \
            = WizardUtils.fetch_absolute_bounding_box(self.configurations, "deck")
            
        book_b = (book_x, book_y, book_w, book_h) \
            = WizardUtils.fetch_absolute_bounding_box(self.configurations, "book")
            
        pass_b = (pass_x, pass_y, pass_w, pass_h) \
            = WizardUtils.fetch_absolute_bounding_box(self.configurations, "pass")
            
        orbs_b = (orbs_x, orbs_y, orbs_w, orbs_h) \
            = WizardUtils.fetch_absolute_bounding_box(self.configurations, "orbs")
            
        for box in [  window_b, deck_b, book_b, pass_b, orbs_b  ]:
            
            (x, y, w, h) = box
            target_mask = cv2.rectangle(target_mask, (x, y), (x + w, y + h), (255, 255, 255), 2)
        
        cards_b = WizardUtils.fetch_card_coordinates(self.configurations)
        
        for box in range(card_quantity):
            
            (x, y, w, h) = cards_b[card_quantity - 1][box]
            target_mask = cv2.rectangle(target_mask, (x, y), (x + w, y + h), (255, 255, 255), 2)
            
        (health_digits_b, mana_digits_b) = WizardUtils.fetch_number_coordinates(self.configurations)
        
        for box in range(health_digit_quantity):
            
            (x, y, w, h) = health_digits_b[health_digit_quantity - 1][box]
            target_mask = cv2.rectangle(target_mask, (x, y), (x + w, y + h), (255, 255, 255), 1)
            
        for box in range(mana_digit_quantity):
            
            (x, y, w, h) = mana_digits_b[mana_digit_quantity - 1][box]
            target_mask = cv2.rectangle(target_mask, (x, y), (x + w, y + h), (255, 255, 255), 1)
            
        if (resize_ratio != 1):
            
            target_mask = cv2.resize(target_mask, None, None, fx = resize_ratio, fy = resize_ratio)
            
        return target_mask   
    
    def display_configuration(self, window_name : str) -> None:
        
        resize_ratio = 0.5
        
        def read_screenshot() -> Iterator[ numpy.ndarray ]:
            
            while True:
                yield WizardUtils.take_screenshot(resize_ratio = 1, color_mode = cv2.COLOR_RGB2BGR)
                        
        cv2.namedWindow(window_name)
        
        target_mask = self.generate_mask(next(read_screenshot()).shape, card_quantity = 7, resize_ratio = 1)
        
        for frame in read_screenshot():
            
            colored_mask = self.get_colored_mask([ 0, 0, 255 ], *frame.shape[:2])
            
            display_frame = numpy.where((target_mask), colored_mask, frame)
            
            display_frame = cv2.resize(display_frame, None, None, fx = resize_ratio, fy = resize_ratio)
            
            cv2.imshow(window_name, display_frame)
            
            if (cv2.waitKey(1) == 27):
                break
            
        cv2.destroyWindow(window_name)
        
    def settings_ready(self) -> bool:
        return (self.configurations is not None)
        
    def configure(self) -> None:
        
        while True:
            print("--options")
            print("[ S ] Show")
            print("[ A ] All")
            print("[ W ] Window")
            print("[ B ] Book")
            print("[ P ] Pass")
            print("[ D ] Deck")
            print("[ O ] Orbs")
            print("[ R ] Return")
            print("")
            user_choice = input("> ").lower()
            if (user_choice.startswith('s')):
                self.display_configuration("KeyWizard - Configuration Result")
            elif (user_choice.startswith('a')):
                self.full_configure()
            elif (user_choice.startswith('w')):
                self.configure_window("KeyWizard - Configure Window")
            elif (user_choice.startswith('b')):
                self.configure_book("KeyWizard - Configure Spell Book")
            elif (user_choice.startswith('p')):
                self.configure_pass("KeyWizard - Configure Pass Button")
            elif (user_choice.startswith('o')):
                self.configure_orbs("KeyWizard - Configure Health & Mana Orbs")
            elif (user_choice.startswith('d')):
                self.configure_deck("KeyWizard - Configure Spell Deck")
            elif (user_choice.startswith('r')):
                return
        
    def full_configure(self) -> None:
        
        window_name = "KeyWizard - Full Configuration"
        self.configure_window(window_name)
        self.configure_book(window_name)
        self.configure_pass(window_name)
        self.configure_orbs(window_name)
        self.configure_deck(window_name)
        self.display_configuration(window_name)
    
if (__name__ == "__main__"):
    wizard_settings = WizardSettings().initialize_configurations().save()
    wizard_settings.load()
    wizard_settings.full_configure()