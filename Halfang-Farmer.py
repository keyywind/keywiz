from typing import Union, Tuple, Type
import pyautogui, tesserocr, datetime, numpy, json, time, PIL, cv2, sys, gc, os
from keywizardUtilities.halfang_utils.bot_utils import BotUtils 

from keyio.keyutils import KeyUtils 
from keyio.mouseutils import MouseUtils 
from keyio.windowutils import WindowUtils 

class FarmerBot:
    
    farmer_settings_name = os.path.join(os.path.join(os.path.dirname(__file__), "keywizardConfig"), "halfang_config.json")
    
    STATE_ANIMATION      = 0
    
    STATE_IDLE           = 1
    
    STATE_COMBAT         = 2
    
    CARD_ATTACK          = 0
    
    CARD_ENCHANT         = 1
    
    CARD_HEAL            = 2
    
    CARD_GREY            = 3
    
    ACTION_ATTACK        = 0
    
    ACTION_ENCHANT       = 1
    
    ACTION_HEAL          = 2
    
    ACTION_PASS          = 3
    
    BINARY_THRESHOLD     = 0.5
    
    PAD_LEN              = 70
    
    SCROLL_OUT           = -10
    
    farmer_settings      = None
    
    book_predictor       = None
    
    pass_predictor       = None
    
    deck_predictor       = None
    
    card_predictor       = None
    
    orbh_predictor       = None
    
    orbm_predictor       = None
    
    screenshot           = None
    
    state                = None
    
    card_quantity        = None
    
    card_types           = None
    
    action_type          = None
    
    action_cards         = None
    
    potion_quantity      = None
    
    precise_health_score = None
    
    precise_mana_score   = None 
    
    refill_patience      = None
    
    paused               = None
    
    terminated           = None
    
    k_listener           = None
    
    enchant_timeout      = None
    
    w101_bounding_box    = None
    
    book_bounding_box    = None
    
    pass_bounding_box    = None
    
    deck_bounding_box    = None
    
    card_bounding_box    = None
    
    orbs_bounding_box    = None
    
    avai_bounding_box    = None
    
    digh_bounding_box    = None
    
    digm_bounding_box    = None
    
    book_centroid        = None
    
    pass_centroid        = None
    
    idle_centroid        = None
    
    tesseract_api        = None
    
    @classmethod
    def _initialize_default_settings(class_) -> Type[ "FarmerBot" ]:
        class_.farmer_settings = {
            "bounding_boxes" : {
                "window" : (  6,  36, 800, 600),
                "book"   : (698, 498, 100, 100),
                "pass"   : (206, 326, 100, 100),
                "deck"   : (163, 250, 480, 100),
                "slot"   : ( 26,  16, 430,  70),
                "orbs"   : (  1, 472, 128, 128),
                "avai"   : (372, 130,  64,  64),
                "digh"   : ( 12, 510,  70,  30),
                "digm"   : ( 67, 536,  50,  30)
            },
            "constants" : {
                "potion_quantity"     :   4,
                "heal_health_score"   :   2,
                "refill_health_score" :   0,
                "refill_mana_score"   :   0,
                "dungeon_patience"    :   3,
                "refill_mana_score_2" :  50,
                "refill_patience"     :   5,
                "heal_rate"           : 0.5,
                "enchant_timeout"     :   5
            },
            "models" : {
                "book" : "./keywizardModel/book_predictor.pb",
                "pass" : "./keywizardModel/pass_predictor.pb",
                "deck" : "./keywizardModel/deck_predictor.pb",
                "card" : "./keywizardModel/card_predictor.pb",
                "orbh" : "./keywizardModel/orbh_predictor.pb",
                "orbm" : "./keywizardModel/orbm_predictor.pb",
                "avai" : "./keywizardModel/avai_predictor.pb"
            },
            "variables" : {
                "yellow_text_hsv" : {
                    "lower" : ( 30, 200,  84),
                    "upper" : ( 30, 255, 255)
                }
            },
            "slot_bounding_boxes" : [
                [ (220, 0, 45, 72) ],
                [ (194, 0, 45, 72), (247, 0, 45, 72) ],
                [ (166, 0, 45, 72), (220, 0, 45, 72), (273, 0, 45, 72) ],
                [ (140, 0, 45, 72), (194, 0, 45, 72), (247, 0, 45, 72), (301, 0, 45, 72) ],
                [ (113, 0, 45, 72), (166, 0, 45, 72), (220, 0, 45, 72), (273, 0, 45, 72), (327, 0, 45, 72) ],
                [ ( 86, 0, 45, 72), (141, 0, 45, 72), (193, 0, 45, 72), (247, 0, 45, 72), (301, 0, 45, 72), (354, 0, 45, 72) ],
                [ ( 58, 0, 45, 72), (113, 0, 45, 72), (167, 0, 45, 72), (220, 0, 45, 72), (274, 0, 45, 72), (327, 0, 45, 72), (381, 0, 45, 72) ]
            ]
        }
        return class_
    
    @staticmethod
    def crop_image(image : numpy.ndarray, bounding_box : Tuple[ int ]) -> numpy.ndarray:
        (x, y, w, h) = bounding_box
        return numpy.copy(image)[ y : y + h, x : x + w ]
    
    @staticmethod
    def get_absolute_bounding_box(window_bounding_box : Tuple[ int ], 
                                  bounding_box        : Tuple[ int ]) -> Type[ "FarmerBot" ]:
        return (
            window_bounding_box[0] + bounding_box[0],
            window_bounding_box[1] + bounding_box[1],
            bounding_box[2],
            bounding_box[3]
        )
    
    @staticmethod
    def bounding2centroid(bounding_box : Tuple[ int ]) -> Tuple[ int ]:
        return (
            bounding_box[0] + bounding_box[2] // 2,
            bounding_box[1] + bounding_box[3] // 2
        )
    
    @classmethod
    def save_settings(class_) -> Type[ "FarmerBot" ]:
        if (class_.farmer_settings is None):
            raise Exception("Cannot save configurations because settings have not been initialized.\n")
        with open(class_.farmer_settings_name, "w") as write_file:
            write_file.write(json.dumps(class_.farmer_settings, indent = 4))
        return class_
    
    @classmethod
    def initialize(class_) -> Type[ "FarmerBot" ]:
        
        BotUtils.initialize_library()
        
        def load_models() -> None:
            nonlocal class_ 
            class_.book_predictor = cv2.dnn.readNetFromTensorflow(
                class_.farmer_settings["models"]["book"])
            class_.pass_predictor = cv2.dnn.readNetFromTensorflow(
                class_.farmer_settings["models"]["pass"])
            class_.deck_predictor = cv2.dnn.readNetFromTensorflow(
                class_.farmer_settings["models"]["deck"])
            class_.card_predictor = cv2.dnn.readNetFromTensorflow(
                class_.farmer_settings["models"]["card"])
            class_.orbh_predictor = cv2.dnn.readNetFromTensorflow(
                class_.farmer_settings["models"]["orbh"])
            class_.orbm_predictor = cv2.dnn.readNetFromTensorflow(
                class_.farmer_settings["models"]["orbm"])
            class_.avai_predictor = cv2.dnn.readNetFromTensorflow(
                class_.farmer_settings["models"]["avai"])
            
        def unpack_bounding_boxes() -> None:
            nonlocal class_
            class_.w101_bounding_box = class_.farmer_settings["bounding_boxes"]["window"]
            class_.book_bounding_box = class_.get_absolute_bounding_box(
                class_.w101_bounding_box,
                class_.farmer_settings["bounding_boxes"]["book"])
            class_.pass_bounding_box = class_.get_absolute_bounding_box(
                class_.w101_bounding_box, 
                class_.farmer_settings["bounding_boxes"]["pass"])
            class_.deck_bounding_box = class_.get_absolute_bounding_box(
                class_.w101_bounding_box,
                class_.farmer_settings["bounding_boxes"]["deck"])
            class_.orbs_bounding_box = class_.get_absolute_bounding_box(
                class_.w101_bounding_box,
                class_.farmer_settings["bounding_boxes"]["orbs"])
            class_.avai_bounding_box = class_.get_absolute_bounding_box(
                class_.w101_bounding_box,
                class_.farmer_settings["bounding_boxes"]["avai"])
            class_.digh_bounding_box = class_.get_absolute_bounding_box(
                class_.w101_bounding_box,
                class_.farmer_settings["bounding_boxes"]["digh"])
            class_.digm_bounding_box = class_.get_absolute_bounding_box(
                class_.w101_bounding_box,
                class_.farmer_settings["bounding_boxes"]["digm"])
            slot_bounding_box        = class_.get_absolute_bounding_box(
                class_.deck_bounding_box, 
                class_.farmer_settings["bounding_boxes"]["slot"])
            
            class_.card_bounding_box = []
            for quantity_index in range(7):
                bounding_boxes = []
                for card_index in range(quantity_index + 1):
                    bounding_box = class_.get_absolute_bounding_box(
                        slot_bounding_box,
                        class_.farmer_settings["slot_bounding_boxes"][quantity_index][card_index]
                    )
                    bounding_boxes.append(bounding_box)
                class_.card_bounding_box.append(bounding_boxes)
                            
        def compute_centroids() -> None:
            nonlocal class_ 
            class_.book_centroid = class_.bounding2centroid(class_.book_bounding_box)
            class_.pass_centroid = class_.bounding2centroid(class_.pass_bounding_box)
            class_.idle_centroid = (
                (class_.book_centroid[0] + class_.pass_centroid[0]) // 2,
                (class_.book_centroid[1] + class_.pass_centroid[1]) // 2
            )
            
        if (os.path.isfile(class_.farmer_settings_name)):
            with open(class_.farmer_settings_name, "r") as read_file:
                class_.farmer_settings = json.loads(read_file.read())
        else:
            class_._initialize_default_settings()
            class_.save_settings()
        
        KeyUtils.configure_quantum(0.0001, True)
        
        class_.key_controller    = KeyUtils()
        class_.mouse_controller  = MouseUtils()
        class_.window_controller = WindowUtils()
        
        os.system("title Keywizard - Halfang Bot")
        os.system("color 1f")
        os.system("mode 100")
        os.system("cls")
        
        print("")
        
        sys.stdout.write(class_.pad_string("\r[ Press F8 to confirm selected window ]", class_.PAD_LEN))
        sys.stdout.flush()
        
        keep_running             = True 
        
        @class_.key_controller.monitor(KeyUtils.Key.KEY_F8)
        def monitor_F8(key_code : int, key_pressed : bool) -> None:
            nonlocal class_, keep_running 
            if (key_pressed):
                (sx, sy, ex, ey) = class_.window_controller.get_foreground_window()
                sy               = sy + 30
                class_.farmer_settings["bounding_boxes"]["window"] = [ sx, sy, 800, 600 ]
                keep_running     = False 
            
        class_.key_controller.initialize_monitors()
        class_.key_controller.start_thread()
        
        while (keep_running):
            time.sleep(0.5)
            
        class_.key_controller.stop_thread()
        
        class_.key_controller    = KeyUtils()
        
        sys.stdout.write(class_.pad_string("\r[ Window Selected ]", class_.PAD_LEN))
        sys.stdout.flush()
        
        print("\n")
        
        load_models()
        
        unpack_bounding_boxes()
        
        compute_centroids()
        
        class_.potion_quantity   = class_.farmer_settings["constants"]["potion_quantity"]
        
        class_.dungeon_patience  = class_.farmer_settings["constants"]["dungeon_patience"]
        
        class_.tesseract_api     = tesserocr.PyTessBaseAPI(oem = tesserocr.OEM.LSTM_ONLY, psm = 6)
        
        class_.tesseract_api.SetVariable("tessedit_char_whitelist", "0123456789")
        
        class_.text_hsv_range    = class_.farmer_settings["variables"]["yellow_text_hsv"]
        
        class_.refill_patience   = class_.farmer_settings["constants"]["refill_patience"]
        
        class_.enchant_timeout   = class_.farmer_settings["constants"]["enchant_timeout"]
                
        return class_
    
    @classmethod 
    def recognize_text(class_, image : numpy.ndarray) -> str:
        class_.tesseract_api.SetImage(PIL.Image.fromarray(image))
        return class_.tesseract_api.GetUTF8Text()
    
    @classmethod 
    def binarize_screenshot(class_) -> numpy.ndarray:
        screenshot = cv2.cvtColor(class_.screenshot, cv2.COLOR_BGR2HSV)
        screenshot = cv2.inRange(screenshot, 
            numpy.array(class_.text_hsv_range["lower"]), 
            numpy.array(class_.text_hsv_range["upper"])
        )
        screenshot = cv2.bitwise_not(screenshot)
        return screenshot 
    
    @classmethod 
    def get_precise_score(class_) -> Tuple[ int ]:
        screenshot = class_.binarize_screenshot()
        health_region = cv2.resize(class_.crop_image(screenshot, class_.digh_bounding_box), None, None, fx = 3, fy = 3)
        mana_region   = cv2.resize(class_.crop_image(screenshot, class_.digm_bounding_box), None, None, fx = 3, fy = 3)
        health_text   = class_.recognize_text(health_region)
        mana_text     = class_.recognize_text(mana_region)
        health_text   = "".join(filter(lambda c : c.isnumeric(), health_text))
        mana_text     = "".join(filter(lambda c : c.isnumeric(), mana_text))
        return (
            (int(health_text) if (health_text.__len__()) else (-1)),
            (int(mana_text)   if (mana_text.__len__())   else (-1))
        )
    
    @classmethod 
    def set_precise_score(class_) -> Type[ "FarmerBot" ]:
        (HS, MS) = class_.get_precise_score()
        class_.precise_health_score = HS
        class_.precise_mana_score   = MS
        return class_ 
    
    @classmethod
    def basic_predict(class_, predictor_name : str, image_list : numpy.ndarray) -> numpy.ndarray:
        try:
            predictor = getattr(class_, predictor_name)
            (h, w)    = image_list[0].shape[0:2]
            def predict_blob(blob_image : numpy.ndarray) -> numpy.ndarray:
                nonlocal predictor
                predictor.setInput(blob_image)
                return predictor.forward()
            blob_list   = [
                cv2.dnn.blobFromImage(__image, 1.0, (w, h))
                    for __image in numpy.float32(image_list) / 255.0
            ]
            return numpy.stack([  predict_blob(__image) for __image in blob_list  ])
        except:
            print(predictor_name)
    
    @classmethod 
    def count_cards(class_) -> int:
        deck_region   = class_.crop_image(class_.screenshot, class_.deck_bounding_box)
        card_quantity = int(numpy.argmax(class_.basic_predict("deck_predictor", numpy.stack([ deck_region ]))[0]))
        return card_quantity
    
    @classmethod 
    def set_card_quantity(class_) -> Type[ "FarmerBot" ]:
        class_.card_quantity = class_.count_cards()
        return class_ 
        
    @classmethod
    def set_screenshot(class_) -> Type[ "FarmerBot" ]:
        class_.screenshot = cv2.cvtColor(numpy.uint8(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
        return class_
    
    @classmethod 
    def classify_cards(class_) -> numpy.ndarray:
        card_regions = numpy.stack([
            class_.crop_image(class_.screenshot, class_.card_bounding_box[class_.card_quantity - 1][card_index])
                for card_index in range(class_.card_quantity)
        ])
        def classify_card(prediction : numpy.ndarray) -> int:
            return int(numpy.argmax(prediction))
        card_types = numpy.stack([
            classify_card(card_prediction) for card_prediction \
                in class_.basic_predict("card_predictor", card_regions)
        ])
        return card_types 
    
    @classmethod 
    def set_card_classification(class_) -> Type[ "FarmerBot" ]:
        class_.card_types = class_.classify_cards()
        return class_ 
    
    @classmethod
    def acquire_orb_score(class_) -> Tuple[ int ]:
        orb_region   = class_.crop_image(class_.screenshot, class_.orbs_bounding_box)
        score_health = int(numpy.argmax(class_.basic_predict(
            "orbh_predictor", numpy.stack([ orb_region ]))[0]))
        score_mana   = int(numpy.argmax(class_.basic_predict(
            "orbm_predictor", numpy.stack([ orb_region ]))[0]))
        return (score_health, score_mana)
    
    @classmethod
    def should_drink_potion(class_) -> bool:
        (score_health, score_mana) = class_.set_precise_score().acquire_orb_score()
        low_health   = (score_health              <= class_.farmer_settings["constants"]["refill_health_score"])
        low_mana     = (score_mana                <= class_.farmer_settings["constants"]["refill_mana_score"])
        low_mana_2   = (class_.precise_mana_score <= class_.farmer_settings["constants"]["refill_mana_score_2"])
        if (low_health or (low_mana and low_mana_2)):
            if (class_.refill_patience == 0):
                class_.refill_patience = class_.farmer_settings["constants"]["refill_patience"]
                return True 
            else:
                class_.refill_patience -= 1
                return False 
        else:
            class_.refill_patience = class_.farmer_settings["constants"]["refill_patience"]
            return False
    
    @classmethod
    def potion_available(class_) -> bool:
        return (class_.potion_quantity > 0)
    
    @classmethod 
    def drink_potion(class_) -> Type[ "FarmerBot" ]:
        control    = KeyUtils.Key.KEY_CTRL
        oh         = KeyUtils.KeyCode.CHAR_O
        controller = class_.key_controller 
        controller.press_key(control)
        class_.preemptive_sleep(0.10)
        controller.press_key(oh)
        class_.preemptive_sleep(0.20)
        controller.release_key(oh)
        class_.preemptive_sleep(0.05)
        controller.release_key(control)
        class_.potion_quantity -= 1
        return class_
    
    @classmethod
    def port_away(class_) -> Type[ "FarmerBot" ]:
        end        = KeyUtils.Key.KEY_END
        controller = class_.key_controller 
        controller.press_key(end)
        class_.preemptive_sleep(0.10)
        controller.release_key(end)
        return class_ 
    
    @classmethod
    def dungeon_available(class_) -> bool:
        avai_region = class_.crop_image(class_.screenshot, class_.avai_bounding_box)
        prediction  = numpy.argmax(class_.basic_predict("avai_predictor", numpy.stack([ avai_region ]))[0])
        available   = (prediction == 10)
        return available
    
    @classmethod
    def preemptive_sleep(class_, duration : Union[ float, int ], preemptive : bool = False) -> Type[ "FarmerBot" ]:
        start_of_time = datetime.datetime.now()
        while ((datetime.datetime.now() - start_of_time).total_seconds() <= duration):
            if (preemptive):
                pass
            else:
                time.sleep(0.05)
        return class_
    
    @staticmethod
    def pad_string(string : str, pad_len : int) -> str:
        str_len = string.__len__()
        return string + " " * (pad_len - str_len)
    
    @classmethod
    def countdown(class_, seconds : Union[ int, float ]) -> Type[ "FarmerBot" ]:
        start_of_time = datetime.datetime.now()
        print("")
        while True:
            elapsed   = (datetime.datetime.now() - start_of_time).total_seconds()
            if (elapsed >= seconds):
                break 
            print_str = "\r[ Starting in {} seconds ]".format(seconds - int(elapsed))
            sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
            sys.stdout.flush()
            class_.preemptive_sleep(0.05)
        sys.stdout.write(class_.pad_string("\r[ Bot Initiated ]", class_.PAD_LEN))
        sys.stdout.flush()
        print("\n")
        return class_ 
    
    @classmethod
    def enter_dungeon(class_) -> Type[ "FarmerBot" ]:
        ex         = KeyUtils.KeyCode.CHAR_X
        controller = class_.key_controller 
        controller.press_key(ex)
        class_.preemptive_sleep(0.1)
        controller.release_key(ex)
        return class_ 
    
    @classmethod
    def loading_screen_present(class_) -> bool:
        return class_.in_state_animation()
    
    @classmethod 
    def in_state_animation(class_) -> bool:
        return (class_.state == class_.STATE_ANIMATION)
    
    @classmethod
    def set_combat_action(class_) -> Type[ "FarmerBot" ]:
        (class_.action_type, class_.action_cards) = BotUtils.determine_moves(
            class_.card_types, class_.should_heal() * 1)
        return class_ 
    
    @classmethod
    def set_state(class_) -> Type[ "FarmerBot" ]:
        book_region  = class_.crop_image(class_.screenshot, class_.book_bounding_box)
        pass_region  = class_.crop_image(class_.screenshot, class_.pass_bounding_box)
        book_present = (class_.basic_predict("book_predictor", 
            numpy.stack([ book_region ]))[0] >= class_.BINARY_THRESHOLD)
        pass_present = (class_.basic_predict("pass_predictor", 
            numpy.stack([ pass_region ]))[0] >= class_.BINARY_THRESHOLD)
        if (book_present and pass_present):
            class_.state = class_.STATE_ANIMATION
        elif (book_present):
            class_.state = class_.STATE_IDLE 
        elif (pass_present):
            class_.state = class_.STATE_COMBAT 
        else:
            class_.state = class_.STATE_ANIMATION
        return class_
    
    @classmethod
    def click_position(class_, position : Tuple[ int ], press_duration : Union[ int, float ]) -> "FarmerBot":
        left_mouse = MouseUtils.LEFT_BUTTON
        controller = class_.mouse_controller
        controller.set_mouse_coord(position[0] - 5, position[1])
        class_.preemptive_sleep(0.10)
        controller.set_mouse_coord(*position) 
        class_.preemptive_sleep(0.05)
        controller.press_button(left_mouse)
        class_.preemptive_sleep(press_duration)
        controller.set_mouse_coord(*position)
        class_.preemptive_sleep(0.05)
        controller.release_button(left_mouse)
        return class_ 
    
    @classmethod
    def run_forward(class_, press : bool = True) -> Type[ "FarmerBot" ]:
        double_u   = KeyUtils.KeyCode.CHAR_W
        controller = class_.key_controller 
        if (press):
            controller.press_key(double_u)
        else:
            controller.release_key(double_u)
        return class_ 
    
    @classmethod
    def in_state_idle(class_) -> bool:
        return (class_.state == class_.STATE_IDLE)
    
    @classmethod
    def in_state_combat(class_) -> bool:
        return (class_.state == class_.STATE_COMBAT)
    
    @classmethod 
    def should_pass(class_) -> bool:
        return (class_.action_type == class_.ACTION_PASS)
    
    @classmethod
    def should_heal(class_) -> bool:
        orb_region = class_.crop_image(class_.screenshot, class_.orbs_bounding_box)
        orb_score  = int(numpy.argmax(
            class_.basic_predict("orbh_predictor", numpy.stack([ orb_region ]))[0]))
        prob       = (numpy.random.uniform(0, 1) <= class_.farmer_settings["constants"]["heal_rate"])
        return ((prob) and (orb_score <= class_.farmer_settings["constants"]["heal_health_score"]))
    
    @classmethod
    def should_enchant(class_) -> bool:
        return (class_.action_type == class_.ACTION_ENCHANT)
    
    @classmethod
    def enchant_card(class_) -> Type[ "FarmerBot" ]:
        card_first_bounding_box  = class_.card_bounding_box[class_.card_quantity - 1][class_.action_cards[0]]
        card_second_bounding_box = class_.card_bounding_box[class_.card_quantity - 1][class_.action_cards[1]]
        class_.click_position(class_.bounding2centroid(card_first_bounding_box), press_duration = 0.1)
        class_.preemptive_sleep(0.2)
        class_.click_position(class_.bounding2centroid(card_second_bounding_box), press_duration = 0.1)
        return class_
    
    @classmethod
    def enchantment_complete(class_) -> bool:
        card_quantity = class_.count_cards()
        if (card_quantity == (class_.card_quantity - 1)):
            return True
        return False 
    
    @classmethod
    def basic_cast(class_, card_index : int = 0) -> Type[ "FarmerBot" ]:
        card_first_bounding_box = class_.card_bounding_box[class_.card_quantity - 1][class_.action_cards[card_index]]
        class_.click_position(class_.bounding2centroid(card_first_bounding_box), press_duration = 0.1)
        return class_ 
    
    @classmethod
    def pass_round(class_) -> Type[ "FarmerBot" ]:
        class_.click_position(class_.pass_centroid, press_duration = 0.10)
        return class_ 
    
    @classmethod 
    def toggle_book(class_) -> Type[ "FarmerBot" ]:
        class_.click_position(class_.book_centroid, press_duration = 0.10)
        return class_
    
    @classmethod 
    def idle_click(class_) -> Type[ "FarmerBot" ]:
        class_.click_position(class_.idle_centroid, press_duration = 0.10)
        return class_
    
    @classmethod
    def shift_attack(class_) -> Type[ "FarmerBot" ]:
        if (class_.action_cards[0] < class_.action_cards[1]):
            card_second_bounding_box = class_.card_bounding_box[class_.card_quantity - 2][class_.action_cards[1] - 1]
        else:
            card_second_bounding_box = class_.card_bounding_box[class_.card_quantity - 2][class_.action_cards[1]]
        class_.click_position(class_.bounding2centroid(card_second_bounding_box), press_duration = 0.1)
        return class_ 
    
    @classmethod
    def turn_around(class_) -> Type[ "FarmerBot" ]:
        controller = class_.key_controller
        controller.press_key(KeyUtils.KeyCode.CHAR_A)
        class_.preemptive_sleep(0.68, preemptive = True)
        controller.release_key(KeyUtils.KeyCode.CHAR_A)
        return class_
    
    @classmethod
    def goto_dungeon_side(class_) -> Type[ "FarmerBot" ]:
        key_w      = KeyUtils.KeyCode.CHAR_W
        key_d      = KeyUtils.KeyCode.CHAR_D
        controller = class_.key_controller 
        controller.press_key(key_w)
        class_.preemptive_sleep(0.23, preemptive = True)
        controller.release_key(key_w)
        controller.press_key(key_d)
        class_.preemptive_sleep(1.25, preemptive = True) 
        controller.release_key(key_d)
        return class_
    
    @classmethod 
    def check_pause(class_) -> bool:
        if (class_.terminated):
            sys.stdout.write(class_.pad_string("\r[ TERMINATED ]", class_.PAD_LEN))
            sys.stdout.flush()
            print("\n")
            class_.key_controller.stop_thread()
            return True
        else:
            while (class_.paused):
                sys.stdout.write(class_.pad_string("\r[ PAUSED ]", class_.PAD_LEN))
                sys.stdout.flush()
                class_.preemptive_sleep(1.0)
            return False 
    
    @classmethod 
    def farm_halfang(class_) -> Type[ "FarmerBot" ]:
        
        class_.paused     = False 
        
        class_.terminated = False 
        
        @class_.key_controller.monitor(KeyUtils.Key.KEY_F9)
        def monitor_pause(key_code : int, key_pressed : bool) -> None:
            nonlocal class_ 
            if (key_pressed):
                class_.paused = not class_.paused 
                
        @class_.key_controller.monitor(KeyUtils.Key.KEY_F10)
        def monitor_terminate(key_code : int, key_pressed : bool) -> None:
            nonlocal class_ 
            if (key_pressed):
                class_.terminated = True 
        
        class_.key_controller.initialize_monitors()
        
        class_.key_controller.start_thread()
        
        class_.countdown(3)
                
        while True:
            
            if (class_.check_pause()):
                return class_ 
            
            class_.idle_click()
            
            mouse_controller = class_.mouse_controller 
            
            mouse_controller.scroll(dy = class_.SCROLL_OUT)
            
            gc.collect()
            
            class_.set_screenshot()
                        
            if (class_.should_drink_potion()):
                if (class_.potion_available()):
                    class_.drink_potion()
                else:
                    class_.port_away()
                    class_.terminated = True 
                    if (class_.check_paused()):
                        return class_ 
                            
            class_.set_screenshot()
            (HS, MS) = class_.acquire_orb_score()
            class_.set_precise_score()
            (DHS, DMS, PS) = (
                class_.precise_health_score,
                class_.precise_mana_score,
                class_.potion_quantity
            )
            print_str = "\r[ WAITING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                HS, MS, DHS, DMS, PS, class_.refill_patience)
            sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
            sys.stdout.flush()
                
            start_of_time = None
                
            while True:
                
                if (class_.check_pause()):
                    return class_ 
                
                class_.set_screenshot()
                
                if (class_.dungeon_available()):
                    if (start_of_time is None):
                        start_of_time = datetime.datetime.now()
                    elif ((datetime.datetime.now() - start_of_time).total_seconds() >= class_.dungeon_patience):
                        break
                else:
                    start_of_time = None
                
                class_.preemptive_sleep(1.0)
                
            class_.set_screenshot()
            (HS, MS) = class_.acquire_orb_score()
            class_.set_precise_score()
            (DHS, DMS, PS) = (
                class_.precise_health_score,
                class_.precise_mana_score,
                class_.potion_quantity
            )
            print_str = "\r[ ENTERING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                HS, MS, DHS, DMS, PS, class_.refill_patience)
            sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
            sys.stdout.flush()
                
            class_.idle_click()
                
            class_.enter_dungeon()
            
            start_of_time = None
            
            while True:
                
                if (class_.check_pause()):
                    return class_ 
                
                class_.set_screenshot()
                class_.set_state()
                
                if (class_.loading_screen_present()):
                    if (start_of_time is None):
                        start_of_time = datetime.datetime.now()
                    elif ((datetime.datetime.now() - start_of_time).total_seconds() >= 0.5):
                        break
                else:
                    start_of_time = None
                            
                class_.preemptive_sleep(0.10, preemptive = True)
                
            while True:
                class_.set_screenshot()
                class_.set_state()
                if (class_.loading_screen_present() == False):
                    break
                class_.preemptive_sleep(0.5)
            
            if (class_.check_pause()):
                return class_ 
            
            class_.preemptive_sleep(1.0)
            
            class_.set_screenshot()
            (HS, MS) = class_.acquire_orb_score()
            class_.set_precise_score()
            (DHS, DMS, PS) = (
                class_.precise_health_score,
                class_.precise_mana_score,
                class_.potion_quantity
            )
            print_str = "\r[ JOINING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                HS, MS, DHS, DMS, PS, class_.refill_patience)
            sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
            sys.stdout.flush()
            
            class_.idle_click()
            
            class_.run_forward(press = True)
            
            while True:
                
                if (class_.check_pause()):
                    return class_ 
                
                class_.set_screenshot()
                class_.set_state()
                if (class_.in_state_animation() == True):
                    break
                class_.preemptive_sleep(0.1)
                
            class_.idle_click()
                
            class_.run_forward(press = False)
            
            while True:
                
                if (class_.check_pause()):
                    return class_ 
                
                class_.set_screenshot()
                class_.set_state()
                if (class_.in_state_idle()):
                    (HS, MS) = class_.acquire_orb_score()
                    class_.set_precise_score()
                    (DHS, DMS, PS) = (
                        class_.precise_health_score,
                        class_.precise_mana_score,
                        class_.potion_quantity
                    )
                    print_str = "\r[ IDLING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                        HS, MS, DHS, DMS, PS, class_.refill_patience)
                    sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
                    sys.stdout.flush()
                    break
                elif (class_.in_state_animation()):
                    class_.set_precise_score()
                    (DHS, DMS, PS) = (
                        class_.precise_health_score,
                        class_.precise_mana_score,
                        class_.potion_quantity
                    )
                    print_str = "\r[ WAITING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                        HS, MS, DHS, DMS, PS, class_.refill_patience)
                    sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
                    sys.stdout.flush()
                else:
                    class_.idle_click()
                    class_.set_card_quantity()
                    class_.set_card_classification()
                    class_.set_combat_action()
                    (HS, MS) = class_.acquire_orb_score()
                    class_.set_precise_score()
                    (DHS, DMS, PS) = (
                        class_.precise_health_score,
                        class_.precise_mana_score,
                        class_.potion_quantity
                    )
                    if (class_.action_type == class_.ACTION_HEAL):
                        print_str = "\r[ HEAL ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                            HS, MS, DHS, DMS, PS, class_.refill_patience)
                        sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
                        sys.stdout.flush()
                        class_.basic_cast()
                    elif (class_.action_type == class_.ACTION_ATTACK):
                        print_str = "\r[ ATTACK ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                            HS, MS, DHS, DMS, PS, class_.refill_patience)
                        sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
                        sys.stdout.flush()
                        class_.basic_cast()
                    elif (class_.action_type == class_.ACTION_PASS):
                        print_str = "\r[ PASSING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                            HS, MS, DHS, DMS, PS, class_.refill_patience)
                        sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
                        sys.stdout.flush()
                        class_.pass_round()
                    else:
                        print_str = "\r[ ENCHANT ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                            HS, MS, DHS, DMS, PS, class_.refill_patience)
                        sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
                        sys.stdout.flush()
                        class_.enchant_card()
                        class_.idle_click()
                        
                        start_of_time = datetime.datetime.now()
                        
                        while True:
                            class_.set_screenshot()
                            if ((class_.enchantment_complete()) or 
                                ((datetime.datetime.now() - start_of_time).total_seconds() >= class_.enchant_timeout)
                            ):
                                break 
                            class_.preemptive_sleep(0.1)
                            
                        if ((datetime.datetime.now() - start_of_time).total_seconds() >= class_.enchant_timeout):
                            class_.basic_cast(card_index = 1)
                        else:
                            class_.shift_attack()
                            
                    controller = class_.mouse_controller 
                    controller.set_mouse_coord(*class_.idle_centroid)
                class_.preemptive_sleep(1.0)
                
            if (class_.check_pause()):
                return class_ 
                
            class_.set_screenshot()
            (HS, MS) = class_.acquire_orb_score()
            class_.set_precise_score()
            (DHS, DMS, PS) = (
                class_.precise_health_score,
                class_.precise_mana_score,
                class_.potion_quantity
            )
            print_str = "\r[ TURNING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                HS, MS, DHS, DMS, PS, class_.refill_patience)
            sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
            sys.stdout.flush()
                
            class_.idle_click()
                
            class_.turn_around()
            
            if (class_.check_pause()):
                return class_ 
            
            class_.set_screenshot()
            class_.set_precise_score()
            (DHS, DMS, PS) = (
                class_.precise_health_score,
                class_.precise_mana_score,
                class_.potion_quantity
            )
            print_str = "\r[ EXITING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                HS, MS, DHS, DMS, PS, class_.refill_patience)
            sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
            sys.stdout.flush()
            
            class_.run_forward(press = True)
            
            while True:
                class_.set_screenshot()
                class_.set_state()
                if (class_.loading_screen_present()):
                    break
                class_.preemptive_sleep(0.5)
                
            class_.run_forward(press = False)
            
            while True:
                class_.set_screenshot()
                class_.set_state()
                if (class_.loading_screen_present() == False):
                    break
                class_.preemptive_sleep(0.5)
                
            if (class_.check_pause()):
                return class_ 
                
            class_.idle_click()
            
            class_.set_screenshot()
            (HS, MS) = class_.acquire_orb_score()
            class_.set_precise_score()
            (DHS, DMS, PS) = (
                class_.precise_health_score,
                class_.precise_mana_score,
                class_.potion_quantity
            )
            print_str = "\r[ ADJUSTING ] [ H-{} ] [ M-{} ] [ HD-{} ] [ MD-{} ] [ P-{} ] [ R-{} ]".format(
                HS, MS, DHS, DMS, PS, class_.refill_patience)
            sys.stdout.write(class_.pad_string(print_str, class_.PAD_LEN))
            sys.stdout.flush()
                
            class_.goto_dungeon_side()

        class_.k_listener.stop()

        return class_ 

if (__name__ == "__main__"):
    
    n = 1
    
    if (n == 1):
        
        FarmerBot.initialize().farm_halfang()

