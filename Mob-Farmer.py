import pynput, numpy, sys, cv2, os

if (os.getcwd() != os.path.dirname(__file__)):
    if (os.path.dirname(__file__).replace(" ", "").__len__()):
        os.chdir(os.path.dirname(__file__)) 
    
from typing import Callable, Iterator, Tuple, Union, Type, List

from keywizardUtilities.mob_utils.wizard_settings import WizardSettings, WizardUtils
from keywizardUtilities.mob_utils.wizard_utils2 import ModelManager
from keywizardUtilities.mob_utils.dungeon_utils import HalfangUtils
from pyautogui import screenshot as py_screenshot

from keyio.windowutils import WindowUtils
from keyio.keyutils import KeyUtils  

class WizardPlayer:
    
    instance_list      = []
    
    idle_function_list = []
    
    window_controller  = WindowUtils()
    
    SELECT_WINDOW      = False 
    
    @classmethod
    def run_instances(class_) -> Type[ "WizardPlayer" ]:
        
        (unpaused, nonterminal) = (True, True)
        
        def fetch_instance() -> Iterator[ "WizardPlayer" ]:
            
            index = 0
            
            while True:
                
                yield (index, class_.instance_list[ index ], class_.idle_function_list[ index ])
                
                if (unpaused):
                    
                    index = (index + 1) % class_.instance_list.__len__()
                  
        def keyboard_on_press(key : Union[ pynput.keyboard.Key, pynput.keyboard.KeyCode ]) -> None:
            
            nonlocal unpaused, nonterminal
            
            if (key == pynput.keyboard.Key.f9):
                unpaused = not unpaused 
                
            elif (key == pynput.keyboard.Key.f10):
                (unpaused, nonterminal) = (
                    False, False    
                )
                
        WizardUtils.countdown(countdown_time = 3)
        
        keyboard_listener = pynput.keyboard.Listener(on_press = keyboard_on_press)
        
        keyboard_listener.start()
                    
        for index, instance, idle_function in fetch_instance():
            
            if not (nonterminal):
                
                break
            
            if not (unpaused):
                
                class_.print_status("Paused", 
                    instance.num_potions, instance.cur_health, instance.cur_mana, instance.health_score, instance.mana_score, instance.potion_patience
                )
                
            else:
                
                instance.execute_once(idle_function, verbose = True)
                
            WizardUtils.sleep(1)
                
        print("\nTerminated")
                
        keyboard_listener.stop()
        
        return class_
                
    @classmethod 
    def initialize_instances(class_, instance_list : List[  "WizardSettings"  ], 
                                idle_function_list : List[  Callable          ] = []) -> Type[ "WizardPlayer" ]:
        
        for instance in instance_list:
            class_.instance_list.append(WizardPlayer(instance))
            class_.idle_function_list.append(None)
            
        for index, idle_function in enumerate(idle_function_list):
            class_.idle_function_list[ index ] = idle_function
            
        return class_
    
    @classmethod
    def initialize(class_, book_model_name : str, pass_model_name : str, card_model_name : str,
                           deck_model_name : str, orbH_model_name : str, orbM_model_name : str,
                           digH_model_name : str, digM_model_name : str, digi_model_name : str) -> Type[ "WizardPlayer" ]:
        
        ModelManager.initialize(
            book_model_name, pass_model_name, card_model_name, 
            deck_model_name, orbH_model_name, orbM_model_name,
            digH_model_name, digM_model_name, digi_model_name
        )
        return class_
    
    @staticmethod
    def screenshot() -> numpy.ndarray:
        return cv2.cvtColor(numpy.uint8(py_screenshot()), cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def __two_points_center(point_1 : Tuple[ int ], point_2 : Tuple[ int ]) -> Tuple[ int ]:
        return (
            (point_1[0] + point_2[0]) // 2,
            (point_1[1] + point_2[1]) // 2
        )
    
    
    
    def __init__(self, player_settings : "WizardSettings") -> None:
        
        self.player_settings = player_settings
        
        if (self.SELECT_WINDOW):
        
            print("")
            
            sys.stdout.write("\r[ Press F8 to confirm selected window ]")
            sys.stdout.flush()
            
            key_controller = KeyUtils()
            
            keep_running   = True
            
            @key_controller.monitor(KeyUtils.Key.KEY_F8)
            def monitor_F8(key_code : int, key_pressed : bool) -> None:
                nonlocal keep_running 
                if (key_pressed):
                    (x, y, *_) = self.window_controller.get_foreground_window()
                    y += 30
                    self.player_settings.configurations["window"]["coord"] = [ x, y ]
                    keep_running = False
                    
            key_controller.initialize_monitors()
            
            key_controller.start_thread()
            
            while (keep_running):
                pass 
            
            key_controller.stop_thread() 
            
            sys.stdout.write("\r[ Window Selected ]                     ")
            sys.stdout.flush()
            
            print("\n")
        
        (self.health_score, self.mana_score, self.should_idle, self.num_potions, self.cur_mana, self.cur_health) = (
            0, 
            0,
            True,
            self.player_settings.configurations["runtime"]["max_potions"], 
            self.player_settings.configurations["runtime"]["full_mana"],
            self.player_settings.configurations["runtime"]["full_health"]
        )
        
        (self.book_bounding_box, self.pass_bounding_box, self.deck_bounding_box, self.orbs_bounding_box, self.card_bounding_box) = (
            WizardUtils.fetch_absolute_bounding_box(self.player_settings.configurations, "book"), 
            WizardUtils.fetch_absolute_bounding_box(self.player_settings.configurations, "pass"), 
            WizardUtils.fetch_absolute_bounding_box(self.player_settings.configurations, "deck"),
            WizardUtils.fetch_absolute_bounding_box(self.player_settings.configurations, "orbs"),
            WizardUtils.fetch_card_coordinates(self.player_settings.configurations)
        )
        
        (self.book_point, self.pass_point) = (
            WizardUtils.bounding_box_centroid(self.book_bounding_box), 
            WizardUtils.bounding_box_centroid(self.pass_bounding_box)
        )
        
        self.idle_point = self.__two_points_center(self.book_point, self.pass_point)
        
        self.red_frame = self.player_settings.get_colored_mask([ 0, 0, 255 ], 
            *WizardUtils.take_screenshot(resize_ratio = 1.0, color_mode = cv2.COLOR_RGB2BGR).shape[ 0:2 ]
        )
        
        self.window_bounding_box = WizardUtils.fetch_absolute_bounding_box(
            self.player_settings.configurations, "window"    
        )
        
        (self.digH_bounding_box, self.digM_bounding_box) = WizardUtils.fetch_number_coordinates(self.player_settings.configurations)
        
        (self.panelH_bounding_box, self.panelM_bounding_box) = (
            WizardUtils.fetch_absolute_bounding_box(self.player_settings.configurations, "health_panel"),
            WizardUtils.fetch_absolute_bounding_box(self.player_settings.configurations, "mana_panel")   
        )
        
        self.detect_digits = self.player_settings.configurations["runtime"]["detect_digits"]
        
        self.potion_patience = self.player_settings.configurations["runtime"]["fill_patience"]
        
        self.window_name = "Keywizard"
        
        self.display_quantity = 7
        
        self.show_window = False
    
    def drink_potion(self) -> "WizardPlayer":
        
        if (self.should_idle):
                
            # mana score predicted by model indicates low mana
            low_mana_1 = (self.mana_score   <= self.player_settings.configurations["runtime"]["potion_thresh"])
            
            # mana score tracked via counting indicates low mana
            low_mana_2 = (self.cur_mana     <= self.player_settings.configurations["runtime"]["fill_mana"])
            
            # health score predicted by model indicates low health
            low_health = (self.health_score <= 0)
            
            if (((low_mana_1) and (low_mana_2)) or (low_health)):
                
                self.potion_patience -= 1
                
            elif (self.potion_patience != self.player_settings.configurations["runtime"]["fill_patience"]):
                
                self.potion_patience = self.player_settings.configurations["runtime"]["fill_patience"]
            
            if (self.potion_patience <= 0):
                
                def click_idle() -> None:
                    
                    WizardUtils.move_mouse(self.idle_point, time_interval = 0.20)
                    WizardUtils.click_mouse(hold_time = 0.3)
                    
                click_idle()
                
                if (self.num_potions > 0):
                
                    pynput.keyboard.Controller().press(pynput.keyboard.Key.ctrl)
                    WizardUtils.sleep(0.5)
                    pynput.keyboard.Controller().press(pynput.keyboard.KeyCode(char = 'o'))
                    WizardUtils.sleep(0.1)
                    pynput.keyboard.Controller().release(pynput.keyboard.KeyCode(char = 'o'))
                    WizardUtils.sleep(0.3)
                    pynput.keyboard.Controller().release(pynput.keyboard.Key.ctrl)
                    
                    self.cur_mana    = self.player_settings.configurations["runtime"]["full_mana"]
                    self.num_potions = self.num_potions - 1
                
                elif (self.num_potions > -1):
                    
                    pynput.keyboard.Controller().press(pynput.keyboard.Key.end)
                    WizardUtils.sleep(0.2)
                    pynput.keyboard.Controller().release(pynput.keyboard.Key.end)
                    self.num_potions = self.num_potions - 1
                    
                self.potion_patience = self.player_settings.configurations["runtime"]["fill_patience"]
            
        return self
    
    def basic_idle(self, idle_time : Union[ float, int ] = 0.05) -> "WizardPlayer":
        
        if (self.should_idle):
            
            def click_idle() -> None:
                
                WizardUtils.move_mouse(self.idle_point, time_interval = 0.20)
                WizardUtils.click_mouse(hold_time = 0.3)
            
            if (numpy.random.uniform(0, 1) <= self.player_settings.configurations["runtime"]["book_rate"]):
                
                click_idle()
                WizardUtils.move_mouse(self.book_point, time_interval = 0.75)
                WizardUtils.click_mouse(hold_time = 0.3)
                WizardUtils.sleep(2.2)
                WizardUtils.move_mouse(self.book_point, time_interval = 0.50)
                WizardUtils.click_mouse(hold_time = 0.3)
            
            click_idle()
            pynput.keyboard.Controller().press('a')
            WizardUtils.sleep(idle_time)
            pynput.keyboard.Controller().release('a')
            WizardUtils.sleep(0.1)
            pynput.keyboard.Controller().press('d')
            WizardUtils.sleep(idle_time)
            pynput.keyboard.Controller().release('d')
            WizardUtils.sleep(0.4)
            
        self.should_idle = False
        
        return self
    
    def halfang_idle(self) -> "WizardPlayer":
        
        
        def click_idle() -> None:
            WizardUtils.move_mouse(WizardUtils.point_by_offset(self.idle_point, (5, 5)), time_interval = 0.5)
            WizardUtils.click_mouse(hold_time = 0.2)
        
        
        def determine_state() -> int:
            
            """
                Different States:
                    
                [ 0 ] - IDLE 
                [ 1 ] - COMBAT
                [ 2 ] - ANIMATION / SCREEN LOADING / WINDOW MINIMIZED
                
            """
            
        # >> determine the current state >>
            
            screenshot = self.screenshot()
            
            current_state = ModelManager.determine_state(
                WizardUtils.crop_image(screenshot, self.book_bounding_box[0:2], self.book_bounding_box[2:4]),
                WizardUtils.crop_image(screenshot, self.pass_bounding_box[0:2], self.pass_bounding_box[2:4])
            )
            
        # << determine the curernt state <<
        
            return current_state
        
        
        def entrance_exit_success() -> bool:
            
            # whether or not the loading screen is present
            
            return (determine_state() == ModelManager.STATE_ANIMATION)
        
        
        def wait_success() -> bool:
            
            # whether or not the loading screen has disappeared
            
            return (determine_state() == ModelManager.STATE_IDLE)
        
        
        def battle_reentrance_success() -> bool:
            
            # whether or not we have entered combat
            
            return (determine_state() == ModelManager.STATE_COMBAT)
        
        
        if (self.should_idle):
                
        # >> turning around to exit the cave >>
        
            click_idle()
            HalfangUtils.exit_halfang_2(entrance_exit_success)
            
        # << turning around to exit the cave <<
            
        
        # >> waiting for loading screen to disappear >>
        
            while not (wait_success()):
                WizardUtils.sleep(0.1)
            WizardUtils.sleep(1.0)
                
        # << waiting for loading screen to disappear <<
                
        
        # >> pressing 'x' to re-enter the cave >>
        
            click_idle()
            HalfangUtils.enter_dungeon(entrance_exit_success)
            
        # << pressing 'x' to re-enter the cave <<
            
        
        # >> waiting for loading screen to disappear >>
        
            while not (wait_success()):
                WizardUtils.sleep(0.1)
            WizardUtils.sleep(0.75)
                
        # << waiting for loading screen to disappear <<
        
        
        # >> running to enter combat with Halfang >>
        
            click_idle()
            HalfangUtils.enter_battle(battle_reentrance_success)
            
        # << running to enter combat with Halfang
        
        self.should_idle = False
        
        return self
    
    def select_cards(self, verbose : bool = True) -> "WizardPlayer":
        
        def click_idle() -> None:
            WizardUtils.move_mouse(WizardUtils.point_by_offset(self.idle_point, (5, 5)), time_interval = 0.5)
            WizardUtils.click_mouse(hold_time = 0.2)
            
        def click_pass() -> None:
            WizardUtils.move_mouse(WizardUtils.point_by_offset(self.pass_point, (5, 2)), time_interval = 1.0)
            WizardUtils.click_mouse(hold_time = 0.3)
            
        def should_heal() -> bool:
            
            """
            
                Criteria:
                    
                [ 1 ] Activation by probability         ( heal rate   )
                [ 2 ] Health score lower than threshold ( heal thresh )
                
            """
            
        # >> evaluates whether or not healing is necessary 
            
            by_rate  = ((numpy.random.uniform(0, 1) <= self.player_settings.configurations["runtime"]["heal_rate"]  ))
            by_score = ((self.health_score          <= self.player_settings.configurations["runtime"]["heal_thresh"]))
            
        # << evaluates whether or not healing is necessary
            
            return ((by_rate) and (by_score))
        
        def verbose_string(first_card  : Union[  type(None), int  ],
                           second_card : Union[  type(None), int  ],
                           action_type :                     int   ) -> None:
            
            nonlocal card_quantity
            
            print_strings = [ "C-{}".format(card_quantity), "PASS" ]
            
            if (action_type == ModelManager.ACTION_ATTACK):
                
                if (second_card is None):
                    
                    print_strings[1] = "{}".format(first_card)
                    
                else:
                    
                    print_strings[1] = "{}+{}".format(first_card, second_card)
                
            elif (action_type == ModelManager.ACTION_HEAL):
                
                print_strings[1] = "HEAL"
            
            self.print_status("Combat", self.num_potions, self.cur_health, self.cur_mana, self.health_score, self.mana_score, self.potion_patience, print_strings)
            
        def adjust_mana(first_card  : Union[  type(None), int  ],
                        second_card : Union[  type(None), int  ],
                        action_type :                     int   ) -> None:
            
            if (action_type == ModelManager.ACTION_ATTACK):
                
                self.cur_mana -= self.player_settings.configurations["runtime"]["attack_mana"]
                
            elif (action_type == ModelManager.ACTION_HEAL):
                
                self.cur_mana -= self.player_settings.configurations["runtime"]["heal_mana"]
        
        screenshot = self.screenshot()
        
        
        # evaluates the number of cards present on the screen
        card_quantity = ModelManager.count_cards(
            WizardUtils.crop_image(screenshot, self.deck_bounding_box[0:2], self.deck_bounding_box[2:4])    
        )
        
        click_idle()
        
        if (card_quantity == 0):
            
            # pass this round if no cards are present
            click_pass()
            
        else:
        
            ((first_card, second_card), (first_type, second_type), action_type) = ModelManager.find_card_combination([
                WizardUtils.crop_image(screenshot, bounding_box[  0:2  ], bounding_box[  2:4  ])
                    for bounding_box in self.card_bounding_box[  card_quantity - 1  ]
            ], should_heal = should_heal, predictor = self.player_settings.configurations["runtime"]["card_predictor"])
            
            if (verbose):
                verbose_string(first_card, second_card, action_type)
                
            if (self.detect_digits == 0):
                
                adjust_mana(first_card, second_card, action_type)
            
            if ((first_card is None) and (second_card is None)):
                
                # pass this round if no cards are available
                click_pass()
                
            else:
            
                if (first_card is not None):
                    
                    # select the first card ( click to attack, heal or initiate enchantment )
                    WizardUtils.click_card(self.card_bounding_box, card_quantity, first_card + 1)
                    
                if (second_card is not None):
                    
                    # select the second card ( click to complete enchantment )
                    WizardUtils.click_card(self.card_bounding_box, card_quantity, second_card + 1)
                    
                    # the second card shifts to the left if the first card was to its left
                    if (first_card < second_card):
                        second_card -= 1
                        
                    # select the second card after shifting ( click to attack )
                    WizardUtils.click_card(self.card_bounding_box, card_quantity - 1, second_card + 1, move_time = 1.5)
            
        click_idle()
        
        self.should_idle = True
        
        return self
        
    def execute_once(self, idle_function : Union[  type(None), Callable  ] = None, verbose : bool = True) -> "WizardPlayer":
        
        def crop_multiple(screenshot : numpy.ndarray, bounding_boxes : List[ Tuple[ int ] ]) -> numpy.ndarray:
            
            return numpy.stack([
                WizardUtils.crop_image(screenshot, bounding_box[ 0:2 ], bounding_box[ 2:4 ])
                    for bounding_box in bounding_boxes
            ])
        
        def determine_health_mana_values(screenshot : numpy.ndarray) -> Tuple[ int ]:
            
            health_value = ModelManager.classify_digits(crop_multiple(screenshot, self.digH_bounding_box[
                 ModelManager.determine_health_digit_count(crop_multiple(screenshot, [self.panelH_bounding_box])[0]) - 1]), combine_digits = True)
            
            mana_value = ModelManager.classify_digits(crop_multiple(screenshot, self.digM_bounding_box[
                ModelManager.determine_mana_digit_count(crop_multiple(screenshot, [self.panelM_bounding_box])[0]) - 1]), combine_digits = True)
            
            return (health_value, mana_value)
        
        if (idle_function is None):
            idle_function = self.basic_idle
        
        screenshot = self.screenshot()
        
        (self.health_score, self.mana_score) = ModelManager.detect_health_mana_scores(
            WizardUtils.crop_image(screenshot, self.orbs_bounding_box[  0:2  ], self.orbs_bounding_box[  2:4  ])    
        )
        
        if (self.detect_digits == 1):
        
            (self.cur_health, self.cur_mana) = determine_health_mana_values(screenshot)
            
        else:
            
            self.cur_health = "?"
        
        current_state = ModelManager.determine_state(
            WizardUtils.crop_image(screenshot, self.book_bounding_box[  0:2  ], self.book_bounding_box[  2:4  ]),
            WizardUtils.crop_image(screenshot, self.pass_bounding_box[  0:2  ], self.pass_bounding_box[  2:4  ])
        )
        
        if (self.show_window):
            
            target_mask = self.player_settings.generate_mask(
                self.red_frame.shape, card_quantity = self.display_quantity, resize_ratio = 1)
            
            display_frame = numpy.where(target_mask, self.red_frame, screenshot)
            
            display_frame = WizardUtils.crop_image(
                display_frame, self.window_bounding_box[ 0:2 ], self.window_bounding_box[ 2:4 ])
            
            cv2.imshow(self.window_name, display_frame)
            
            wait_key = cv2.waitKey(1)
            
            if (ord("1") <= wait_key <= ord("7")):
                self.display_quantity = (wait_key - ord("0"))
            
        elif (cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE)):
            
            cv2.destroyWindow(self.window_name)
        
        if (current_state == ModelManager.STATE_ANIMATION):
            
            if (verbose):
                self.print_status("Animation", self.num_potions, "?", "?", "?", "?", self.potion_patience)
        
        elif (current_state == ModelManager.STATE_IDLE):
            
            if (verbose):
                self.print_status("Idle", self.num_potions, self.cur_health, self.cur_mana, self.health_score, self.mana_score, self.potion_patience)
            
            self.drink_potion();  idle_function()
        
        elif (current_state == ModelManager.STATE_COMBAT):
            
            if (verbose):
                self.print_status("Combat", self.num_potions, self.cur_health, self.cur_mana, self.health_score, self.mana_score, self.potion_patience)
            
            self.select_cards(verbose = verbose)
            
        return self
    
    @staticmethod 
    def print_status(state : str, num_potions : int, cur_health : int, cur_mana : int, health_score : int, mana_score : int, potion_patience : int, additional_strings : Union[ List[ str ], Tuple[ str ] ] = [], print_length : int = 80) -> None:
        
        print_string = " ".join([
            "[ {} ]".format(state),
            "[ P-{} ]".format(num_potions),
            "[ H-{} ]".format(cur_health),
            "[ M-{} ]".format(cur_mana),
            "[ R-{} ]".format(health_score),
            "[ B-{} ]".format(mana_score),
            "[ W-{} ]".format(potion_patience)
        ] + [
            "[ {} ]".format(target_string)
                for target_string in additional_strings
        ])
            
        sys.stdout.write("\r" + WizardUtils.pad_string(print_string, print_length))
        sys.stdout.flush()
    
    def run_bot(self, idle_function : Union[  type(None), Callable  ] = None) -> "WizardPlayer":
        
        def keyboard_on_press(key : Union[ pynput.keyboard.Key, pynput.keyboard.KeyCode ]) -> None:
            
            nonlocal unpaused, nonterminal
            
            if (key == pynput.keyboard.Key.f9):
                unpaused = not unpaused 
                
            elif (key == pynput.keyboard.Key.f10):
                (unpaused, nonterminal) = (
                    False, False    
                )
                
            elif (key == pynput.keyboard.Key.f11):
                self.show_window = not self.show_window
                
                
        (unpaused, nonterminal) = (True, True)
        
        keyboard_listener = pynput.keyboard.Listener(on_press = keyboard_on_press)
        
        keyboard_listener.start()
        
        WizardUtils.countdown(countdown_time = 3)
        
        while (nonterminal):
            
            while (unpaused):
                
                self.execute_once(idle_function)
                
                WizardUtils.sleep(1)
                
            if (cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE)):
                
                cv2.destroyWindow(self.window_name)
                
            self.print_status("Paused", self.num_potions, self.cur_health, self.cur_mana, self.health_score, self.mana_score, self.potion_patience)
            
            WizardUtils.sleep(0.25)
            
        self.print_status("Terminated", self.num_potions, self.cur_health, self.cur_mana, self.health_score, self.mana_score, self.potion_patience)
        
        print("\n")
        
        keyboard_listener.stop()
        
        cv2.destroyAllWindows()
        
        return self
    
def main(book_model_name : str, 
         pass_model_name : str, 
         deck_model_name : str, 
         card_model_name : str,
         orbH_model_name : str,
         orbM_model_name : str,
         digH_model_name : str,
         digM_model_name : str,
         digi_model_name : str,
         config_file     : str) -> None:
    
    player_settings = WizardSettings(config_file)
    
    WizardPlayer.initialize(
        book_model_name, pass_model_name, card_model_name, 
        deck_model_name, orbH_model_name, orbM_model_name,
        digH_model_name, digM_model_name, digi_model_name
    )
    
    while True:
        print("--options")
        print("[ P ] Play [ append 'H' to farm Halfang dungeon ]")
        print("[ C ] Configure Settings")
        print("[ S ] Save Settings")
        print("[ E ] Exit")
        print("")
        user_choice = input("> ").lower()
        
        if (user_choice.startswith('p')):
            if not (player_settings.settings_ready() or player_settings.load()):
                player_settings.initialize_configurations().full_configure()
            wizard_player = WizardPlayer(player_settings = player_settings)
            idle_function = ((wizard_player.halfang_idle) if (user_choice.endswith("h")) else (None))
            wizard_player.run_bot(idle_function)
        elif user_choice.startswith('c'):
            if (player_settings.settings_ready()):
                player_settings.configure()
            elif (player_settings.load()):
                player_settings.configure()
            else:
                player_settings.initialize_configurations().full_configure()
        elif (user_choice.startswith('s')):
            player_settings.save()
        elif (user_choice.startswith('e')):
            return
    
if (__name__ == "__main__"):   
    
    book_model_name = "./keywizardModel/book_predictor.pb"
    
    pass_model_name = "./keywizardModel/pass_predictor.pb"
    
    card_model_name = [  "./keywizardModel/meteor/card_predictor.pb", "./keywizardModel/tempest/card_predictor.pb"  ]
    
    deck_model_name = "./keywizardModel/deck_predictor.pb"
    
    orbH_model_name = "./keywizardModel/orbH_predictor.pb"
    
    orbM_model_name = "./keywizardModel/orbM_predictor.pb"
    
    digH_model_name = "./keywizardModel/digH_predictor.pb"
    
    digM_model_name = "./keywizardModel/digM_predictor.pb"
    
    digi_model_name = "./keywizardModel/digi_predictor.pb"
    
    config_file     = "./keywizardConfig/wizard_config.json"
    
    test = 3
    
    if (test == 1):
        
        main(
            book_model_name, pass_model_name, deck_model_name, 
            card_model_name, orbH_model_name, orbM_model_name, 
            digH_model_name, digM_model_name, digi_model_name,
            config_file
        )
    
    elif (test == 2):
        
        WizardPlayer.initialize(
            book_model_name, pass_model_name, card_model_name, 
            deck_model_name, orbH_model_name, orbM_model_name, 
            digH_model_name, digM_model_name, digi_model_name
        )
        
        instance_list = [
            WizardSettings("./keywizardConfig/wizard_config.json"),
            WizardSettings("./keywizardConfig/wizard_config_sub.json")
        ]
        
        for index, _ in enumerate(instance_list):
            instance_list[ index ].load()
        
        WizardPlayer.initialize_instances(instance_list)
        
        WizardPlayer.run_instances()
        
    elif (test == 3):
        
        WizardPlayer.SELECT_WINDOW = True
        
        main(
            book_model_name, pass_model_name, deck_model_name, 
            card_model_name, orbH_model_name, orbM_model_name, 
            digH_model_name, digM_model_name, digi_model_name,
            config_file
        )